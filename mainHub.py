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
import time
import signal
from gpiozero import Button
import serial
import ast
import qrtools
import RPi.GPIO as GPIO
import subprocess
import pygame
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(25, GPIO.OUT, initial=GPIO.LOW)
led = LED(17)
blue = LED(13)
red = LED(5)
green = LED(6)
button = Button(27)
APPLICATION_ID = "FVAPPID123456789bcdjk"
REST_API_KEY = "A"
MASTER_KEY = "FVMASTERKEY123456789bcdjk"
CENTRALHUBID= "xXaHzOkVCQ"
print("Connecting to server...")
register(APPLICATION_ID, REST_API_KEY, master_key=MASTER_KEY)

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
logInSuccess = False

#p = subprocess.Popen([os.system("echo a")])
#try:
#p.wait(30)
#except:
#print("sub timedout")
#os.kill(p.pid, signal.SIGINT)

#8 -> 18
#11 -> 23
#12 <- 25

def poweroff():
    print("powering off...")
    GPIO.output(25, GPIO.HIGH)
    sleep(5)
    os.system("sudo poweroff")

def logIn():
    global logInSuccess
    try:
        file = open("info.txt", "r")
        username = file.readline().rstrip('\n')
        pw = file.readline().rstrip('\n')
        print(username)
        print(pw)
        U = User.login(username,pw)
        logInSuccess = True 
        try:
            print(U.defaultCentralHub)
            red.off()
            blue.on()
            green.off()
        except:
            print("no central hub")
            addCentralHubToUser = Function("addPtrToCentralHub")
            addCentralHubToUser(centralHubId=CENTRALHUBID, userId = U.objectId)
            sleep(2)
            red.off()
            blue.on()
            green.off()
            pass
        print("Connected successfully!")
    except Exception as e:
        print("Couldn't log in")
        red.on()
        blue.off()
        green.off()
        logInSuccess = False
        print(e)
        pass

def wifiToggle():
    print("setting up wifi")
    os.system("sudo ifdown wlan0")
    sleep(2)
    os.system("sudo ifup wlan0")
    sleep(2)
    print("log in")
    logIn()

def saveUser(userEmail, userPassword):
    f = open("info.txt", "w")
    f.write(userEmail + "\n" + userPassword)
    f.close()
    scanQRCode(time.time())
    
def connectToWifi(wifiName, wifiPassword):
    print("trying to connect")
    file = open("/etc/network/interfaces", "w")
    file.write("source-directory /etc/network/interfaces.d" + "\n")
    file.write("allow-hotplug wlan0"+ "\n")
    file.write("auto wlan0" + "\n")
    file.write("iface wlan0 inet dhcp" + "\n")
    file.write("    wpa-ssid \""+wifiName+"\"" + "\n")
    file.write("    wpa-psk \""+wifiPassword+"\"" + "\n")               
    file.close()
    wifiToggle()

def takePic():
    randomFileName = "centralHubPhoto.jpg"
    try:
        camera.capture(randomFileName)
        print("I'm taking a photo!")
        with open(randomFileName, "rb") as image_file:
            rawdata = image_file.read()
        parsePhotoFile = File(randomFileName, rawdata, 'image/jpg')
        parsePhotoFile.save()
        parseCentralHubData = CentralHubDataClass(photoFile = parsePhotoFile, centralHub = CentralHubObject)
        parseCentralHubData.save()
    except:
        red.on()
        blue.off()
        green.off()
        sleep(4)
        poweroff()
def scanQRCode(startTime):
    print("taking photo for QR Scan")
    red.on()
    blue.on()
    green.off()
    try:
        camera.capture('qrPhoto.jpg')
    except:
        red.on()
        blue.off()
        green.off()
        sleep(4)
        poweroff()
    from qrtools import QR
    qrCode = QR(filename = u"./qrPhoto.jpg")
    if qrCode.decode():
        print qrCode.data_to_string()
        try:
            qrCodeOutputDict = ast.literal_eval(qrCode.data_to_string())
            #blink green
            red.off()
            blue.off()
            green.on()
            sleep(1)
            red.off()
            blue.off()
            green.off()
            sleep(1)
            red.off()
            blue.off()
            green.on()
            sleep(1)
            red.off()
            blue.off()
            green.off()
            sleep(1)
            red.off()
            blue.off()
            green.on()
            if qrCodeOutputDict["t"]=="c":
                if logInSuccess == True:   
                    newCubeFunc = Function("newCube")
                    funcOutput = newCubeFunc(cubeID = qrCodeOutputDict["i"], centralHubID = CENTRALHUBID)        
                    if funcOutput["result"] == "error":
                        print("Error!")
                    elif funcOutput["result"] == "in use":
                        print("Cube in use!")
                    else:
                        #try first time pin here
                        #echo -e 'agent on \n pair ' + funcOutput["result"] + '\n 1234 \n quit' | bluetoothctl
                        print(funcOutput["result"])
                if (time.time() - startTime < 75):
                    print('no qr code data..try again')
                    scanQRCode(startTime)
                else:
                    #Enough tries
                    poweroff()                    
            elif qrCodeOutputDict["t"]=="u":
                print("user")
                userEmail = qrCodeOutputDict["e"]
                userPassword = qrCodeOutputDict["p"]
                saveUser(userEmail, userPassword)
                print("save done")
            elif qrCodeOutputDict["t"]=="w":
                print("wifi")
                wifiName = qrCodeOutputDict["n"]
                wifiPassword = qrCodeOutputDict["p"]
                connectToWifi(wifiName, wifiPassword)
                print("connect done")
                if logInSuccess == False:
                    print "log in failed!"
                    red.on()
                    blue.off()
                    green.off()
                    sleep(3)
                    red.off()
                    poweroff()
                else:
                    print "log in success"
                    print time.time()
                    scanQRCode(time.time())
            else:
                scanQRCode(startTime)
        except Exception as e:
            print e
            scaQRCode(startTime)
            pass
    else:
        print time.time()
        print (time.time() - startTime)
        if (time.time() - startTime < 75):
                print('no qr code data..try again')
                scanQRCode(startTime)
        else:
                #Enough tries
                blue.on()
                green.off()
                red.on()
                sleep(1)
                blue.off()
                red.off()
                sleep(1)
                blue.on()
                red.on()
                sleep(1)
                blue.off()
                red.off()
                sleep(1)
                blue.on()
                red.on()
                poweroff()

def fetchCubes(deviceType):
    fetchCubesFromParse = Function("fetchCubes")
    functionOutput = fetchCubesFromParse(centralHubID=CENTRALHUBID, deviceType = deviceType)
    try:
        CubesMACLinkedToHub = functionOutput["result"]
        print(CubesMACLinkedToHub)
        for MAC in CubesMACLinkedToHub:
            print(MAC)
            os.system('sudo rfcomm release 0')
            os.system('sudo rfcomm -A bind 0 ' + MAC)
            if deviceType==2:
                getSensorCubeData()
            elif deviceType==1:
                outputDict = getCameraCubeData()
                saveCameraCubePic(outputDict) 
    except Exception as e:
        print('error fetching cubes')
        print(e)
        pass


def getSensorCubeData():
    print("get sensor data")    
    bluetoothSerial = serial.Serial("/dev/rfcomm0", baudrate=9600)
    sleep(5)
    print("sending 1")
    bluetoothSerial.write('1') 
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


def saveCameraCubePic(cameraCubeOutputDict):
    print("saving...")
    cubeID = cameraCubeOutputDict["cubeID"]
    battery = float(cameraCubeOutputDict["battery"])
    with open("cameraData.jpg", "rb") as image_file:
        rawdata = image_file.read()
    parsePhotoFile = File("cameraData.jpg", rawdata, 'image/jpg')
    parsePhotoFile.save()
    print(parsePhotoFile.url)
    #Dictiornary with a "battery" : float , "cubeID" : String
    CubeObject = CubeClass(objectId=cubeID)  
    parseCameraData = CameraDataClass(photoFile = parsePhotoFile, battery = battery, cube = CubeObject)
    parseCameraData.save()
    print("save done")
    os.system('sudo rfcomm release 0')

       
def getCameraCubeData():
    print("getting data from camera cube")
    bluetoothSerial = serial.Serial("/dev/rfcomm0", baudrate=9600)
    print("Connected!")
    bluetoothSerial.write('a'.encode())
    sent = 0
    file = open("cameraData.jpg", "w")
    led.off()
    red.off()
    green.off()
    blue.on()
    #start_time = time.time()
    while not sent:
        cameraCubeOutput = bluetoothSerial.readline()
        file.write(cameraCubeOutput)
        if(cameraCubeOutput.find('done') != -1):
            print(cameraCubeOutput)
            CubeOutput = cameraCubeOutput.replace('done','')
            file.write(cameraCubeOutput)
            sent = 1
            file.close            
    print("done getting data from camera cube")
    cameraCubeOutputString = bluetoothSerial.readline()
    print(cameraCubeOutputString)
    try:
        cameraCubeOutputDict = ast.literal_eval(cameraCubeOutputString)
        return cameraCubeOutputDict
    except:
        print("An exception has ocurred. Likely failed to convert data.")
        pass


if (GPIO.input(23) and GPIO.input(18)):
        #timer turned on pi
        print ("timer activated")
        red.on()
        blue.off()
        green.on()
        wifiToggle()
        if (logInSuccess == True):
            fetchCubes(2)
        poweroff()
elif (GPIO.input(23)):
        #light sensor turn pi on
        print("sensor activated")
        red.on()
        blue.on()
        green.on()
        wifiToggle()
        if (logInSuccess == True):
            led.on()
            red.on()
            blue.on()
            green.on()
            takePic()
            fetchCubes(1)
            led.off()
            red.off()
            blue.on()
            green.off()
        led.off()
        poweroff()
elif (GPIO.input(18)):
        #Button turned pi on
        print("button activated")
        red.off()
        blue.on()
        green.on()
        wifiToggle()
        scanQRCode(time.time())
else:
        red.on()
        blue.off()
        green.off()
        sleep(3)
        red.off()
        poweroff()
  




