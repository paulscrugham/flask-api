from flask import Blueprint, request, make_response
from google.cloud import datastore
import constants
import json
from API_errors import *
from utils import APIError, validate_content_type, get_load, get_boat, create_load_repr

client = datastore.Client()

bp = Blueprint('load', __name__, url_prefix='/loads')

@bp.route('', methods=['POST','GET'])
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

@bp.route('/<id>', methods=['DELETE','GET', 'PUT', 'PATCH'])
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