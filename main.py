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
import os

DEBUG = True

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'google_creds.json'

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

def authorize_station_owner(payload, station):
    # check that owner of received JWT matches that of the station
    if payload['sub'] != station['owner']:
        raise APIError(ERR_403_STATION_OWNER)

def get_reading(reading_id):
    reading_key = client.key(constants.readings, int(reading_id))
    reading = client.get(key=reading_key)
    return reading_key, reading

def get_station(station_id):
    station_key = client.key(constants.stations, int(station_id))
    station = client.get(key=station_key)
    return station_key, station

def get_user(user_id):
    user_key = client.key(constants.users, int(user_id))
    user = client.get(key=user_key)
    return user_key, user

def create_station_repr(station):
    station["id"] = station.key.id  # Add id value to response
    station["self"] = request.url_root + 'stations/' + str(station.key.id)  # Add station URL to response
    # Add reading representation to response
    rep_readings = []
    for reading in station["readings"]:
        temp = {
            "id": reading,
            "value": get_reading(reading)[1]["value"],
            "self": request.host_url + 'readings/' + str(reading)
            }
        rep_readings.append(temp)
    station["readings"] = rep_readings
    return station

def create_reading_repr(reading):
    reading["id"] = reading.key.id  # Add id value to response
    reading["self"] = request.url_root + 'readings/' +  str(reading.key.id) # Add URL to response
    # Create source representation
    if reading["source"]:
        temp = {
            "id": reading["source"],
            "name": get_station(reading["source"])[1]["name"],
            "self": request.host_url + 'stations/' + str(reading["source"])
        }
        reading["source"] = temp
    return reading

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
            'stations': []
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
            rep_stations = []
            for station in user["stations"]:
                temp = {}
                temp["id"] = station
                temp["name"] = get_station(station)[1]["name"]
                temp["self"] = request.url_root + 'stations/' + str(station)
                rep_stations.append(temp)
            user["stations"] = rep_stations
        res = make_response(json.dumps(data))
        res.mimetype = constants.application_json
        res.status_code = 200
        return res
    else:
        raise APIError(ERR_405_NO_METHOD)

# ---------------------------------------------
#           STATIONS APP ROUTES
# ---------------------------------------------

@app.route('/stations', methods=['POST','GET'])
def stations_get_post():
    # Authenticate owner
    payload = verify_jwt(request)
    
    if request.method == 'POST':
        validate_content_type(request)
        
        # Save request info in variable
        content = request.get_json()
        # Create new station entity object
        new_station = datastore.entity.Entity(key=client.key(constants.stations))
        new_station.update({
            "name": content["name"], 
            "reading_types": content["reading_types"],
            "on_since": content["on_since"],
            "owner": payload["sub"],
            "readings": []
            })
        
        # Add new station to Google Cloud Store
        client.put(new_station)

        # Update user entity
        query = client.query(kind=constants.users)
        query.add_filter("sub", "=", payload["sub"])
        user = list(query.fetch(limit=1))[0]
        user["stations"].append(new_station.key.id)
        client.put(user)

        # Return the new station attributes
        data = {
            "id": new_station.key.id,
            "name": new_station["name"],
            "reading_types": new_station["reading_types"],
            "on_since": new_station["on_since"],
            "owner": new_station["owner"],
            "readings": [],
            "self": request.base_url + '/' + str(new_station.key.id)
        }
        res = make_response(json.dumps(data))
        res.mimetype = constants.application_json
        res.status_code = 201
        return res

    elif request.method == 'GET':
        validate_content_type(request)
        query = client.query(kind=constants.stations)
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
        
        # Create list of station representations
        rep_results = []
        for station in results:
            rep_results.append(create_station_repr(station))
                
        data = {"stations": rep_results}
        # Add url of next page to output
        if next_url:
            data["next"] = next_url
        res = make_response(json.dumps(data))
        res.mimetype = constants.application_json
        res.status_code = 200
        return res
    else:
        raise APIError(ERR_405_NO_METHOD)

@app.route('/stations/<id>', methods=['DELETE','GET', 'PUT', 'PATCH'])
def stations_get_put_patch_delete(id):
    # Authenticate owner
    payload = verify_jwt(request)

    station_key, station = get_station(id)
    
    # Send 404 error if no station with the requested id exists
    if not station:
        raise APIError(ERR_404_INVALID_ID)
    
    # Authorize owner
    authorize_station_owner(payload, station)

    if request.method == 'DELETE':
        # Update the source attribute of all readings on this station
        for item in station["readings"]:
            reading_key, reading = get_reading(item)
            reading["source"] = None
            client.put(reading)

        # Update the stations attribute of the owner's user entity
        user = get_user_from_sub(payload["sub"])
        station_to_delete = [item for item in user["stations"] if item == station.key.id][0]
        user["stations"].remove(station_to_delete)
        client.put(user)

        # Delete the station
        client.delete(station_key)
        return '', 204
    elif request.method == 'GET':
        validate_content_type(request)
        station = create_station_repr(station)
        res = make_response(json.dumps(station))
        res.status_code = 200
        res.mimetype = constants.application_json
        return res
    elif request.method == 'PUT':
        validate_content_type(request)
        
        # Replace station entity content
        content = request.get_json()
        station["name"] = content["name"]
        station["on_since"] = content["on_since"]
        station["reading_types"] = content["reading_types"]

        update_station_owner(id, content["owner"])

        station["readings"] = []

        # Update station
        client.put(station)
        
        # Return the station object
        station = create_station_repr(station)
        res = make_response(json.dumps(station))
        res.mimetype = constants.application_json
        res.status_code = 200
        return res
    elif request.method == 'PATCH':
        validate_content_type(request)
        
        content = request.get_json()

        if "name" in content:
            station["name"] = content["name"]

        if "on_since" in content:
            station["on_since"] = content["on_since"]

        if "reading_types" in content:
            station["reading_types"] = content["reading_types"]

        if "owner" in content:
            update_station_owner(id, content["owner"])

        client.put(station)

        # Add any new readings
        if 'readings' in content:
            for reading in content["readings"]:
                try:
                    add_reading(station.key.id, reading)
                    station["readings"].append(reading)
                except(APIError):
                    print("reading already on station")

        return '', 204
    else:
        raise APIError(ERR_405_NO_METHOD)

@app.route('/stations/<station_id>/users/<user_id>', methods=['PUT', 'DELETE'])
def update_station_owner(station_id, user_id):
    if request.method == 'PUT':
        # Authenticate owner
        payload = verify_jwt(request)
        station = get_station(station_id)[1]
        authorize_station_owner(payload, station)
        new_user = get_user(user_id)[1]

        # Check if the station and/or user exists
        if not station or not new_user:
            raise APIError(ERR_404_INVALID_ID)

        # Check if the station is already owned by this user
        if new_user.key.id == user_id:
            raise APIError(ERR_403_SAME_STATION_OWNER)

        # Change station owner
        station["owner"] = new_user["sub"]
        # Add station to new user's list
        new_user["stations"].append(int(station_id))
        # Remove station from old user's list
        old_user = get_user_from_sub(payload["sub"])
        old_user["stations"].remove(new_user.key.id)

        # Update both station and users
        client.put(new_user)
        client.put(old_user)
        client.put(station)
        return '', 204
    else:
        raise APIError(ERR_405_NO_METHOD)

# ---------------------------------------------
#           READINGS APP ROUTES
# ---------------------------------------------

@app.route('/readings', methods=['POST','GET'])
def readings_get_post():
    if request.method == 'POST':
        validate_content_type(request)

        content = request.get_json()
        new_reading = datastore.entity.Entity(key=client.key(constants.readings))
        try:
            new_reading.update({
                "reading_type": content["reading_type"],
                "source": content["source"],
                "value": content["value"],
                "read_time": content["read_time"]
                })
        except(KeyError):
            return ERR_400_INVALID_ATTR
        client.put(new_reading)
        # Return the new reading attributes
        data = {
            "id": new_reading.key.id,
            "reading_type": new_reading["reading_type"],
            "source": new_reading["source"],
            "value": new_reading["value"],
            "read_time": new_reading["read_time"],
            "self": request.base_url + '/' + str(new_reading.key.id)
        }
        res = make_response(data)
        res.mimetype = constants.application_json
        res.status_code = 201
        return res
    elif request.method == 'GET':
        validate_content_type(request)
        # Apply pagination to results
        query = client.query(kind=constants.readings)
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
        for reading in results:
            repr_results.append(create_reading_repr(reading))
        data = {"readings": repr_results}
        if next_url:
            data["next"] = next_url
        res = make_response(json.dumps(data))
        res.mimetype = constants.application_json
        res.status_code = 200
        return res
    else:
        raise APIError(ERR_405_NO_METHOD)

@app.route('/readings/<id>', methods=['DELETE','GET', 'PUT', 'PATCH'])
def readings_get_put_patch_delete(id):
    reading_key, reading = get_reading(id)
    if request.method == 'DELETE':
        # Send 404 error if no station with the requested id exists
        if not reading:
            raise APIError(ERR_404_INVALID_ID)
        # Get station carrying this reading
        if reading["source"]:
            station_key = client.key(constants.stations, int(reading["source"]["id"]))
            station = client.get(key=station_key)
            for item in station["readings"]:
                if item["id"] == id:
                    station["readings"].remove(item)
                    client.put(station)
                    continue

        client.delete(reading_key)
        return '', 204
    elif request.method == 'GET':
        validate_content_type(request)
        # Send 404 error if no station with the requested id exists
        if not reading:
            raise APIError(ERR_404_INVALID_ID)
        reading["id"] = reading.key.id  # Add id value to response
        reading["self"] = request.base_url  # Add URL to response
        # Create source representation
        if reading["source"]:
            temp = {
                "id": reading["source"],
                "name": get_station(reading["source"])[1]["name"],
                "self": request.host_url + 'stations/' + str(reading["source"])
            }
            reading["source"] = temp
        res = make_response(json.dumps(reading))
        res.status_code = 200
        res.mimetype = constants.application_json
        return res
    elif request.method == 'PUT':
        validate_content_type(request)
        
        # Replace reading entity content
        content = request.get_json()
        reading["reading_type"] = content["reading_type"]
        reading["value"] = content["value"]
        reading["read_time"] = content["read_time"]

        # Update reading
        client.put(reading)

        # Return the reading object
        reading["id"] = reading.key.id  # Add id value to response
        reading["self"] = request.base_url  # Add station URL to response
        res = make_response(json.dumps(reading))
        res.mimetype = constants.application_json
        res.status_code = 200
        return res
    elif request.method == 'PATCH':
        validate_content_type(request)
        
        # Replace station entity content
        content = request.get_json()
        for attr in content:
            reading[attr] = content[attr]

        # Update reading
        client.put(reading)
        return '', 204
    else:
        raise APIError(ERR_405_NO_METHOD)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)