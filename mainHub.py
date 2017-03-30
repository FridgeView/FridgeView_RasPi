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
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(25, GPIO.OUT, initial=GPIO.LOW)
led = LED(17)
button = Button(27)
qrTry = 0
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


def logIn():
    try:
        file = open("info.txt", "r")
        username = file.readline().rstrip('\n')
        pw = file.readline().rstrip('\n')
        print(username)
        print(pw)
        U = User.login(username,pw)
        try:
            print(U.defaultCentralHub)
        except:
            print("no central hub")
            addCentralHubToUser = Function("addPtrToCentralHub")
            addCentralHubToUser(centralHubId=CENTRALHUBID, userId = U.objectId)
            GPIO.output(25, GPIO.HIGH)
            sleep(5)
            os.system("sudo poweroff")
            pass
        print("Connected successfully!")
    except Exception as e:
        print("Couldn't log in")
        print(e)
        GPIO.output(25, GPIO.HIGH)
        sleep(5)
        os.system("sudo poweroff")
        pass


def saveUser(userEmail, userPassword):
    f = open("info.txt", "w")
    f.write(userEmail + "\n" + userPassword)
    f.close()
    
def connectToWifi(wifiName, wifiPassword, wifiEncryption):
    file = open("/etc/network/interfaces", "w")
    file.write("source-directory /etc/network/interfaces.d" + "\n")
    file.write("allow-hotplug wlan0"+ "\n")
    file.write("auto wlan0" + "\n")
    file.write("iface wlan0 inet dhcp" + "\n")
    file.write("    wpa-ssid \""+wifiName+"\"" + "\n")
    file.write("    wpa-psk \""+wifiPassword+"\"" + "\n")               
    file.close()
    #os.system("sudo reboot")


#random string for uploading picture to the server
def randomstr(length):
    return ''.join(random.choice(string.lowercase) for i in range(length))

def buttonPressed():
    print("button pressed")
    #sleep(5)
    #scanQRCode()
    #takePic()
    #£fetchCubes(2) #Sensor Cubes
    #fetchCubes(1) #Camera Cubes
    
def takePic():
    #randomFileName = randomstr(16) + ".jpg"
    randomFileName = "centralHubPhoto.jpg"
    camera.capture(randomFileName)
    print("I'm taking a photo!")
    with open(randomFileName, "rb") as image_file:
        rawdata = image_file.read()
    parsePhotoFile = File(randomFileName, rawdata, 'image/jpg')
    parsePhotoFile.save()
    parseCentralHubData = CentralHubDataClass(photoFile = parsePhotoFile, centralHub = CentralHubObject)
    parseCentralHubData.save()

def scanQRCode():
    print("taking photo for QR Scan")
    camera.capture('qrPhoto.jpg')
    from qrtools import QR
    qrCode = QR(filename = u"./qrPhoto.jpg")
    if qrCode.decode():
        print qrCode.data_to_string()
        try:
            qrCodeOutputDict = ast.literal_eval(qrCode.data_to_string())
            if qrCodeOutputDict["Type"]=="Cube":
                newCubeFunc = Function("newCube")
                funcOutput = newCubeFunc(cubeID = qrCodeOutputDict["CubeID"], centralHubID = CENTRALHUBID)        
                if funcOutput["result"] == "error":
                    print("Error!")
                elif funcOutput["result"] == "in use":
                    print("Cube in use!")
                else:
                    #try first time pin here
                    #echo -e 'agent on \n pair ' + funcOutput["result"] + '\n 1234 \n quit' | bluetoothctl
                    print(funcOutput["result"])
                GPIO.output(25, GPIO.HIGH)
                sleep(5)
                os.system("sudo poweroff")
            elif qrCodeOutputDict["Type"]=="Wifi":
                print("wifi")
                wifiName = qrCodeOutputDict["WifiName"]
                wifiPassword = qrCodeOutputDict["WifiPassword"]
                wifiEncryp = qrCodeOutputDict["WifiEncryption"]
                userEmail = qrCodeOutputDict["UserEmail"]
                userPassword = qrCodeOutputDict["UserPassword"]
                saveUser(userEmail, userPassword)
                #connectToWifi(wifiName, wifiPassword, wifiEncryp)             
        except:
            pass
            if (qrTry < 20) :
                qrTry += 1
                print('error with qr code data..try again')
                scanQRCode()
            else:
                print('error with qr')
                qrTry = 0


def fetchCubes(deviceType):
    fetchCubesFromParse = Function("fetchCubes")
    functionOutput = fetchCubesFromParse(centralHubID=CENTRALHUBID, deviceType = deviceType)
    try:
        CubesMACLinkedToHub = functionOutput["result"]
        print(CubesMACLinkedToHub)
        for MAC in CubesMACLinkedToHub:
            print(MAC)
            os.system('sudo rfcomm release 0')
            print("A")
            os.system('sudo rfcomm -A bind 0 ' + MAC)
            print("B")
            if deviceType==2:
                print("C")
                getSensorCubeData()
            elif deviceType==1:
                getCameraCubeData()
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

       
def getCameraCubeData():
    print("getting data from camera cube")
    bluetoothSerial = serial.Serial("/dev/rfcomm0", baudrate=38400)
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

if (GPIO.input(23)):
        #light sensor turn pi on
        print("sensor activated")
        os.system("sudo ifdown wlan0")
        sleep(5)
        os.system("sudo ifup wlan0")
        sleep(5)
        logIn()
        fetchCubes(2)
        led.on()
        takePic()
        fetchCubes(1)
        led.off()
        GPIO.output(25, GPIO.HIGH)
        sleep(5)
        os.system("sudo poweroff")
if (GPIO.input(18)):
        #Button turned pi on
        print("button activated")
        os.system("sudo ifdown wlan0")
        sleep(5)
        os.system("sudo ifup wlan0")
        sleep(5)
        logIn()
        scanQRCode()
        GPIO.output(25, GPIO.HIGH)
        sleep(5)
        os.system("sudo poweroff")
led.off()
  




