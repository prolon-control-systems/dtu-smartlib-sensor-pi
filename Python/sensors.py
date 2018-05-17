
import json
import os


sensor = []


def updateSensors(data) :

	if 'desired' in data :
		payload = data['desired']
	else :
		payload = data

	for sen in sensor :
		if sen['pointId'] in payload :
			for key in payload[sen['pointId']] :
				sen[key] = payload[sen['pointId']][key]



def initSensors() :

	global connectionString
	global deviceId

	
	#Reading data for sensors, deviceId, and connectionstring from setup file
	if os.path.isfile('./setup.json') : 
		with open('setup.json', 'r') as setup_file:
			setup = json.load(setup_file)

		print("Initializing sensors")
		for key in setup :
			if key == "sensors" :
				for s in setup["sensors"] :
					print("Adding sensor")
					sensor.append(s)
					print("{0}".format(len(sensor)))

			if key == "deviceId" :
				deviceId = setup[key]
			if key == "connectionString" :
				connectionString = str(setup[key])

	else :
		deviceId = "B101_default_35"
		connectionString = "HostName=dtu-test-hub.azure-devices.net;DeviceId=B101_DI123_01_KN035;SharedAccessKey=4te7dJgvDtIPdBDR5jlC34KsOZL4XgyQEHxDJBhVvUQ="
		sensor[0] = {
					  "pointId": "US01",
					  "type": "ultraSound",
					  "readType": "ultrasound",
					  "unit": "cm",
					  "groveID": 2,
					  "delta": 50,
					  "checkValue": 0,
					  "value": 0,
					  "timestamp": 0,
					  "minTime": 5,
					  "maxTime": 60
					}
		sensor[1] = {
					  "pointId": "TR01",
					  "type": "Temperature",
					  "readType": "dht",
					  "unit": "degree-celsius",
					  "groveID": 4,
					  "delta": 1,
					  "checkValue": 0,
					  "value": 0,
					  "timestamp": 0,
					  "minTime": 5,
					  "maxTime": 60,
					  "offset" : 0
					}
		sensor[2] = {
					  "pointId": "HR01",
					  "type": "Humidity",
					  "readType": "dht",
					  "unit": "%",
					  "groveID": 4,
					  "delta": 1,
					  "checkValue": 0,
					  "value": 0,
					  "timestamp": 0,
					  "minTime": 5,
					  "maxTime": 60
					}
		sensor[3] = {
					  "pointId": "SR01",
					  "type": "Sound",
					  "readType": "analog",
					  "unit": "dB",
					  "groveID": 1,
					  "delta": 10,
					  "checkValue": 0,
					  "value": 0,
					  "timestamp": 0,
					  "minTime": 5,
					  "maxTime": 60
					}
		sensor[4] = {
					"pointId": "LX01",
					"type": "Light",
					"readType": "analog",
					"unit": "lux",
					"groveID": 2,
					"delta": 10,
					"checkValue": 0,
					"value": 0,
					"timestamp": 0,
					"minTime": 5,
					"maxTime": 60
					}


				