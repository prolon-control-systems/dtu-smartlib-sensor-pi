#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Dec 20 13:42:50 2017

@author: samaltesen
"""

import random
import time
import datetime as dt
import sys
import sensors as s
from iotClient import * 
from grove_rgb_lcd import *
import grovepi
import math
import json
import logging

s.initSensors()

MESSAGE_COUNT = 0
client = 0
lastSentTime = dt.datetime.now()
maxSentTime = 60
numberOfSensors = 5
tmp = 0
twinCallback = ""

for sensor in s.sensor:
	sensor['timestamp'] = dt.datetime.utcnow()

def checkDelta(sensor):
	if abs(sensor['sample'] - sensor['sendValue']) > sensor['delta']:
		return True
	return False

def readValue(sensor):
	
	if sensor['readType'] == 'ultrasound':
		sensor['sample'] = grovepi.ultrasonicRead(sensor['groveID'])
	elif sensor['readType'] == 'analog':
		sensor['sample'] = grovepi.analogRead(sensor['groveID'])
	elif sensor['readType'] == 'dht':
		[tmp1, tmp2] = grovepi.dht(sensor['groveID'], 1)
		if sensor['type'] == 'Temperature' and math.isnan(tmp1) != True:
			sensor['sample'] = tmp1 - sensor['offset']
		elif sensor['type'] == 'Humidity' and math.isnan(tmp2) != True:
			sensor['sample'] = tmp2
	sensor['sampleTimestamp'] = dt.datetime.utcnow()



def sendMessage():
	global MESSAGE_COUNT
	print("Init sending :")
	data =	{	"DeviceId"	: s.deviceId, 
				"Trend"		: []
			}
	
	print(json.dumps(data))
	
	for sensor in s.sensor:
		if sensor['sendFlag'] == True:
			sensorData =	{   "PointId"	: s.deviceId + "_" + sensor['pointId'],
								"Timestamp"	: sensor['timestamp'].isoformat() + "Z",
								"Type"		: sensor['type'],
								"Unit"		: sensor['unit'],
								"Value"		: sensor['sendValue']
							}

			data['Trend'].append(sensorData)
			sensor['sendFlag'] = False

	if len(data['Trend']) > 0:
		jsonString = json.dumps(data)
		print("Data:")
		print(json.dumps(data, indent=4))
		message = IoTHubMessage(jsonString)
		client.send_event_async(message, send_confirmation_callback, MESSAGE_COUNT)
		MESSAGE_COUNT += 1
		print("")
	else :
		print("No data ready");


def synchronizeDeviceTwin() :
	print ( "IoTHubClient is reporting state" )
	reported_state = {}
	jsonFormat = json.dumps(reported_state)

	print("This is the reported state\n{0}".format(jsonFormat))
	client.send_reported_state(jsonFormat , len(jsonFormat), send_reported_state_callback, SEND_REPORTED_STATE_CONTEXT)

def checkData(sensor):
	timeDiff = sensor['sampleTimestamp'] - sensor['timestamp']
	deltaTime = timeDiff.total_seconds()

	if (checkDelta(sensor) and (sensor['minTime'] < deltaTime)) :
		setSendData(sensor)
		return True
	if deltaTime > sensor['maxTime']:
		setSendData(sensor)
		return True
	return False	

def checkTimeouts() :
	timeNow = dt.datetime.utcnow()
	for sensor in s.sensor:
		timeDiff = timeNow - sensor['timestamp']
		deltaTime = timeDiff.total_seconds()

		if(deltaTime > sensor['maxTime'] - 10):
			setSendData(sensor)

def setSendData(sensor):
	sensor['sendValue'] = sensor['sample']
	sensor['timestamp'] = sensor['sampleTimestamp']
	sensor['sendFlag'] = True

def run(): 
	try:
		if client.protocol == IoTHubTransportProvider.MQTT:
			synchronizeDeviceTwin()
			
		while True:
			send = False;
			for sensor in s.sensor:
				time.sleep(0.4)
				readValue(sensor)
				if(checkData(sensor)):
					send = True
			if(send):
				print("sending")	
				checkTimeouts()
				sendMessage()
				status = client.get_send_status()
				

	except IoTHubError as iothub_error:
		logging.DEBUG("DEBUG: {0} Unexpected error {1} from IoTHub".format( dt.datetime.now(), iothub_error) )
		
		print ( "Unexpected error %s from IoTHub" % iothub_error )
		return
	except IoTHubClientError as iotclient_error:
		logging.DEBUG("DEBUG: {0} Unexpected error {1} from IoTHubclient".format( dt.datetime.now(), iothub_error) )
	except KeyboardInterrupt:
		print ( "IoTHubClient sample stopped" )
		print_last_message_time(client)

if( __name__ == '__main__'):
	client = iothub_client_init(s.connectionString, IoTHubTransportProvider.MQTT)
	run()

