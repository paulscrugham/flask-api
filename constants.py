import json
from flask import make_response

# app specific constants
boats = "boats"
loads = "loads"
users = "users"

# generic constants
application_json = 'application/json'

ERR_400_INVALID_ATTR = (json.dumps({"Error": "The request object is missing at least one of the required attributes or an attribute is invalid."}), 400)
ERR_403_NAME_EXISTS = (json.dumps({"Error": "The provided name attribute already exists."}), 403)
ERR_404_INVALID_ID = (json.dumps({"Error": "No boat with this boat_id exists"}), 404)
ERR_405_NO_METHOD = (json.dumps({"Error": "Method not recognized"}), 405)
ERR_406_INVALID_ACCEPT = (json.dumps({"Error": "The requested MIME type is not supported."}), 406)
ERR_415_INVALID_MIME = (json.dumps({"Error": "The MIME type of the request object is not accepted"}), 415)