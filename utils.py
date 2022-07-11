from flask import request
from google.cloud import datastore
import constants
from API_errors import *

class APIError(Exception):
    def __init__(self, e):
        self.description = e["description"]
        self.status_code = e["status_code"]

# API helper functions

client = datastore.Client()

def get_user_from_sub(sub):
    """Get the user ID for the provided owner"""
    query = client.query(kind=constants.users)
    query.add_filter("sub", "=", sub)
    user = list(query.fetch(limit=1))[0]
    return user

def validate_content_type(req):
    """Validate that the request format is application/json"""
    if req.content_type != 'application/json':
        raise APIError(ERR_406_INVALID_MIME)

def authorize_boat_owner(payload, boat):
    # check that owner of received JWT matches that of the boat
    if payload['sub'] != boat['owner']:
        raise APIError(ERR_403_BOAT_OWNER)

def get_load(load_id):
    load_key = client.key(constants.loads, int(load_id))
    load = client.get(key=load_key)
    return load_key, load

def get_boat(boat_id):
    boat_key = client.key(constants.boats, int(boat_id))
    boat = client.get(key=boat_key)
    return boat_key, boat

def create_boat_repr(boat):
    boat["id"] = boat.key.id  # Add id value to response
    boat["self"] = request.url_root + 'boats/' + str(boat.key.id)  # Add boat URL to response
    # Add load representation to response
    rep_loads = []
    for load in boat["loads"]:
        temp = {
            "id": load,
            "item": get_load(load)[1]["item"],
            "self": request.host_url + 'loads/' + str(load)
            }
        rep_loads.append(temp)
    boat["loads"] = rep_loads
    return boat

def create_load_repr(load):
    load["id"] = load.key.id  # Add id value to response
    load["self"] = request.url_root + 'loads/' +  str(load.key.id) # Add URL to response
    # Create carrier representation
    if load["carrier"]:
        temp = {
            "id": load["carrier"],
            "name": get_boat(load["carrier"])[1]["name"],
            "self": request.host_url + 'boats/' + str(load["carrier"])
        }
        load["carrier"] = temp
    return load