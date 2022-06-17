from flask import Blueprint, request, render_template, url_for
from google.cloud import datastore
import json
from json2html import *
from authlib.integrations.flask_client import OAuth
import constants

client = datastore.Client()

bp = Blueprint('auth', __name__, url_prefix='/auth')

def get_state(state):
    """
    Queries Datastore for the session with the matching state attribute.
    """
    # get session (Datastore entity with matching state attribute)
    query = client.query(kind=constants.states)
    results = list(query.fetch())
    for e in results:
        if e['state'] == state:
            return e
    return None

@bp.route("/")
def home():
    return render_template("home.html", state=None)

@bp.route("/userinfo/<state>")
def userinfo(state):
    curr_state = get_state(state)
    if not curr_state:
        return json.dumps({'Error': 'State could not be verified'}), 401
    return render_template("home.html", state=curr_state)

@bp.route("/login")
def login():
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

@bp.route("/callback", methods=["GET", "POST"])
def callback():
    # get token from auth0
    token = oauth.auth0.authorize_access_token()
    # create and store a session in Google Datastore
    random_string = str(uuid4())
    new_state = datastore.entity.Entity(key=client.key(constants.states))
    new_state.update({
        'state': random_string,
        'id_token': token['id_token'],
        'name': token['userinfo']['name']
        })
    client.put(new_state)
    return redirect("/userinfo/{}".format(random_string))

@bp.route("/logout")
def logout():
    # session.clear()
    # TODO: replace session.clear() with method to delete state from Datastore
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