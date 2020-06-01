import os

from flask import Flask
from flask_jwt_extended import JWTManager

#from pyauth import user as pyauth

SECRET = os.environ.get("JWTSECRET")
ISSUER = os.environ.get("JWTISSUER")
BASE_URL = ISSUER # This shoud be a seperate envvar

app = Flask(__name__)
app.config['DOMAIN_NAME'] = BASE_URL
app.config['JWT_SECRET_KEY'] = SECRET
app.config['JWT_COOKIE_DOMAIN'] = ISSUER
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
app.config['JWT_COOKIE_SECURE'] = True
app.config['JWT_COOKIE_SAMESITE'] = "lax"
app.config['JWT_COOKIE_CSRF_PROTECT'] = True
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 30

jwt = JWTManager(app)

from webapp import error_handlers
from webapp import public_api_endpoints
from webapp import private_api_endpoints

from webapp import public_web_views
from webapp import private_web_views
