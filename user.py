from flask import Blueprint, request, make_response
from google.cloud import datastore
import constants
import json
from API_errors import *
from utils import APIError, validate_content_type, get_boat

client = datastore.Client()

bp = Blueprint('user', __name__, url_prefix='/users')

@bp.route("", methods=['GET'])
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