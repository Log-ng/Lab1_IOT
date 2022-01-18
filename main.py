print("Xin chào ThingsBoard")
import paho.mqtt.client as mqttclient
import time
import json

import subprocess as sp
import re
# --------------------------------------------------------------------------
wt = 5 # Wait time -- I purposefully make it wait before the shell command
accuracy = 3 #Starting desired accuracy is fine and builds at x1.5 per loop
# --------------------------------------------------------------------------
BROKER_ADDRESS = "demo.thingsboard.io"
PORT = 1883
THINGS_BOARD_ACCESS_TOKEN = "cOHFSdk5cNGKr45SAdvB"


def subscribed(client, userdata, mid, granted_qos):
    print("Subscribed...")


def recv_message(client, userdata, message):
    print("Received: ", message.payload.decode("utf-8"))
    temp_data = {'value': True}
    try:
        jsonobj = json.loads(message.payload)
        if jsonobj['method'] == "setValue":
            temp_data['value'] = jsonobj['params']
            client.publish('v1/devices/me/attributes', json.dumps(temp_data), 1)
    except:
        pass


def connected(client, usedata, flags, rc):
    if rc == 0:
        print("Thingsboard connected successfully!!")
        client.subscribe("v1/devices/me/rpc/request/+")
    else:
        print("Connection is failed")
def get_location():
    pshellcomm = ['powershell']
    pshellcomm.append('add-type -assemblyname system.device; ' \
                      '$loc = new-object system.device.location.geocoordinatewatcher;' \
                      '$loc.start(); ' \
                      'while(($loc.status -ne "Ready") -and ($loc.permission -ne "Denied")) ' \
                      '{start-sleep -milliseconds 100}; ' \
                      '$acc = %d; ' \
                      'while($loc.position.location.horizontalaccuracy -gt $acc) ' \
                      '{start-sleep -milliseconds 100; $acc = [math]::Round($acc*1.5)}; ' \
                      '$loc.position.location.latitude; ' \
                      '$loc.position.location.longitude; ' \
                      '$loc.position.location.horizontalaccuracy; ' \
                      '$loc.stop()' % (accuracy))

    # Remove >>> $acc = [math]::Round($acc*1.5) <<< to remove accuracy builder
    # Once removed, try setting accuracy = 10, 20, 50, 100, 1000 to see if that affects the results
    # Note: This code will hang if your desired accuracy is too fine for your device
    # Note: This code will hang if you interact with the Command Prompt AT ALL
    # Try pressing ESC or CTRL-C once if you interacted with the CMD,
    # this might allow the process to continue

    p = sp.Popen(pshellcomm, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.STDOUT, text=True)
    (out, err) = p.communicate()
    out = re.split('\n', out)

    latitude = float(out[0])
    longitude = float(out[1])
    # print(latitude, longitude)
    return latitude, longitude

client = mqttclient.Client("Gateway_Thingsboard")
client.username_pw_set(THINGS_BOARD_ACCESS_TOKEN)

client.on_connect = connected
client.connect(BROKER_ADDRESS, 1883)
client.loop_start()

client.on_subscribe = subscribed
client.on_message = recv_message

temp = 30
humi = 50
light_intesity = 100
counter = 0

longitude = 0.0
latitude = 0.0
while True:
    latitude, longitude = get_location()
    print(latitude, longitude)
    collect_data = {'temperature': temp, 'humidity': humi, 'light':light_intesity,
                    'longitude': longitude, 'latitude': latitude}
    temp += 1
    humi += 1
    light_intesity += 1
    client.publish('v1/devices/me/telemetry', json.dumps(collect_data), 1)
    time.sleep(10)
