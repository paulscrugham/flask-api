from google.cloud import datastore
from flask import Flask, url_for, render_template, redirect, make_response
from os import environ as env
from dotenv import find_dotenv, load_dotenv
from authlib.integrations.flask_client import OAuth
from urllib.parse import quote_plus, urlencode

from jwt import AuthError
from API_errors import *
from utils import APIError
import constants
import os
import boat
import load
import user

DEBUG = True

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'google_creds.json'

client = datastore.Client()

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.register_blueprint(boat.bp)
app.register_blueprint(load.bp)
app.register_blueprint(user.bp)

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
#           ERROR HANDLER ROUTES
# ---------------------------------------------
@app.errorhandler(AuthError)
def handle_auth_exception(e):
    res = make_response({"Error": e.error["description"]})
    res.status_code = e.status_code
    res.content_type = "application/json"
    return res

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


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)