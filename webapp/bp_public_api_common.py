import html
import sys
import datetime
import base64

from flask import Flask, request, render_template, jsonify, make_response, redirect, Blueprint
from flask_jwt_extended import (
    JWTManager, jwt_required, jwt_optional, jwt_refresh_token_required,
    create_refresh_token, create_access_token,
    set_access_cookies, set_refresh_cookies, unset_jwt_cookies,
    get_jwt_identity, verify_jwt_in_request, get_jti
)

import jots.pyauth.user
import jots.pyauth.group
from jots.webapp import app, jwt
from jots.webapp import error_handlers
from jots.mailer import send as mailer

api_root = Blueprint('root_api', __name__)

# FORM DATA
@api_root.route('/login', methods=["POST"])
def login_form():
  ''' Accepts login form data
      Get user object and check password
      Returns access and refresh tokens with CSRF tokens
  '''
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  form_data = request.form

  username = html.escape(form_data['username'])
  password = form_data['password']

  try:
    user = jots.pyauth.user.user(email_address=username, db=DB_CON)

  except jots.pyauth.user.UserNotFound:
    raise error_handlers.InvalidAPIUsage("access denied", status_code=403)

  except jots.pyauth.user.InputError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)

  if user.properties.status != "active":
    raise error_handlers.InvalidAPIUsage("access denied", status_code=403)

  result = user.authenticate(password)
  if not result:
    raise error_handlers.InvalidAPIUsage("access denied", status_code=403)

  # Add user claims - groups, all except admin
  group_data = jots.pyauth.group.find_user_in_group(user.properties.userId, db=DB_CON)
  group_names = list()
  for group in group_data.keys():
    if group != "admin":
      group_names.append(group)

  access_token = create_access_token(identity=username,
                                     user_claims={"groups": group_names})

  refresh_token = create_refresh_token(identity=username)
  refresh_jti = get_jti(refresh_token)

  try:
    user.set_refresh_jti(refresh_jti)
  except jots.pyauth.user.InputError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)
  except jots.pyauth.user.UserActionError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)

  response = make_response(redirect("/page"))
  set_access_cookies(response, access_token)
  set_refresh_cookies(response, refresh_token)

  return response


@api_root.route('/reset', methods=["POST"])
def reset_form():
  ''' Accepts password reset form data
      Validates reset code and sets password
      Returns to login if OK
  '''
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  valid_reset_status = ['new', 'reset']

  form_data = request.form

  username = html.escape(form_data['username'])
  password = form_data['password']
  reset_code = html.escape(form_data['resetcode'])

  try:
    user = jots.pyauth.user.user(email_address=username, db=DB_CON)
  except jots.pyauth.user.UserNotFound:
    raise error_handlers.InvalidAPIUsage("access denied", status_code=403)
  except jots.pyauth.user.InputError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)

  # Check user status is suitable for a password reset
  if user.properties.status not in valid_reset_status:
    raise error_handlers.InvalidAPIUsage("password not resetable", status_code=400)

  # Check for matching reset code
  if user.properties.resetCode != reset_code:
    raise error_handlers.InvalidAPIUsage("invalid reset code", status_code=403)

  # Check reset code hasn't expired
  date_now = datetime.datetime.now()
  reset_expiry = datetime.datetime.strptime(user.properties.resetExpiry, "%d/%m/%YT%H:%M:%S.%f")
  if date_now > reset_expiry:
    raise error_handlers.InvalidAPIUsage("expired reset code", status_code=403)

  try:
    user.set_password(password)
    response = make_response(redirect("/"))
    return response
  except jots.pyauth.user.InputError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)
  except jots.pyauth.user.UserActionError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)


# JSON
@api_root.route('/token/new')
def token_get():
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  if 'Authorization' not in request.headers:
    raise error_handlers.InvalidAPIUsage("missing autorization header", status_code=400)

  auth_header = request.headers.get('Authorization')
  if "Basic " in auth_header:
    auth_header = auth_header.split("Basic ")[1]

  b64_auth_content = base64.b64decode(auth_header).decode('utf-8').strip()

  if ":" not in b64_auth_content:
    raise error_handlers.InvalidAPIUsage("bad autorization header", status_code=400)

  key, secret = b64_auth_content.split(":")
  try:
    app_obj = jots.pyauth.app.app(app_key=key, db=DB_CON)
  except jots.pyauth.app.AppNotFound:
    raise error_handlers.InvalidAPIUsage("bad app", status_code=400)
  except jots.pyauth.app.InputError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)

  if app_obj.authenticate(secret):
    expires = datetime.timedelta(days=30)
    access_token = create_access_token(identity=app_obj.properties.appName,
                                       expires_delta=expires,
                                       user_claims={"appId": app_obj.properties.appId})
    return access_token
  else:
    raise error_handlers.InvalidAPIUsage("permission denied", status_code=403)






