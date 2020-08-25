import html
import sys
import datetime

from functools import wraps
from distutils.util import strtobool

from flask import Flask, request, render_template, jsonify, make_response, redirect, Blueprint, g
from flask_jwt_extended import (
    JWTManager, jwt_required, jwt_optional, jwt_refresh_token_required,
    create_refresh_token, create_access_token,
    set_access_cookies, set_refresh_cookies, unset_jwt_cookies,
    get_jwt_identity, verify_jwt_in_request, get_jwt_claims
)

from jots.webapp import app
from jots.webapp import error_handlers
from jots.mailer import send as mailer

import jots.pyauth.user
import jots.pyauth.group
import jots.pyauth.app

api_users = Blueprint('users', __name__)
# /api/v1/users

def valid_id_required(func):
  ''' Decorator for views only accessible to valid apps or users
      If valid app or user is found, populate 'g' object
  '''
  @wraps(func)
  def id_wrapper(*args, **kwargs):
    # Allow the use of a mock DB during testing
    if app.config['TESTING']:
      DB_CON = app.config['TEST_DB']
    else:
      DB_CON = None

    g.app_obj = None
    g.user_obj = None

    # Extract requesters identidy and confirm it's a valid app
    requester_id = get_jwt_identity()

    # App errors passed as we need to check that a user isn't authing before raising an error
    try:
      g.app_obj = jots.pyauth.app.app(app_name=requester_id, db=DB_CON)
    except jots.pyauth.app.AppNotFound:
      pass
    except jots.pyauth.user.InputError:
      pass

    try:
      g.user_obj = jots.pyauth.user.user(email_address=requester_id, db=DB_CON)
    except jots.pyauth.user.UserNotFound:
      pass
    except jots.pyauth.user.InputError:
      pass

    # Catch all - if neither object is populated, raise error
    if g.app_obj is None and g.user_obj is None:
      raise error_handlers.InvalidAPIUsage("access denied", status_code=403)

    return func(*args, **kwargs)
  return id_wrapper


def app_write_enabled_required(func):
  ''' Decorator for views only accessible to apps with write access
  '''
  @wraps(func)
  def app_req_rw_wrapper(*args, **kwargs):
    if g.app_obj is not None:
      if 'writeEnabled' not in g.app_obj.properties.attributes:
        raise error_handlers.InvalidAPIUsage("access denied", status_code=403)

      if not bool(strtobool(g.app_obj.properties.attributes['writeEnabled'])):
        raise error_handlers.InvalidAPIUsage("access denied", status_code=403)

    return func(*args, **kwargs)
  return app_req_rw_wrapper


def user_is_admin(func):
  ''' Decorator for views only accessible to users in admin group
  '''
  @wraps(func)
  def usr_adm_wrapper(*args, **kwargs):
    # Allow the use of a mock DB during testing
    if app.config['TESTING']:
      DB_CON = app.config['TEST_DB']
    else:
      DB_CON = None

    if g.user_obj is not None:
      # If user object was created, check user is admin
      try:
        group = jots.pyauth.group.group(group_name="admin", db=DB_CON)
      except jots.pyauth.group.GroupNotFound:
        raise error_handlers.InvalidAPIUsage("admin group not found", status_code=500)

      if g.user_obj.properties.userId not in group.properties.members:
        raise error_handlers.InvalidAPIUsage("access denied", status_code=403)

    return func(*args, **kwargs)
  return usr_adm_wrapper


@api_users.route('/new', methods=["POST"])
def api_newuser():
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidAPIUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  if 'email' not in request_content:
    raise error_handlers.InvalidAPIUsage("bad payload", status_code=400)

  email = html.escape(request_content['email'])
  if len(email) < 5:
    raise error_handlers.InvalidAPIUsage("bad email address", status_code=400)

  # This should be the start of a verification process, short-circuit for now
  try:
    reset_code = jots.pyauth.user.create_user(service_domain=app.config['DOMAIN_NAME'],
                                              email_address=email,
                                              db=DB_CON)

  except jots.pyauth.user.UserActionError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)

  # The next step is to email a link to the 'reset' page with a query string (q) containing reset code
  try:
    email_obj = mailer.personalised_email(recipient=email,
                                          template_name="newuser",
                                          data={"site_name": app.config['DOMAIN_NAME'],
                                                "reset_url": "https://{}:{}/reset?q={}".format(app.config['DOMAIN_NAME'],
                                                                                               app.config['SERVER_PORT'],
                                                                                               reset_code)})
    if app.config['TESTING']:
      email_obj.send(mail_agent="file")
    else:
      email_obj.send()
  except mailer.InputError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)
  except mailer.MailActionError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)

  return jsonify({"status": "ok",
                  "reset_code": reset_code})


@api_users.route('/reset', methods=["POST"])
def api_passwordreset():
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidAPIUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  if 'email' not in request_content:
    raise error_handlers.InvalidAPIUsage("bad payload", status_code=400)

  email = html.escape(request_content['email'])
  if len(email) < 5:
    raise error_handlers.InvalidAPIUsage("bad email address", status_code=400)

  try:
    user = jots.pyauth.user.user(email_address=email, db=DB_CON)
  except jots.pyauth.user.UserNotFound:
    raise error_handlers.InvalidAPIUsage("bad user", status_code=400)
  except jots.pyauth.user.InputError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)

  try:
    reset_code = user.reset_password(service_domain=app.config['DOMAIN_NAME'])
  except jots.pyauth.user.UserActionError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)
  except jots.pyauth.user.InputError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)

  # The next step is to email a link to the 'reset' page with a query string (q) containing reset code
  try:
    email_obj = mailer.personalised_email(recipient=email,
                                          template_name="reset",
                                          data={"site_name": app.config['DOMAIN_NAME'],
                                                "reset_url": "https://{}:{}/reset?q={}".format(app.config['DOMAIN_NAME'],
                                                                                               app.config['SERVER_PORT'],
                                                                                               reset_code)})
    if app.config['TESTING']:
      email_obj.send(mail_agent="file")
    else:
      email_obj.send()
  except mailer.InputError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)
  except mailer.MailActionError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)

  return jsonify({"status": "ok",
                  "reset_code": reset_code})


@api_users.route('/find', methods=['POST'])
@jwt_required
@valid_id_required
@user_is_admin
def api_findusers():
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None


  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidAPIUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  if 'email' not in request_content:
    raise error_handlers.InvalidAPIUsage("bad payload", status_code=400)

  email_address = html.escape(request_content['email'])

  try:
    response = jots.pyauth.user.find_users_like(email_address, db=DB_CON)
    return jsonify(response)

  except jots.pyauth.group.GroupNotFound:
    return jsonify(dict())


@api_users.route('/<user_id>/details')
@jwt_required
@valid_id_required
@user_is_admin
def api_user_details(user_id):
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  user_id = html.escape(user_id)

  try:
    user = jots.pyauth.user.user(user_id=user_id, db=DB_CON)
    return jsonify(user.properties.as_dict())
  except jots.pyauth.user.UserNotFound:
    raise error_handlers.InvalidAPIUsage("invalid user", status=403)
  except jots.pyauth.user.InputError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)


@api_users.route('/<user_id>/set/<user_attribute>', methods=['POST'])
@jwt_required
@valid_id_required
@user_is_admin
@app_write_enabled_required
def api_set_user_attribute(user_id, user_attribute):
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidAPIUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  if "value" not in request_content:
    raise error_handlers.InvalidAPIUsage("bad payload", status_code=400)

  user_id = html.escape(user_id)
  user_attribute = html.escape(user_attribute)
  attribute_value = html.escape(request_content['value'])

  try:
    user = jots.pyauth.user.user(user_id=user_id, db=DB_CON)
  except jots.pyauth.user.UserNotFound:
    raise error_handlers.InvalidAPIUsage("invalid user", status=403)
  except jots.pyauth.user.InputError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)

  # If changing status to reset, we should trigger a password reset
  # Else use attribute change method
  if user_attribute == "status" and attribute_value == "reset":
    try:
      reset_code = user.reset_password(service_domain=app.config['DOMAIN_NAME'])
    except jots.pyauth.user.UserActionError as err:
      raise error_handlers.InvalidAPIUsage(err.message, status_code=400)
    except jots.pyauth.user.InputError as err:
      raise error_handlers.InvalidAPIUsage(err.message, status_code=400)

    # Wmail a link to the 'reset' page with a query string (q) containing reset code
    try:
      email_obj = mailer.personalised_email(recipient=user.properties.email,
                                            template_name="reset",
                                            data={"site_name": app.config['DOMAIN_NAME'],
                                                  "reset_url": "https://{}:{}/reset?q={}".format(app.config['DOMAIN_NAME'],
                                                                                                 app.config['SERVER_PORT'],
                                                                                                 reset_code)})
      if app.config['TESTING']:
        email_obj.send(mail_agent="file")
      else:
        email_obj.send()
    except mailer.InputError as err:
      raise error_handlers.InvalidAPIUsage(err.message, status_code=400)
    except mailer.MailActionError as err:
      raise error_handlers.InvalidAPIUsage(err.message, status_code=400)

    return jsonify({"new_value": user.properties.as_dict()[user_attribute]})

  else:
    try:
      user.update_named_attribute(user_attribute, attribute_value)
      return jsonify({"new_value": user.properties.as_dict()[user_attribute]})
    except jots.pyauth.user.InputError as err:
      raise error_handlers.InvalidAPIUsage(err.message, status_code=400)
    except jots.pyauth.user.UserActionError as err:
      raise error_handlers.InvalidAPIUsage(err.message, status_code=400)


@api_users.route('/delete', methods=['POST'])
@jwt_required
@valid_id_required
@user_is_admin
@app_write_enabled_required
def api_user_delete():
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidAPIUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  if "userid" not in request_content:
    raise error_handlers.InvalidAPIUsage("bad payload", status_code=400)

  user_id = html.escape(request_content['userid'])

  try:
    result = jots.pyauth.user.delete_user(user_id, db=DB_CON)
    return jsonify({"result": str(result)})
  except jots.pyauth.user.UserActionError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)

