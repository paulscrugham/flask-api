from flask import Blueprint, request, make_response
from google.cloud import datastore
import constants
import json
from API_errors import *
from jwt import verify_jwt
from utils import APIError, get_user_from_sub, validate_content_type, authorize_boat_owner, get_load, get_boat, create_boat_repr

client = datastore.Client()

bp = Blueprint('boat', __name__, url_prefix='/boats')

@bp.route('', methods=['POST','GET'])
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

@bp.route('/<id>', methods=['DELETE','GET', 'PUT', 'PATCH'])
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

@bp.route('/<boat_id>/loads/<load_id>', methods=['PUT'])
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

@bp.route('/<boat_id>/loads/<load_id>', methods=['DELETE'])
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