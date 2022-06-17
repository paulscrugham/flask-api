from flask import Blueprint, request, jsonify
from google.cloud import datastore
import json
import constants
from jwt import AuthError, verify_jwt
from html_errors import *

client = datastore.Client()

bp = Blueprint('boat', __name__, url_prefix='/boats')

@bp.route('', methods=['POST','GET'])
def boats_get_post():
    if request.method == 'POST':
        # validate JWT
        try:
            payload = verify_jwt(request)
        except AuthError as e:
            return jsonify(e.error), e.status_code
        
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
                # TODO: add owner ID from JWT
                "owner": payload["sub"],
                "loads": [],
                "self": request.base_url + '/' + str(boat.key.id)
                })
        except(KeyError):
            return ERR_400_INVALID_ATTR
        # Add new boat to Google Cloud Store
        client.put(new_boat)
        # Return the new boat attributes
        response = {
            "id": new_boat.key.id,
            "name": new_boat["name"],
            "length": new_boat["length"],
            "date_built": new_boat["date_built"],
            "owner": new_boat["owner"],
            "loads": [],
            "self": request.base_url + '/' + str(new_boat.key.id)
        }
        return json.dumps(response), 201
    elif request.method == 'GET':
        query = client.query(kind=constants.boats)
        q_limit = int(request.args.get('limit', '3'))  # default number of results is 3
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
                
        output = {"boats": results}
        # Add url of next page to output
        if next_url:
            output["next"] = next_url
        return json.dumps(output)
    else:
        return 'Method not recognized'

@bp.route('/<id>', methods=['DELETE','GET', 'PUT', 'PATCH'])
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
        boat_key = client.key(constants.boats, int(id))
        boat = client.get(key=boat_key)
        # Send 404 error if no boat with the requested id exists
        if not boat:
            return {"Error": "No boat with this boat_id exists"}, 404
        boat["id"] = boat.key.id  # Add id value to response
        boat["self"] = request.base_url  # Add boat URL to response
        # Add load URLs to response
        for load in boat["loads"]:
            load["self"] = request.host_url + 'loads/' + load["id"]
        return json.dumps(boat), 200
    elif request.method == 'PUT':
        boat_key = client.key(constants.boats, int(id))
        boat = client.get(key=boat_key)
        # Send 404 error if no boat with the requested id exists
        if not boat:
            return ERR_404_INVALID_ID
        # Iterate over provided attributes
        content = request.get_json()
        for attr in content:
            boat[attr] = content[attr]
        client.put(boat)
        # Return the boat object
        res = create_boat_res(boat)
        res = make_response(json.dumps(res))
        res.mimetype = 'application/json'
        res.status_code = 200
        return res
    elif request.method == 'PATCH':
        # TODO: add patch method for boats
        pass
    else:
        return 'Method not recognized'

@bp.route('/<boat_id>/loads/<load_id>', methods=['PUT','DELETE'])
def add_delete_load(boat_id,load_id):
    # Add a load to a boat
    if request.method == 'PUT':
        boat_key = client.key(constants.boats, int(boat_id))
        boat = client.get(key=boat_key)
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
        error_msg = {"Error": "No boat with this boat_id is loaded with the load with this load_id"}
        boat_key = client.key(constants.boats, int(boat_id))
        boat = client.get(key=boat_key)
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
        return 'Method not recognized'

