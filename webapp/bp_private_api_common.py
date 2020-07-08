import html
import sys
import datetime

from functools import wraps

from flask import Flask, request, render_template, jsonify, make_response, redirect, Blueprint
from flask_jwt_extended import (
    JWTManager, jwt_required, jwt_optional, jwt_refresh_token_required,
    create_refresh_token, create_access_token,
    set_access_cookies, set_refresh_cookies, unset_jwt_cookies,
    get_jwt_identity, verify_jwt_in_request
)

from jots.webapp import app
from jots.webapp import error_handlers
from jots.mailer import send as mailer

import jots.pyauth.user
import jots.pyauth.group
import jots.pyauth.app

api_common = Blueprint('common', __name__)

@api_common.route('/')
@jwt_required
def api_index():
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  username = get_jwt_identity()
  user = jots.pyauth.user.user(email_address=username, db=DB_CON)

  response = {"version": "v1",
              "your_user": user.properties.userId}
  return jsonify(response)

