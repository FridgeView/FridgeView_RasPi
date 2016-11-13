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

APPLICATION_ID = "FVAPPID123456789bcdjk"
REST_API_KEY = "A"
MASTER_KEY = "FVMASTERKEY123456789bcdjk"

register(APPLICATION_ID, REST_API_KEY, master_key=MASTER_KEY)
#This is not good
U = User.login("fvAdmin","abcd")

photoClassName = "Photos"
photoClass = Object.factory(photoClassName)

camera = picamera.PiCamera()
encoded_string = base64.b64encode(camera.capture('newPhoto.jpg'))

newPhoto = photoClass(encrypStr = encoded_string,device = 0,user=User.current_user())
newPhoto.save()
