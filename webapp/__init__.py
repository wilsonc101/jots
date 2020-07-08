import os

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS

SECRET = os.environ.get("JWTSECRET")
ISSUER = os.environ.get("JWTISSUER")
BASE_URL = ISSUER # This shoud be a seperate envvar
SERVER_PORT = 5000 # Default server port

app = Flask(__name__)
app.config['SERVER_PORT'] = SERVER_PORT
app.config['DOMAIN_NAME'] = BASE_URL
app.config['JWT_SECRET_KEY'] = SECRET
app.config['JWT_COOKIE_DOMAIN'] = ISSUER
app.config['JWT_TOKEN_LOCATION'] = ['cookies', 'headers']
app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
app.config['JWT_COOKIE_SECURE'] = True
app.config['JWT_COOKIE_SAMESITE'] = "lax"
app.config['JWT_COOKIE_CSRF_PROTECT'] = True
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 30

jwt = JWTManager(app)
CORS(app)


from jots.webapp import error_handlers
from jots.webapp import public_api_endpoints
from jots.webapp import public_web_views
from jots.webapp import private_web_views

from jots.webapp import bp_private_api_common
from jots.webapp import bp_private_api_users
from jots.webapp import bp_private_api_groups
from jots.webapp import bp_private_api_apps

app.register_blueprint(bp_private_api_common.api_common, url_prefix="/api")
app.register_blueprint(bp_private_api_users.api_users, url_prefix="/api/v1/users")
app.register_blueprint(bp_private_api_groups.api_groups, url_prefix="/api/v1/groups")
app.register_blueprint(bp_private_api_apps.api_apps, url_prefix="/api/v1/apps")
