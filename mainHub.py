import os
os.environ["PARSE_API_ROOT"] = "https://fridgeview.herokuapp.com/parse"
import base64
import requests
import picamera
import random, string
from parse_rest.datatypes import Function, Object, File, GeoPoint
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
import qrtools

led = LED(17)
statusLed = LED(25)
button = Button(27)
APPLICATION_ID = "FVAPPID123456789bcdjk"
REST_API_KEY = "A"
MASTER_KEY = "FVMASTERKEY123456789bcdjk"
CENTRALHUBID= "xXaHzOkVCQ"
print("Connecting to server...")
register(APPLICATION_ID, REST_API_KEY, master_key=MASTER_KEY)

try:
    #Fix later: this is not good
    U = User.login("fvAdmin","abcd")
    print("Connected successfully!")
except:
    pass

CentralHubDataClassName = "CentralHubData"
CentralHubDataClass = Object.factory(CentralHubDataClassName)

CameraDataClassName = "CameraData"
CameraDataClass = Object.factory(CameraDataClassName)

CubeClassName = "Cube"
CubeClass = Object.factory(CubeClassName)

CentralHubClassName = "CentralHub"
CentralHubClass = Object.factory(CentralHubClassName)

CentralHubObject = CentralHubClass(objectId=CENTRALHUBID)

camera = picamera.PiCamera()
camera.rotation = 180

bluetoothSerial = None

#random string for uploading picture to the server
def randomstr(length):
    return ''.join(random.choice(string.lowercase) for i in range(length))

def buttonPressed():
    print("button pressed")
    #sleep(5)
    #scanQRCode()
    #takePic()
    #fetchCubes(2) #Sensor Cubes
    fetchCubes(1) #Camera Cubes
    

def takePic():
    #while true:
    led.on()
    randomFileName = randomstr(16) + ".jpg"
    camera.capture(randomFileName)
    led.off()
    print("I'm taking a photo!")
    with open(randomFileName, "rb") as image_file:
        rawdata = image_file.read()
    parsePhotoFile = File(randomFileName, rawdata, 'image/jpg')
    parsePhotoFile.save()
    print(parsePhotoFile.url)
    parseCentralHubData = CentralHubDataClass(photoFile = parsePhotoFile, centralHub = CentralHubObject)
    parseCentralHubData.save()
    #sleep(2)

def scanQRCode():
    print("taking photo for QR Scan")
    camera.capture('qrPhoto.jpg')
    from qrtools import QR
    myCode = QR(filename = u"./qrPhoto.jpg")
    if myCode.decode():
          print myCode.data
          print myCode.data_type
          print myCode.data_to_string()

def fetchCubes(deviceType):
    fetchCubesFromParse = Function("fetchCubes")
    functionOutput = fetchCubesFromParse(centralHubID=CENTRALHUBID, deviceType = deviceType)
    try:
        CubesMACLinkedToHub = functionOutput["result"]
        print(CubesMACLinkedToHub)
        for MAC in CubesMACLinkedToHub:
            print(MAC)
            os.system('sudo rfcomm release 0')
            os.system('sudo rfcomm bind 0 ' + MAC)
            if deviceType==2:
                getSensorCubeData()
            elif deviceType==1:
                getCameraCubeData()
    except:
        print('error fetching cubes')
        pass
    
def getSensorCubeData():
    print("get sensor data")
    bluetoothSerial = serial.Serial("/dev/rfcomm0", baudrate=9600)
    bluetoothSerial.write('1'.encode()) 
    sensorCubeOutputString = bluetoothSerial.readline()
    print(sensorCubeOutputString)
    try:
        sensorCubeOutputDict = ast.literal_eval(sensorCubeOutputString)

        cubeID = sensorCubeOutputDict["cubeID"]
        temp = float(sensorCubeOutputDict["Temp"])
        humid = float(sensorCubeOutputDict["Hum"])
        battery = float(sensorCubeOutputDict["Battery"])
        
        newSensorDataFunc = Function("newSensorData")
        newSensorDataFunc(cubeID=cubeID, temperature=temp, humidity=humid, battery=battery)
    except:
        print("An exception has ocurred. Likely failed to convert data.")
        pass
    os.system('sudo rfcomm release 0')

        
def getCameraCubeData():
    print("getting data from camera cube")
    bluetoothSerial = serial.Serial("/dev/rfcomm0", baudrate=9600)
    bluetoothSerial.write('a'.encode())
    sent = 0
    randomFileName = randomstr(16) + ".jpeg"
    file = open("cameradata.jpeg", "w")
    #start_time = time.time()
    while not sent:
        cameraCubeOutput = bluetoothSerial.readline()
        file.write(cameraCubeOutput)
        if(cameraCubeOutput.find('done') != -1): 
            CubeOutput = cameraCubeOutput.replace('done','')
            file.write(cameraCubeOutput)
            sent = 1
            file.close
    #print(time.time()-start_time) #this prints out how long it takes to send the photo through BT
    print("done getting data from camera cube")
    cameraBattery = float(bluetoothSerial.readline())
    print(cameraBattery)
    with open("cameradata.jpeg", "rb") as image_file:
        rawdata = image_file.read()
    parsePhotoFile = File("cameradata.jpeg", rawdata, 'image/jpeg')
    parsePhotoFile.save()
    print(parsePhotoFile.url)
    #Dictiornary with a "battery" : float , "cubeID" : String
    #CubePtr = CubeClass(objectId=CubeID)  
    parseCameraData = CameraDataClass(photoFile = parsePhotoFile, battery = cameraBattery, cube = CubePtr)
    parseCameraData.save()
    os.system('sudo rfcomm release 0')
        
while True:
    statusLed.on  
    button.when_pressed = buttonPressed 
    #print ("Test")
    #print bluetoothSerial.readline()
    #print ("Test2")
    sleep(1)
  




