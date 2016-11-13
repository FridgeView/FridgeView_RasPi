import os
os.environ["PARSE_API_ROOT"] = "https://fridgeview.herokuapp.com/parse"

from parse_rest.datatypes import Function, Object, GeoPoint
from parse_rest.connection import register
from parse_rest.query import QueryResourceDoesNotExist
from parse_rest.connection import ParseBatcher
from parse_rest.core import ResourceRequestBadRequest, ParseError

APPLICATION_ID = "FVAPPID123456789bcdjk"
REST_API_KEY = "A"
MASTER_KEY = "FVMASTERKEY123456789bcdjk"

register(APPLICATION_ID, REST_API_KEY, master_key=MASTER_KEY)

from parse_rest.datatypes import Object

myClassName = "TestObject"
myClass = Object.factory(myClassName)

print myClass
print myClass.__name__


import base64
import requests
import picamera

camera = picamera.PiCamera()

camera.capture('/home/pi/Desktop/image.jpg')

with open("/home/pi/Desktop/image.jpg", "rb") as image_file:
    encoded_string = base64.b64encode(image_file.read())


dummyObject = myClass(foo1 = encoded_string)
dummyObject.save()
