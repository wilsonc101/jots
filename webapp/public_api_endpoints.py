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

from webapp import app
from webapp import error_handlers

import pyauth.user


# FORM DATA
@app.route('/login', methods=["POST"])
def login_form():
  ''' Accepts login form data
      Get user object and check password
      Returns access and refresh tokens with CSRF tokens
  '''
  form_data = request.form

  username = html.escape(form_data['username'])
  password = form_data['password']

  try:
    user = pyauth.user.user(email_address=username)

  except pyauth.user.UserNotFound:
    raise error_handlers.InvalidUsage("access denied", status_code=403)

  except pyauth.user.InputError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)

  result = user.authenticate(password)
  if not result:
    raise error_handlers.InvalidUsage("access denied", status_code=403)

  access_token = create_access_token(identity=username)
  refresh_token = create_refresh_token(identity=username)

  response = make_response(redirect("/page"))
  set_access_cookies(response, access_token)
  set_refresh_cookies(response, refresh_token)

  return response


@app.route('/reset', methods=["POST"])
def reset_form():
  ''' Accepts password reset form data
      Validates reset code and sets password
      Returns to login if OK
  '''
  valid_reset_status = ['new', 'reset']

  form_data = request.form

  username = html.escape(form_data['username'])
  password = form_data['password']
  reset_code = html.escape(form_data['resetcode'])

  try:
    user = pyauth.user.user(email_address=username)

  except pyauth.user.UserNotFound:
    raise error_handlers.InvalidUsage("access denied", status_code=403)

  except pyauth.user.InputError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)

  # Check user status is suitable for a password reset
  if user.properties.status not in valid_reset_status:
    raise error_handlers.InvalidUsage("password not resetable", status_code=400)

  # Check for matching reset code
  if user.properties.resetCode != reset_code:
    raise error_handlers.InvalidUsage("invalid reset code", status_code=403)

  # Check reset code hasn't expired
  date_now = datetime.datetime.now()
  reset_expiry = datetime.datetime.strptime(user.properties.resetExpiry, "%d/%m/%YT%H:%M:%S.%f")
  if date_now > reset_expiry:
    raise error_handlers.InvalidUsage("expired reset code", status_code=403)

  try:
    user.set_password(password)
    user.update(resetCode="", resetExpiry="", status="active")

    response = make_response(redirect("/"))
    return response

  except pyauth.user.InputError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)

  except pyauth.user.UserActionError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)



# JSON
@app.route('/api/v1/users/new', methods=["POST"])
def api_newuser():
  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  if 'email' not in request_content:
    raise error_handlers.InvalidUsage("bad payload", status_code=400)

  email = html.escape(request_content['email'])

  # This should be the start of a verification process, short-circuit for now
  try:
    reset_code = pyauth.user.create_user(service_domain=app.config['DOMAIN_NAME'],
                                         email_address=email)

    # The next step is to email a link to the 'reset' page with a query string (q) containing reset code
    return jsonify({"status": "ok",
                    "reset_code": reset_code})

  except pyauth.user.UserActionError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)


@app.route('/api/v1/users/reset', methods=["POST"])
def api_passwordreset():
  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  if 'email' not in request_content:
    raise error_handlers.InvalidUsage("bad payload", status_code=400)

  email = html.escape(request_content['email'])

  user = pyauth.user.user(email_address=email)
  reset_code = user.reset_password(service_domain=app.config['DOMAIN_NAME'])

  # The next step is to email a link to the 'reset' page with a query string (q) containing reset code
  return jsonify({"status": "ok",
                  "reset_code": reset_code})


