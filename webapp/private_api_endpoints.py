import html
import sys
import datetime

from functools import wraps

from flask import Flask, request, render_template, jsonify, make_response, redirect
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

def protected_view(func):
  ''' Decorator for views only accessible to administrators or apps
  '''
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  @wraps(func)
  def wrapper(*args, **kwargs):
    # Extract requesters identidy and confirm it's a valid user or app
    requester_id = get_jwt_identity()
    try:
      # Exceptions as 'passed' as they will be picked up by app check
      user_obj = None
      user_obj = jots.pyauth.user.user(email_address=requester_id, db=DB_CON)
      _check_group_permission("admin", user_obj.properties.userId)
    except jots.pyauth.user.UserNotFound:
      pass
    except jots.pyauth.user.InputError:
      pass

    if not user_obj:
      try:
        app_obj = jots.pyauth.app.app(app_name=requester_id, db=DB_CON)
      except jots.pyauth.app.AppNotFound:
        raise error_handlers.InvalidUsage("invalid requestor id", status=403)
      except jots.pyauth.user.InputError:
        raise error_handlers.InvalidUsage("invalid requestor id", status=403)

    return func(*args, **kwargs)
  return wrapper


def _check_group_permission(group_name, user_id):
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  try:
    group = jots.pyauth.group.group(group_name=group_name, db=DB_CON)
  except jots.pyauth.group.GroupNotFound:
    raise error_handlers.InvalidUsage("group not found", status_code=400)

  if user_id not in group.properties.members:
    raise error_handlers.InvalidUsage("access denied", status_code=403)

  return True


@app.route('/api')
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


@app.route('/api/v1/groups/find', methods=['POST'])
@jwt_required
@protected_view
def api_findgroups():
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  if 'groupname' not in request_content:
    raise error_handlers.InvalidUsage("bad payload", status_code=400)

  groupname = html.escape(request_content['groupname'])

  try:
    response = jots.pyauth.group.find_groups_like(groupname, db=DB_CON)
    return jsonify(response)

  except jots.pyauth.group.GroupNotFound:
    return jsonify(dict())


@app.route('/api/v1/groups/new', methods=['POST'])
@jwt_required
def api_newgroup():
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  username = get_jwt_identity()
  try:
    user = jots.pyauth.user.user(email_address=username, db=DB_CON)
  except jots.pyauth.user.UserNotFound:
    raise error_handlers.InvalidUsage("invalid user", status=403)

  _check_group_permission("admin", user.properties.userId)

  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  if 'groupname' not in request_content:
    raise error_handlers.InvalidUsage("bad payload", status_code=400)

  group_name = html.escape(request_content['groupname'])
  try:
    new_group = jots.pyauth.group.create_group(group_name, db=DB_CON)
    return jsonify(new_group)
  except jots.pyauth.group.GroupActionError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)


@app.route('/api/v1/groups/delete', methods=['POST'])
@jwt_required
def api_deletegroup():
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  username = get_jwt_identity()
  try:
    user = jots.pyauth.user.user(email_address=username, db=DB_CON)
  except jots.pyauth.user.UserNotFound:
    raise error_handlers.InvalidUsage("invalid user", status=403)

  _check_group_permission("admin", user.properties.userId)

  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  if 'groupid' not in request_content:
    raise error_handlers.InvalidUsage("bad payload", status_code=400)

  group_id = html.escape(request_content['groupid'])
  try:
    result = jots.pyauth.group.delete_group(group_id, db=DB_CON)
    return jsonify({"result": str(result)})
  except jots.pyauth.group.GroupNotFound as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)
  except jots.pyauth.group.GroupActionError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)



@app.route('/api/v1/groups/<group_id>/members')
@jwt_required
@protected_view
def api_groupmembers(group_id):
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  group_id = html.escape(group_id)

  try:
    group = jots.pyauth.group.group(group_id=group_id, db=DB_CON)
    group_members_with_email = group.get_members_detail(attribute="email")
    return jsonify(group_members_with_email)
  except jots.pyauth.group.GroupNotFound:
    return jsonify(dict())
  except jots.pyauth.group.GroupActionError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)
  except jots.pyauth.group.InputError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)


@app.route('/api/v1/groups/<group_id>/members/add', methods=['POST'])
@jwt_required
@protected_view
def api_groupmember_add(group_id):
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  group_id = html.escape(group_id)

  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  if 'email' not in request_content:
    raise error_handlers.InvalidUsage("bad payload", status_code=400)

  email = html.escape(request_content['email'])
  try:
    group = jots.pyauth.group.group(group_id=group_id, db=DB_CON)
    new_member_list = group.add_member(email=email)
  except jots.pyauth.group.GroupNotFound:
    raise error_handlers.InvalidUsage("group not found", status_code=400)
  except jots.pyauth.group.InputError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)
  except jots.pyauth.group.GroupActionError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)

  try:
    new_member_list = group.get_members_detail(attribute="email")
    return jsonify(new_member_list)
  except jots.pyauth.group.GroupActionError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)
  except jots.pyauth.group.InputError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)


@app.route('/api/v1/groups/<group_id>/members/remove', methods=['POST'])
@jwt_required
@protected_view
def api_groupmember_remove(group_id):
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  group_id = html.escape(group_id)

  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  if 'userid' not in request_content:
    raise error_handlers.InvalidUsage("bad payload", status_code=400)

  user_id = html.escape(request_content['userid'])

  try:
    group = jots.pyauth.group.group(group_id=group_id, db=DB_CON)
    new_member_list = group.remove_member(user_id=user_id, force=True)
  except jots.pyauth.group.GroupNotFound:
    raise error_handlers.InvalidUsage("group not found", status_code=400)
  except jots.pyauth.group.InputError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)
  except jots.pyauth.group.GroupActionError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)

  try:
    new_member_list = group.get_members_detail(attribute="email")
    return jsonify(new_member_list)
  except jots.pyauth.group.GroupActionError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)
  except jots.pyauth.group.InputError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)


@app.route('/api/v1/users/find', methods=['POST'])
@jwt_required
@protected_view
def api_findusers():
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  if 'email' not in request_content:
    raise error_handlers.InvalidUsage("bad payload", status_code=400)

  email_address = html.escape(request_content['email'])

  try:
    response = jots.pyauth.user.find_users_like(email_address, db=DB_CON)
    return jsonify(response)

  except jots.pyauth.group.GroupNotFound:
    return jsonify(dict())


@app.route('/api/v1/users/<user_id>/details')
@jwt_required
@protected_view
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
    raise error_handlers.InvalidUsage("invalid user", status=403)
  except jots.pyauth.user.InputError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)


@app.route('/api/v1/users/<user_id>/set/<user_attribute>', methods=['POST'])
@jwt_required
@protected_view
def api_set_user_attribute(user_id, user_attribute):
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  if "value" not in request_content:
    raise error_handlers.InvalidUsage("bad payload", status_code=400)

  user_id = html.escape(user_id)
  user_attribute = html.escape(user_attribute)
  attribute_value = html.escape(request_content['value'])

  try:
    user = jots.pyauth.user.user(user_id=user_id, db=DB_CON)
  except jots.pyauth.user.UserNotFound:
    raise error_handlers.InvalidUsage("invalid user", status=403)
  except jots.pyauth.user.InputError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)

  # Changing to reset status should trigger a password reset
  # Otherwise, use attribute change method
  if user_attribute == "status" and attribute_value == "reset":
    try:
      reset_code = user.reset_password(service_domain=app.config['DOMAIN_NAME'])
    except jots.pyauth.user.UserActionError as err:
      raise error_handlers.InvalidUsage(err.message, status_code=400)
    except jots.pyauth.user.InputError as err:
      raise error_handlers.InvalidUsage(err.message, status_code=400)

    # The next step is to email a link to the 'reset' page with a query string (q) containing reset code
    try:
      email_obj = mailer.personalised_email(recipient=user.properties.email,
                                            template_name="reset",
                                            data={"site_name": app.config['DOMAIN_NAME'],
                                                  "reset_url": "https://{}:5000/reset?q={}".format(app.config['DOMAIN_NAME'], reset_code)})
      if app.config['TESTING']:
        email_obj.send(mail_agent="file")
      else:
        email_obj.send()
    except mailer.InputError as err:
      raise error_handlers.InvalidUsage(err.message, status_code=400)
    except mailer.MailActionError as err:
      raise error_handlers.InvalidUsage(err.message, status_code=400)

    return jsonify({"new_value": user.properties.as_dict()[user_attribute]})

  else:
    try:
      user.update_named_attribute(user_attribute, attribute_value)
      return jsonify({"new_value": user.properties.as_dict()[user_attribute]})
    except jots.pyauth.user.InputError as err:
      raise error_handlers.InvalidUsage(err.message, status_code=400)
    except jots.pyauth.user.UserActionError as err:
      raise error_handlers.InvalidUsage(err.message, status_code=400)


@app.route('/api/v1/users/delete', methods=['POST'])
@jwt_required
@protected_view
def api_user_delete():
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  if "userid" not in request_content:
    raise error_handlers.InvalidUsage("bad payload", status_code=400)

  user_id = html.escape(request_content['userid'])

  try:
    result = jots.pyauth.user.delete_user(user_id, db=DB_CON)
    return jsonify({"result": str(result)})
  except jots.pyauth.user.UserActionError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)


@app.route('/api/v1/apps/find', methods=['POST'])
@jwt_required
@protected_view
def api_findapps():
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  if 'appname' not in request_content:
    raise error_handlers.InvalidUsage("bad payload", status_code=400)

  app_name = html.escape(request_content['appname'])

  try:
    response = jots.pyauth.app.find_apps_like(app_name, db=DB_CON)
    return jsonify(response)

  except jots.pyauth.app.AppNotFound:
    return jsonify(dict())


@app.route('/api/v1/apps/new', methods=['POST'])
@jwt_required
@protected_view
def api_newapp():
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  if 'appname' not in request_content:
    raise error_handlers.InvalidUsage("bad payload", status_code=400)

  app_name = html.escape(request_content['appname'])
  try:
    app_id, app_key, app_secret = jots.pyauth.app.create_app(app_name, db=DB_CON)
    return jsonify({app_name: {"id": app_id, "key": app_key, "secret": app_secret}})
  except jots.pyauth.app.AppActionError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)


@app.route('/api/v1/apps/delete', methods=['POST'])
@jwt_required
@protected_view
def api_deleteapp():
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  if 'appid' not in request_content:
    raise error_handlers.InvalidUsage("bad payload", status_code=400)

  app_id = html.escape(request_content['appid'])
  try:
    result = jots.pyauth.app.delete_app(app_id, db=DB_CON)
    return jsonify({"result": str(result)})
  except jots.pyauth.group.AppNotFound as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)
  except jots.pyauth.group.AppActionError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)
