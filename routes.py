from flask import Flask, send_from_directory, render_template, jsonify, request, make_response
import os, json, csv, StringIO, zipfile
from ccd_parser import ParsingCCD
from pymongo import MongoClient
import flask_excel as excel
app = Flask(__name__)


#######################
### CORS VALIDATION ###
#######################
connection = MongoClient('mongodb://localhost:27017/')
db = connection.test


@app.after_request
def add_cors_headers(response):
	response.headers.add('Access-Control-Allow-Origin', '*')
	response.headers.add('Access-Control-Allow-Credentials', 'true')
	response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
	response.headers.add('Access-Control-Allow-Headers', 'Authorization')
	response.headers.add('Access-Control-Allow-Methods', 'GET')
	response.headers.add('Access-Control-Allow-Methods', 'POST')
	response.headers.add('Access-Control-Allow-Methods', 'PUT')
	response.headers.add('Access-Control-Allow-Methods', 'DELETE')
	return response


@app.route('/')
def index():
	return render_template('ng-index.html')

@app.route('/ccd', methods = ['GET'])
def ccdFileNames():

	# id = db.sample.distinct('demographics.patient_id')
	# return jsonify(id)
	directory = os.getcwd()
	files = os.listdir(directory + "/NIST Samples")
	fileStr = {'filename' : []}
	for fil in files:
		if fil.split('.')[1] == 'xml':
			fileStr['filename'].append(fil)
	return jsonify(fileStr)


@app.route('/ccd/<name>', methods=['GET'])
def ccd(name):
	# print name
	x = ParsingCCD("NIST Samples/" + name)
	jsonFile = x.parse().split(".")[0]

	page = open(jsonFile + ".json", 'r')
	parsed = json.loads(page.read())
	pid = parsed['demographics'][1]['patient_id']
	db.sample.update_one({'demographics.patient_id': str(pid)},{'$set':parsed},upsert=True)

	with open(jsonFile + ".json") as data_file: 
		jsonStr = ""
		jsonStr = json.load(data_file)
	return jsonify(jsonStr)


@app.route('/ccd/upload', methods=['POST'])
def ccdUploadFile():
	xmlFile = json.loads(request.data)["filename"]
	if xmlFile.split(".")[1] == "xml":
		with open("NIST Samples/" + xmlFile, 'w') as f: 
			 f.write(json.loads(request.data)["data"])
	return jsonify({"data":"hu"})


@app.route('/ccd/getCSV/<id>/<section>', methods=['GET'])
def getCSV(id, section):
	# with open("outputs/Adjacency.csv") as fp:
	# csv = fp.read()
	# print name
	# csvList = db.sample.find({"demographics.1.title" : name})
	csvList =  db.sample.find({"demographics.1.patient_id" : id}, {section.lower() : 1})

	si = StringIO.StringIO()
	cw = csv.writer(si)

	# print csvList[0]
	# # .items()
	# # [0][1][1]

	cw.writerows(csvList[0].items()[0][1][1].items())

	# for item in csvList:
	# 	print item

	# return Response(
	# csv,
	# mimetype="text/csv",
	# headers={"Content-disposition":
	# "attachment; filename=healthSummary.csv"})


	output = make_response(si.getvalue())
	output.headers["Content-Disposition"] = "attachment; filename=export.csv"
	output.headers["Content-type"] = "text/csv"

	return output


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
