ERR_400_INVALID_ATTR = {
    "description": "The request object is missing at least one of the required attributes or an attribute is invalid.", 
    "status_code": 400
}

ERR_403_NAME_EXISTS = {
    "description": "The provided name attribute already exists.", 
    "status_code": 403
}

ERR_403_BOAT_OWNER = {
    "description": "This boat is owned by someone else.", 
    "status_code": 403
}

ERR_403_LOAD = {
    "description": "The load is already loaded on another boat",
    "status_code": 403
}

ERR_404_INVALID_ID = {
    "description": "Either no entity with this entity_id exists, or the entity relationship does not exist.",
    "status_code": 404
}

ERR_405_NO_METHOD = {
    "description": "Method not recognized",
    "status_code": 405
}

ERR_406_INVALID_ACCEPT = {
    "description": "The requested MIME type is not supported.",
    "status_code": 406
}

ERR_415_INVALID_MIME = {
    "description": "The MIME type of the request object is not accepted",
    "status_code": 415
}