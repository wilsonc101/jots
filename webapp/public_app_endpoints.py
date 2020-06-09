import html
import sys
import datetime

from flask import Flask, request, render_template, jsonify, make_response, redirect
from flask_jwt_extended import (
    JWTManager, jwt_required, jwt_optional, jwt_refresh_token_required,
    create_refresh_token, create_access_token,
    set_access_cookies, set_refresh_cookies, unset_jwt_cookies,
    get_jwt_identity, verify_jwt_in_request
)

import jots.pyauth.user
from jots.webapp import app
from jots.webapp import error_handlers
from jots.mailer import send as mailer


@app.route('/api/v1/token', methods=["POST"])
def m2m_create_token():
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

