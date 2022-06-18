from google.cloud import datastore
from flask import Flask, request, url_for, render_template, redirect, jsonify, make_response
from os import environ as env
from dotenv import find_dotenv, load_dotenv
from authlib.integrations.flask_client import OAuth
from urllib.parse import quote_plus, urlencode
from jwt import AuthError, verify_jwt
from html_errors import *
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

@app.route("/users")
def users_get():
    # TODO: complete /GET users endpoint
    pass

# ---------------------------------------------
#           BOATS APP ROUTES
# ---------------------------------------------

@app.route('/boats', methods=['POST','GET'])
def boats_get_post():
    if request.method == 'POST':
        # verify JWT
        try:
            payload = verify_jwt(request)
        except AuthError as e:
            return jsonify(e.error), e.status_code

        # Validate that request format is JSON
        if request.content_type != constants.application_json:
            return ERR_415_INVALID_MIME
        
        # Save request info in variable
        content = request.get_json()
        # Create new boat entity object
        new_boat = datastore.entity.Entity(key=client.key(constants.boats))
        # try/except block to catch a missing attribute
        try: 
            new_boat.update({
                "name": content["name"], 
                "length": content["length"],
                "date_built": content["date_built"],
                "owner": payload["sub"],
                "loads": []
                })
        except(KeyError):
            return constants.ERR_400_INVALID_ATTR
        
        # Add new boat to Google Cloud Store
        client.put(new_boat)

        # Update user entity
        query = client.query(kind=constants.users)
        query.add_filter("sub", "=", new_boat["owner"])
        user = query.fetch()
        user["boats"].append({
            "name": new_boat["name"],
            "id": new_boat.key.id
        })
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
        # verify JWT
        try:
            payload = verify_jwt(request)
        except AuthError as e:
            return jsonify(e.error), e.status_code
        # Validate that request format is JSON
        if request.content_type != constants.application_json:
            return ERR_415_INVALID_MIME
        query = client.query(kind=constants.boats)
        query.add_filter("owner", "=", payload['sub'])
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
        # Add id of entity, self URL, and load info to results
        for boat in results:
            boat["id"] = boat.key.id
            boat["self"] = request.base_url + '/' + str(boat.key.id)
            for load in boat["loads"]:
                load["self"] = request.host_url + 'loads/' + str(load["id"])
                
        data = {"boats": results}
        # Add url of next page to output
        if next_url:
            data["next"] = next_url
        res = make_response(json.dumps(data))
        res.mimetype = constants.application_json
        res.status_code = 201
        return res
    else:
        return ERR_405_NO_METHOD

@app.route('/boats/<id>', methods=['DELETE','GET', 'PUT', 'PATCH'])
def boats_put_delete(id):
    if request.method == 'DELETE':
        boat_key = client.key(constants.boats, int(id))
        boat = client.get(key=boat_key)
        # Send 404 error if no boat with the requested id exists
        if not boat:
            return {"Error": "No boat with this boat_id exists"}, 404
        # Update the carrier attribute of all loads on this boat
        for item in boat["loads"]:
            load_key = client.key(constants.loads, int(item["id"]))
            load = client.get(key=load_key)
            load["carrier"] = None
            client.put(load)
        # Delete the boat
        client.delete(boat_key)
        return '', 204
    elif request.method == 'GET':
        # verify JWT
        try:
            payload = verify_jwt(request)
            if DEBUG: print("Received JWT verified for {}".format(payload['sub']))
        except AuthError as e:
            return jsonify(e.error), e.status_code
        
        # Validate that request format is JSON
        if request.content_type != constants.application_json:
            return ERR_415_INVALID_MIME
        
        boat_key = client.key(constants.boats, int(id))
        boat = client.get(key=boat_key)
        
        if not boat:
            return ERR_404_INVALID_ID

        if payload['sub'] != boat['owner']:
            return ERR_403_BOAT_OWNER
        
        boat["id"] = boat.key.id  # Add id value to response
        boat["self"] = request.base_url  # Add boat URL to response
        # Add load URLs to response
        for load in boat["loads"]:
            load["self"] = request.host_url + 'loads/' + load["id"]
        res = make_response(json.dumps(boat))
        res.status_code = 200
        res.mimetype = constants.application_json
        return res
    elif request.method == 'PUT':
        boat_key = client.key(constants.boats, int(id))
        boat = client.get(key=boat_key)

        if not boat:
            return ERR_404_INVALID_ID
        
        if payload['sub'] != boat['owner']:
            return ERR_403_BOAT_OWNER
        
        # Iterate over provided attributes
        content = request.get_json()
        for attr in content:
            boat[attr] = content[attr]
        client.put(boat)
        # Return the boat object
        res = create_boat_res(boat)
        res = make_response(json.dumps(res))
        res.mimetype = constants.application_json
        res.status_code = 200
        return res
    elif request.method == 'PATCH':
        # TODO: add patch method for boats
        pass
    else:
        return ERR_405_NO_METHOD

@app.route('/boats/<boat_id>/loads/<load_id>', methods=['PUT','DELETE'])
def add_delete_load(boat_id,load_id):
    # Add a load to a boat
    if request.method == 'PUT':
        # verify JWT
        try:
            payload = verify_jwt(request)
        except AuthError as e:
            return jsonify(e.error), e.status_code

        boat_key = client.key(constants.boats, int(boat_id))
        boat = client.get(key=boat_key)
        
        # check that owner of received JWT matches that of the boat
        if payload['sub'] != boat['owner']:
            return ERR_403_BOAT_OWNER

        load_key = client.key(constants.loads, int(load_id))
        load = client.get(key=load_key)
        # Check if the boat and/or load exists
        if not boat or not load:
            return {"Error": "The specified boat and/or load does not exist"}, 404
        # Check if load is on another boat
        if load["carrier"]:
            return {"Error": "The load is already loaded on another boat"}, 403
        # Add boat to load
        load["carrier"] = {
            "id": boat_id,
            "name": boat["name"]
        }
        # Add load to boat
        boat["loads"].append({
            "id": load_id,
            "item": load["item"]
        })
        # Update both boat and load
        client.put(load)
        client.put(boat)
        return '', 204
    elif request.method == 'DELETE':
        # verify JWT
        try:
            payload = verify_jwt(request)
        except AuthError as e:
            return jsonify(e.error), e.status_code
        error_msg = {"Error": "No boat with this boat_id is loaded with the load with this load_id"}
        
        boat_key = client.key(constants.boats, int(boat_id))
        boat = client.get(key=boat_key)

        # check that owner of received JWT matches that of the boat
        if payload['sub'] != boat['owner']:
            return ERR_403_BOAT_OWNER
        
        load_key = client.key(constants.loads, int(load_id))
        load = client.get(key=load_key)
        # Check if the boat and/or load exists
        if not boat or not load:
            return error_msg, 404
        for item in boat["loads"]:
            if item["id"] == load_id:
                # Remove load from boat
                boat["loads"].remove(item)
                client.put(boat)
                # Update load carrier
                load["carrier"] = None
                client.put(load)
                return '', 204
        # Return 404 if the load was not found on the boat
        return error_msg, 404
    else:
        return ERR_405_NO_METHOD

# ---------------------------------------------
#           LOADS APP ROUTES
# ---------------------------------------------

@app.route('/loads', methods=['POST','GET'])
def loads_get_post():
    if request.method == 'POST':
        # Validate that request format is JSON
        if request.content_type != constants.application_json:
            return ERR_415_INVALID_MIME
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
        # Validate that request format is JSON
        if request.content_type != constants.application_json:
            return ERR_415_INVALID_MIME
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
        for e in results:
            e["id"] = e.key.id
            e["self"] = request.base_url + '/' + str(e.key.id)
        data = {"loads": results}
        if next_url:
            data["next"] = next_url
        res = make_response(json.dumps(data))
        res.mimetype = constants.application_json
        res.status_code = 200
        return res
    else:
        return ERR_405_NO_METHOD

@app.route('/loads/<id>', methods=['DELETE','GET', 'PUT', 'PATCH'])
def loads_put_delete(id):
    if request.method == 'DELETE':
        load_key = client.key(constants.loads, int(id))
        load = client.get(key=load_key)
        # Send 404 error if no boat with the requested id exists
        if not load:
            return {"Error": "No load with this load_id exists"}, 404
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
        # Validate that request format is JSON
        if request.content_type != constants.application_json:
            return ERR_415_INVALID_MIME
        load_key = client.key(constants.loads, int(id))
        load = client.get(key=load_key)
        # Send 404 error if no boat with the requested id exists
        if not load:
            return {"Error": "No load with this load_id exists"}, 404
        load["id"] = load.key.id  # Add id value to response
        load["self"] = request.base_url  # Add URL to response
        # Populate carrier attribute
        if load["carrier"]:
            load["carrier"]["self"] = request.host_url + 'boats/' + load["carrier"]["id"]
        res = make_response(json.dumps(load))
        res.status_code = 200
        res.mimetype = constants.application_json
        return res
    elif request.method == 'PUT':
        # TODO: add put method for loads
        pass
    elif request.method == 'PATCH':
        # TODO: add patch method for loads
        pass
    else:
        return ERR_405_NO_METHOD


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)