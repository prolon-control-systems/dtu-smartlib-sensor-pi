#!/usr/bin/env python
#Test
# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
import subprocess
import shlex
import os
import random
import time
import sys
import iothub_client
import sensors as s
import json
from iothub_client import IoTHubClient, IoTHubClientError, IoTHubTransportProvider, IoTHubClientResult
from iothub_client import IoTHubMessage, IoTHubMessageDispositionResult, IoTHubError, DeviceMethodReturnValue
from iothub_client import IoTHubClientRetryPolicy, GetRetryPolicyReturnValue
from iothub_client_args import get_iothub_opt, OptionError
from grove_rgb_lcd import *
import grovepi
import math
import logging
import datetime as dt
# HTTP options
# Because it can poll "after 9 seconds" polls will happen effectively
# at ~10 seconds.
# Note that for scalabilty, the default value of minimumPollingTime
# is 25 minutes. For more information, see:
# https://azure.microsoft.com/documentation/articles/iot-hub-devguide/#messaging
TIMEOUT = 241000
MINIMUM_POLLING_TIME = 9

# messageTimeout - the maximum time in milliseconds until a message times out.
# The timeout period starts at IoTHubClient.send_event_async.
# By default, messages do not expire.
MESSAGE_TIMEOUT = 10000

MESSAGE_TIMEOUT_COUNT = 0

RECEIVE_CONTEXT = 0
AVG_WIND_SPEED = 10.0
MIN_TEMPERATURE = 20.0
MIN_HUMIDITY = 60.0
MESSAGE_COUNT = 5
RECEIVED_COUNT = 0
CONNECTION_STATUS_CONTEXT = 0
TWIN_CONTEXT = 0
SEND_REPORTED_STATE_CONTEXT = 0
METHOD_CONTEXT = 0

# global counters
RECEIVE_CALLBACKS = 0
SEND_CALLBACKS = 0
BLOB_CALLBACKS = 0
CONNECTION_STATUS_CALLBACKS = 0
TWIN_CALLBACKS = 0
SEND_REPORTED_STATE_CALLBACKS = 0
METHOD_CALLBACKS = 0

PROTOCOL = 0
payloadTest = ""
# String containing Hostname, Device Id & Device Key in the format:
# "HostName=<host_name>;DeviceId=<device_id>;SharedAccessKey=<device_key>"
CONNECTION_STRING = "[Device Connection String]"

MSG_TXT = "{\"deviceId\": \"myPythonDevice\",\"windSpeed\": %.2f,\"temperature\": %.2f,\"humidity\": %.2f}"

# some embedded platforms need certificate information

def testFunction():
	print("Testing CONNECTIONSTRING: {0}".format(CONNECTION_STRING))

def set_certificates(client):
    from iothub_client_cert import CERTIFICATES
    try:
        client.set_option("TrustedCerts", CERTIFICATES)
        print ( "set_option TrustedCerts successful" )
    except IoTHubClientError as iothub_client_error:
        print ( "set_option TrustedCerts failed (%s)" % iothub_client_error )


def receive_message_callback(message, counter):
    global RECEIVE_CALLBACKS
    message_buffer = message.get_bytearray()
    size = len(message_buffer)
    print ( "Received Message [%d]:" % counter )
    print ( "    Data: <<<%s>>> & Size=%d" % (message_buffer[:size].decode('utf-8'), size) )
    map_properties = message.properties()
    key_value_pair = map_properties.get_internals()
    print ( "    Properties: %s" % key_value_pair )
    counter += 1
    RECEIVE_CALLBACKS += 1
    print ( "    Total calls received: %d" % RECEIVE_CALLBACKS )
    return IoTHubMessageDispositionResult.ACCEPTED


def send_confirmation_callback(message, result, user_context):
	global SEND_CALLBACKS
	print ( "Confirmation[%d] received for message with result = %s" % (user_context, result) )
	map_properties = message.properties()
	print ( "    message_id: %s" % message.message_id )
	print ( "    correlation_id: %s" % message.correlation_id )
	key_value_pair = map_properties.get_internals()
	print ( "    Properties: %s" % key_value_pair )
	SEND_CALLBACKS += 1
	print ( "    Total calls confirmed: %d" % SEND_CALLBACKS )
	logging.info("{0} MESSAGE: Confirmation[{1}] received for message with result = {2}, Total calls confirmed: {3}".format(dt.datetime.now(), user_context, result, SEND_CALLBACKS))



def connection_status_callback(result, reason, user_context):
	global CONNECTION_STATUS_CALLBACKS
	print ( "Connection status changed[%d] with:" % (user_context) )
	print ( "    reason: %d" % reason )
	print ( "    result: %s" % result )
	CONNECTION_STATUS_CALLBACKS += 1
	print ( "    Total calls confirmed: %d" % CONNECTION_STATUS_CALLBACKS )
	logging.info("{0} CONNECTION: Connection status changed[{1}] with:".format(dt.datetime.now(), user_context))
	logging.info("{0} CONNECTION: reason: {1}".format(dt.datetime.now(), reason ))
	logging.info("{0} CONNECTION: result: {1}".format(dt.datetime.now(), result ))
	logging.info("{0} CONNECTION: Total calls confirmed: {1}".format(dt.datetime.now(), CONNECTION_STATUS_CALLBACKS ))



def device_twin_callback(update_state, payload, user_context):
    global TWIN_CALLBACKS
    print("")
    print ( "")
    print ( "Twin callback called with: - Called from client")
    print ( "updateStatus: %s" % update_state )
    print ( "context: %s" % user_context )
    print ( "payload: %s" % payload )
    TWIN_CALLBACKS += 1
    print ( "Total calls confirmed: %d\n" % TWIN_CALLBACKS )
    payloadDict = json.loads(payload)
    s.updateSensors(payloadDict)


def send_reported_state_callback(status_code, user_context):
	global SEND_REPORTED_STATE_CALLBACKS
	print ( "Confirmation[%d] for reported state received with:" % (user_context) )
	print ( "    status_code: %d" % status_code )
	SEND_REPORTED_STATE_CALLBACKS += 1
	print ( "    Total calls confirmed: %d" % SEND_REPORTED_STATE_CALLBACKS )
	#logging.info("{0} REPORTEDSTATE: Confirmation[{1}] for reported state received with:".format(dt.datetime.now(), user_context ))
	#logging.info("{0} REPORTEDSTATE: status_code: {1}".format(dt.datetime.now(), status_code ))
	#logging.info("{0} REPORTEDSTATE: Total calls confirmed: {1}".format(dt.datetime.now(), SEND_REPORTED_STATE_CALLBACKS ))



def device_method_callback(method_name, payload, user_context):
	global METHOD_CALLBACKS
	print ( "\nMethod callback called with:\nmethodName = %s\npayload = %s\ncontext = %s" % (method_name, payload, user_context) )
	METHOD_CALLBACKS += 1
	print ( "Total calls confirmed: %d\n" % METHOD_CALLBACKS )
	device_method_return_value = DeviceMethodReturnValue()
	if method_name == "ExecCmd" :

		jsonCommand = json.loads(payload)

		cmd = jsonCommand["Command"]
		proc = subprocess.Popen( shlex.split(cmd), stdout=subprocess.PIPE)
		(out, err) = proc.communicate()

		jsonOut = json.dumps(out)
		print(jsonOut)
		#test = os.system(payload)
		print("Payload: {0}".format(out))
		device_method_return_value.response = jsonOut
		device_method_return_value.status = 200
	else :
		device_method_return_value.response = "{ \"Response\": \"This is the response from the device\" }"
		device_method_return_value.status = 400
	return device_method_return_value


def blob_upload_conf_callback(result, user_context):
    global BLOB_CALLBACKS
    print ( "Blob upload confirmation[%d] received for message with result = %s" % (user_context, result) )
    BLOB_CALLBACKS += 1
    print ( "    Total calls confirmed: %d" % BLOB_CALLBACKS )


def iothub_client_init(ConString, Proto):
    logging.basicConfig(filename='smartlib{0}.log'.format(dt.date.today().isocalendar()[1]), level=logging.DEBUG)
    # prepare iothub client
    print("ConString {0}".format(ConString))
    client = IoTHubClient(ConString, Proto)
    if client.protocol == IoTHubTransportProvider.HTTP:
        client.set_option("timeout", TIMEOUT)
        client.set_option("MinimumPollingTime", MINIMUM_POLLING_TIME)
    # set the time until a message times out
    client.set_option("messageTimeout", MESSAGE_TIMEOUT)
    # some embedded platforms need certificate information
    set_certificates(client)
    # to enable MQTT logging set to 1
    if client.protocol == IoTHubTransportProvider.MQTT:
        client.set_option("logtrace", 0)
    client.set_message_callback(
        receive_message_callback, RECEIVE_CONTEXT)
    if client.protocol == IoTHubTransportProvider.MQTT or client.protocol == IoTHubTransportProvider.MQTT_WS:
        client.set_device_twin_callback(
            device_twin_callback, TWIN_CONTEXT)
        client.set_device_method_callback(
            device_method_callback, METHOD_CONTEXT)
    if client.protocol == IoTHubTransportProvider.AMQP or client.protocol == IoTHubTransportProvider.AMQP_WS:
        client.set_connection_status_callback(
            connection_status_callback, CONNECTION_STATUS_CONTEXT)

    retryPolicy = IoTHubClientRetryPolicy.RETRY_INTERVAL
    retryInterval = 0
    client.set_retry_policy(retryPolicy, retryInterval)
    print ( "SetRetryPolicy to: retryPolicy = %d" %  retryPolicy)
    print ( "SetRetryPolicy to: retryTimeoutLimitInSeconds = %d" %  retryInterval)
    retryPolicyReturn = client.get_retry_policy()
    print ( "GetRetryPolicy returned: retryPolicy = %d" %  retryPolicyReturn.retryPolicy)
    print ( "GetRetryPolicy returned: retryTimeoutLimitInSeconds = %d" %  retryPolicyReturn.retryTimeoutLimitInSeconds)
    return client


def print_last_message_time(client):
    try:
        last_message = client.get_last_message_receive_time()
        print ( "Last Message: %s" % time.asctime(time.localtime(last_message)) )
        print ( "Actual time : %s" % time.asctime() )
    except IoTHubClientError as iothub_client_error:
        if iothub_client_error.args[0].result == IoTHubClientResult.INDEFINITE_TIME:
            print ( "No message received" )
        else:
            print ( iothub_client_error )


def iothub_client_sample_run():

    try:

        client = iothub_client_init()

        if client.protocol == IoTHubTransportProvider.MQTT:
            print ( "IoTHubClient is reporting state" )
            reported_state = "{\"newState\":\"standBy\"}"
            client.send_reported_state(reported_state, len(reported_state), send_reported_state_callback, SEND_REPORTED_STATE_CONTEXT)

        while True:
            # send a few messages every minute
            print ( "IoTHubClient sending %d messages" % MESSAGE_COUNT )

            for message_counter in range(0, MESSAGE_COUNT):
                temperature = MIN_TEMPERATURE + (random.random() * 10)
                humidity = MIN_HUMIDITY + (random.random() * 20)
                msg_txt_formatted = MSG_TXT % (
                    AVG_WIND_SPEED + (random.random() * 4 + 2),
                    temperature,
                    humidity)
                # messages can be encoded as string or bytearray
                if (message_counter & 1) == 1:
                    message = IoTHubMessage(bytearray(msg_txt_formatted, 'utf8'))
                else:
                    message = IoTHubMessage(msg_txt_formatted)
                # optional: assign ids
                message.message_id = "message_%d" % message_counter
                message.correlation_id = "correlation_%d" % message_counter
                # optional: assign properties
                prop_map = message.properties()
                prop_map.add("temperatureAlert", 'true' if temperature > 28 else 'false')

                client.send_event_async(message, send_confirmation_callback, message_counter)
                print ( "IoTHubClient.send_event_async accepted message [%d] for transmission to IoT Hub." % message_counter )

            # Wait for Commands or exit
            print ( "IoTHubClient waiting for commands, press Ctrl-C to exit" )

            status_counter = 0
            while status_counter <= MESSAGE_COUNT:
                status = client.get_send_status()
                print ( "Send status: %s" % status )
                time.sleep(10)
                status_counter += 1

    except IoTHubError as iothub_error:
        print ( "Unexpected error %s from IoTHub" % iothub_error )
        return
    except KeyboardInterrupt:
        print ( "IoTHubClient sample stopped" )

    print_last_message_time(client)


def init(ConString, proto):
	CONNECTION_STRING = ConString
	print("{0}".format(CONNECTION_STRING))
	if proto == "MQTT":
		PROTOCOL = IoTHubTransportProvider.MQTT
	elif proto == "MQTTWS":
		PROTOCOL = IoTHubTransportProvider.MQTT_WS
	elif proto == "AMQP":
		PROTOCOL = IoTHubTransportProvider.AMQP
	elif proto == "AMQPWS":
		PROTOCOL = IoTHubTransportProvider.AMQP_WS
	elif proto == "HTTP":
		PROTOCOL = IoTHubTransportProvider.HTTP


if __name__ == '__main__':
	print ( "\nPython %s" % sys.version )
	print ( "IoT Hub Client for Python" )
	try:
	#(CONNECTION_STRING, PROTOCOL) = get_iothub_opt(sys.argv[1:], CONNECTION_STRING, PROTOCOL)
		CONNECTION_STRING="HostName=dtu-test-hub.azure-devices.net;DeviceId=B101_DI123_01_KN002;SharedAccessKey=Y6YoYW/a8RtFIUZ5pJvVi5qDIbIou8+t2wzKTgoPRJw="
		PROTOCOL = IoTHubTransportProvider.MQTT
	except OptionError as option_error:
		print ( option_error )
		usage()
		sys.exit(1)

	print ( "Starting the IoT Hub Python sample..." )
	print ( "    Protocol %s" % PROTOCOL )
	print ( "    Connection string=%s" % CONNECTION_STRING )

	iothub_client_sample_run()