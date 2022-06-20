from audioop import add
from venv import create
from google.cloud import datastore
from flask import Flask, request, url_for, render_template, redirect, jsonify, make_response
from os import environ as env
from dotenv import find_dotenv, load_dotenv
from authlib.integrations.flask_client import OAuth
from urllib.parse import quote_plus, urlencode

from jwt import AuthError, verify_jwt
from API_errors import *
import json
import constants

DEBUG = True

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

oauth = OAuth(app)

oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

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

# ---------------------------------------------
#           ERROR HANDLER ROUTES
# ---------------------------------------------
@app.errorhandler(AuthError)
def handle_auth_exception(e):
    res = make_response({"Error": e.error["description"]})
    res.status_code = e.status_code
    res.content_type = "application/json"
    return res

class APIError(Exception):
    def __init__(self, e):
        self.description = e["description"]
        self.status_code = e["status_code"]

@app.errorhandler(APIError)
def handle_api_exception(e):
    res = make_response({"Error": e.description})
    res.status_code = e.status_code
    res.content_type = "application/json"
    return res

# ---------------------------------------------
#           AUTH APP ROUTES
# ---------------------------------------------

@app.route("/")
def home():
    return render_template("home.html", token=None)

@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

@app.route("/userinfo", methods=["GET", "POST"])
def callback():
    # get token from auth0
    token = oauth.auth0.authorize_access_token()
    
    # check if user already exists in database
    query = client.query(kind=constants.users)
    query.add_filter("sub", "=", token['userinfo']['sub'])
    user = list(query.fetch(limit=1))
    if not user:
        # store user in Google Datastore
        new_user = datastore.entity.Entity(key=client.key(constants.users))
        new_user.update({
            'sub': token['userinfo']['sub'],
            'name': token['userinfo']['name'],
            'boats': []
            })
        client.put(new_user)
    return render_template("home.html", token=token)

@app.route("/logout")
def logout():
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

# ---------------------------------------------
#           USERS APP ROUTES
# ---------------------------------------------

@app.route("/users", methods=['GET'])
def users_get():
    if request.method == 'GET':
        validate_content_type(request)

        query = client.query(kind=constants.users)
        data = list(query.fetch())
        for user in data:
            rep_boats = []
            for boat in user["boats"]:
                temp = {}
                temp["id"] = boat
                temp["name"] = get_boat(boat)[1]["name"]
                temp["self"] = request.url_root + 'boats/' + str(boat)
                rep_boats.append(temp)
            user["boats"] = rep_boats
        res = make_response(json.dumps(data))
        res.mimetype = constants.application_json
        res.status_code = 200
        return res
    else:
        raise APIError(ERR_405_NO_METHOD)

# ---------------------------------------------
#           BOATS APP ROUTES
# ---------------------------------------------

@app.route('/boats', methods=['POST','GET'])
def boats_get_post():
    # Authenticate owner
    payload = verify_jwt(request)
    
    if request.method == 'POST':
        validate_content_type(request)
        
        # Save request info in variable
        content = request.get_json()
        # Create new boat entity object
        new_boat = datastore.entity.Entity(key=client.key(constants.boats))
        new_boat.update({
            "name": content["name"], 
            "length": content["length"],
            "date_built": content["date_built"],
            "owner": payload["sub"],
            "loads": []
            })
        
        # Add new boat to Google Cloud Store
        client.put(new_boat)

        # Update user entity
        query = client.query(kind=constants.users)
        query.add_filter("sub", "=", payload["sub"])
        user = list(query.fetch(limit=1))[0]
        user["boats"].append(new_boat.key.id)
        client.put(user)

        # Return the new boat attributes
        data = {
            "id": new_boat.key.id,
            "name": new_boat["name"],
            "length": new_boat["length"],
            "date_built": new_boat["date_built"],
            "owner": new_boat["owner"],
            "loads": [],
            "self": request.base_url + '/' + str(new_boat.key.id)
        }
        res = make_response(json.dumps(data))
        res.mimetype = constants.application_json
        res.status_code = 201
        return res

    elif request.method == 'GET':
        validate_content_type(request)
        query = client.query(kind=constants.boats)
        query.add_filter("owner", "=", payload["sub"])
        
        # Apply pagination to results
        q_limit = int(request.args.get('limit', '5'))  # default number of results is 3
        q_offset = int(request.args.get('offset', '0'))  # default offset is 0
        b_iterator = query.fetch(limit=q_limit, offset=q_offset)
        pages = b_iterator.pages
        results = list(next(pages))
        # Calculate url of next page if more results exist
        if b_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
        else:
            next_url = None
        
        # Create list of boat representations
        rep_results = []
        for boat in results:
            rep_results.append(create_boat_repr(boat))
                
        data = {"boats": rep_results}
        # Add url of next page to output
        if next_url:
            data["next"] = next_url
        res = make_response(json.dumps(data))
        res.mimetype = constants.application_json
        res.status_code = 200
        return res
    else:
        raise APIError(ERR_405_NO_METHOD)

@app.route('/boats/<id>', methods=['DELETE','GET', 'PUT', 'PATCH'])
def boats_get_put_patch_delete(id):
    # Authenticate owner
    payload = verify_jwt(request)

    boat_key, boat = get_boat(id)
    
    # Send 404 error if no boat with the requested id exists
    if not boat:
        raise APIError(ERR_404_INVALID_ID)
    
    # Authorize owner
    authorize_boat_owner(payload, boat)

    if request.method == 'DELETE':
        # Update the carrier attribute of all loads on this boat
        for item in boat["loads"]:
            load_key, load = get_load(item)
            load["carrier"] = None
            client.put(load)

        # Update the boats attribute of the owner's user entity
        user = get_user_from_sub(payload["sub"])
        boat_to_delete = [item for item in user["boats"] if item == boat.key.id][0]
        user["boats"].remove(boat_to_delete)
        client.put(user)

        # Delete the boat
        client.delete(boat_key)
        return '', 204
    elif request.method == 'GET':
        validate_content_type(request)
        boat = create_boat_repr(boat)
        res = make_response(json.dumps(boat))
        res.status_code = 200
        res.mimetype = constants.application_json
        return res
    elif request.method == 'PUT':
        validate_content_type(request)
        
        # Replace boat entity content
        content = request.get_json()
        boat["name"] = content["name"]
        boat["date_built"] = content["date_built"]
        boat["length"] = content["length"]

        # Remove boat to load relationships
        for load in boat["loads"]:
            delete_load(boat.key.id, load)

        boat["loads"] = []

        # Update boat
        client.put(boat)
        
        # Return the boat object
        boat = create_boat_repr(boat)
        res = make_response(json.dumps(boat))
        res.mimetype = constants.application_json
        res.status_code = 200
        return res
    elif request.method == 'PATCH':
        validate_content_type(request)
        
        content = request.get_json()
        for attr in content:
            if attr != "loads":
                boat[attr] = content[attr]

        client.put(boat)

        # Add any new loads
        if 'loads' in content:
            for load in content["loads"]:
                try:
                    add_load(boat.key.id, load)
                    boat["loads"].append(load)
                except(APIError):
                    print("Load already on boat")

        return '', 204
    else:
        raise APIError(ERR_405_NO_METHOD)

@app.route('/boats/<boat_id>/loads/<load_id>', methods=['PUT'])
def add_load(boat_id,load_id):
    # Authenticate owner
    payload = verify_jwt(request)
    boat_key, boat = get_boat(boat_id)
    authorize_boat_owner(payload, boat)
    load_key, load = get_load(load_id)
    
    # Check if the boat and/or load exists
    if not boat or not load:
        raise APIError(ERR_404_INVALID_ID)
    # Check if load is on another boat
    if load["carrier"]:
        raise APIError(ERR_403_LOAD)
    # Add boat to load
    load["carrier"] = int(boat_id)
    # Add load to boat
    boat["loads"].append(int(load_id))
    # Update both boat and load
    client.put(load)
    client.put(boat)
    return '', 204

@app.route('/boats/<boat_id>/loads/<load_id>', methods=['DELETE'])
def delete_load(boat_id,load_id):
    # Authenticate owner
    payload = verify_jwt(request)
    boat_key, boat = get_boat(boat_id)
    authorize_boat_owner(payload, boat)
    load_key, load = get_load(load_id)
    
    # Check if the boat and/or load exists
    if not boat or not load:
        raise APIError(ERR_404_INVALID_ID)
    for item in boat["loads"]:
        if item == int(load_id):
            # Remove load from boat
            boat["loads"].remove(item)
            client.put(boat)
            # Update load carrier
            load["carrier"] = None
            client.put(load)
            return '', 204
    # Return 404 if the load was not found on the boat
    raise APIError(ERR_404_INVALID_ID)

# ---------------------------------------------
#           LOADS APP ROUTES
# ---------------------------------------------

@app.route('/loads', methods=['POST','GET'])
def loads_get_post():
    if request.method == 'POST':
        validate_content_type(request)

        content = request.get_json()
        new_load = datastore.entity.Entity(key=client.key(constants.loads))
        try:
            new_load.update({
                "volume": content["volume"],
                "carrier": None,
                "item": content["item"],
                "creation_date": content["creation_date"]
                })
        except(KeyError):
            return ERR_400_INVALID_ATTR
        client.put(new_load)
        # Return the new load attributes
        data = {
            "id": new_load.key.id,
            "volume": new_load["volume"],
            "carrier": new_load["carrier"],
            "item": new_load["item"],
            "creation_date": new_load["creation_date"],
            "self": request.base_url + '/' + str(new_load.key.id)
        }
        res = make_response(data)
        res.mimetype = constants.application_json
        res.status_code = 201
        return res
    elif request.method == 'GET':
        validate_content_type(request)
        # Apply pagination to results
        query = client.query(kind=constants.loads)
        q_limit = int(request.args.get('limit', '5'))
        q_offset = int(request.args.get('offset', '0'))
        l_iterator = query.fetch(limit= q_limit, offset=q_offset)
        pages = l_iterator.pages
        results = list(next(pages))
        if l_iterator.next_page_token:
            next_offset = q_offset + q_limit
            next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
        else:
            next_url = None
        repr_results = []
        for load in results:
            repr_results.append(create_load_repr(load))
        data = {"loads": repr_results}
        if next_url:
            data["next"] = next_url
        res = make_response(json.dumps(data))
        res.mimetype = constants.application_json
        res.status_code = 200
        return res
    else:
        raise APIError(ERR_405_NO_METHOD)

@app.route('/loads/<id>', methods=['DELETE','GET', 'PUT', 'PATCH'])
def loads_get_put_patch_delete(id):
    load_key, load = get_load(id)
    if request.method == 'DELETE':
        # Send 404 error if no boat with the requested id exists
        if not load:
            raise APIError(ERR_404_INVALID_ID)
        # Get boat carrying this load
        if load["carrier"]:
            boat_key = client.key(constants.boats, int(load["carrier"]["id"]))
            boat = client.get(key=boat_key)
            for item in boat["loads"]:
                if item["id"] == id:
                    boat["loads"].remove(item)
                    client.put(boat)
                    continue

        client.delete(load_key)
        return '', 204
    elif request.method == 'GET':
        validate_content_type(request)
        # Send 404 error if no boat with the requested id exists
        if not load:
            raise APIError(ERR_404_INVALID_ID)
        load["id"] = load.key.id  # Add id value to response
        load["self"] = request.base_url  # Add URL to response
        # Create carrier representation
        if load["carrier"]:
            temp = {
                "id": load["carrier"],
                "name": get_boat(load["carrier"])[1]["name"],
                "self": request.host_url + 'boats/' + str(load["carrier"])
            }
            load["carrier"] = temp
        res = make_response(json.dumps(load))
        res.status_code = 200
        res.mimetype = constants.application_json
        return res
    elif request.method == 'PUT':
        validate_content_type(request)
        
        # Replace load entity content
        content = request.get_json()
        load["volume"] = content["volume"]
        load["item"] = content["item"]
        load["creation_date"] = content["creation_date"]

        # Update load
        client.put(load)

        # Return the load object
        load["id"] = load.key.id  # Add id value to response
        load["self"] = request.base_url  # Add boat URL to response
        res = make_response(json.dumps(load))
        res.mimetype = constants.application_json
        res.status_code = 200
        return res
    elif request.method == 'PATCH':
        validate_content_type(request)
        
        # Replace boat entity content
        content = request.get_json()
        for attr in content:
            load[attr] = content[attr]

        # Update load
        client.put(load)
        return '', 204
    else:
        raise APIError(ERR_405_NO_METHOD)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)