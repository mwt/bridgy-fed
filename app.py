"""Main Flask application."""
from flask import Flask, render_template
from flask_caching import Cache
import flask_gae_static
from google.cloud.ndb import AND, OR, Key
from oauth_dropins.webutil import (
    appengine_info,
    appengine_config,
    flask_util,
    util,
)

import common
from models import Response


app = Flask(__name__, static_folder=None)
app.template_folder = './templates'
app.config.from_mapping(
    ENV='development' if appengine_info.DEBUG else 'PRODUCTION',
    CACHE_TYPE='SimpleCache',
    SECRET_KEY=util.read('flask_secret_key'),
)
app.json.compact = False
app.url_map.converters['regex'] = flask_util.RegexConverter
app.after_request(flask_util.default_modern_headers)
app.register_error_handler(Exception, flask_util.handle_exception)
if appengine_info.DEBUG:
    flask_gae_static.init_app(app)

# don't redirect API requests with blank path elements
app.url_map.redirect_defaults = True

app.wsgi_app = flask_util.ndb_context_middleware(
    app.wsgi_app, client=appengine_config.ndb_client)

cache = Cache(app)

util.set_user_agent('Bridgy Fed (https://fed.brid.gy/)')


@app.get(f'/domain/<regex("{common.DOMAIN_RE}"):domain>')
def domain(domain):
    """Serves a domain page."""
    responses = Response.query(
        OR(AND(Response.key > Key('Response', f'http://{domain}/'),
               Response.key < Key('Response', f'http://{domain}{chr(ord("/") + 1)}')),
           AND(Response.key > Key('Response', f'https://{domain}/'),
               Response.key < Key('Response', f'https://{domain}{chr(ord("/") + 1)}')))
    ).order(-Response.updated)

    return render_template(
        'user.html',
        domain= domain,
        responses= responses,
        logs= logs,
        util= util,
    )


import activitypub, add_webmention, logs, redirect, render, salmon, superfeedr, webfinger, webmention
