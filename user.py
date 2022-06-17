from flask import Blueprint, request
from google.cloud import datastore
import json
from json2html import *
import constants

client = datastore.Client()

bp = Blueprint('user', __name__, url_prefix='/users')

@bp.route('', methods=['POST','GET'])
def users_get():
    pass