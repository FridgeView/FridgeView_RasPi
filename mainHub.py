import os
os.environ["PARSE_API_ROOT"] = "https://fridgeview.herokuapp.com/parse"
import base64
import requests
import picamera
from parse_rest.datatypes import Function, Object, GeoPoint
from parse_rest.connection import register
from parse_rest.query import QueryResourceDoesNotExist
from parse_rest.connection import ParseBatcher
from parse_rest.core import ResourceRequestBadRequest, ParseError
from parse_rest.user import User
from parse_rest.datatypes import Object
from parse_rest.connection import SessionToken, register
from gpiozero import LED
from time import sleep
from gpiozero import Button
import serial
import ast

bluetoothSerial = serial.Serial("/dev/rfcomm0", baudrate=9600)



led = LED(17)
statusLed = LED(25)
button = Button(27)
APPLICATION_ID = "FVAPPID123456789bcdjk"
REST_API_KEY = "A"
MASTER_KEY = "FVMASTERKEY123456789bcdjk"
print("Connecting to server...")
register(APPLICATION_ID, REST_API_KEY, master_key=MASTER_KEY)

try:
    #Fix later: this is not good
    U = User.login("fvAdmin","abcd")
    print("Connected successfully!")
except:
    pass

photoClassName = "Photos"
photoClass = Object.factory(photoClassName)

sensorDataClassName = "SensorData"
sensorDataClass = Object.factory(sensorDataClassName)

def buttonPressed():
    print("button pressed")
    takePic()
    getSensorCubeData()

def takePic():    
    led.on()
    camera.capture('newPhoto.jpg')
    led.off()
    print("I'm taking a photo!")
    with open("newPhoto.jpg", "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    newPhoto = photoClass(encrypStr = encoded_string,device = 0,user=U)
    newPhoto.save()
camera = picamera.PiCamera()
camera.rotation = 180

def getSensorCubeData():
    print("getting sensor data")
    bluetoothSerial.write('a'.encode())
    print("Sent 'a'")
    sensorCubeOutputString = bluetoothSerial.readline()
    print(sensorCubeOutputString)
    sensorCubeOutputDict = ast.literal_eval(sensorCubeOutputString)
    newSensorData = sensorDataClass(sensorCubeID = sensorCubeOutputDict["sensorCubeID"], temperature = sensorCubeOutputDict["Temp"], humidity = sensorCubeOutputDict["Hum"], user = U)
    newSensorData.save()

while True:
    statusLed.on  
    button.when_pressed = buttonPressed 
    #print ("Test")
    #print bluetoothSerial.readline()
    #print ("Test2")
    sleep(1)
  




