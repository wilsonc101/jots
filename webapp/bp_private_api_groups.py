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

api_groups = Blueprint('groups', __name__)
# /api/v1/groups/


def protected_view(func):
  ''' Decorator for views only accessible to administrators or apps
  '''
  @wraps(func)
  def wrapper(*args, **kwargs):
    # Allow the use of a mock DB during testing
    if app.config['TESTING']:
      DB_CON = app.config['TEST_DB']
    else:
      DB_CON = None

    # Extract requesters identidy and confirm it's a valid user or app
    requester_id = get_jwt_identity()
    try:
      # Exceptions as 'passed' as they will be picked up by app check
      user_obj = None
      user_obj = jots.pyauth.user.user(email_address=requester_id, db=DB_CON)
    except jots.pyauth.user.UserNotFound:
      pass
    except jots.pyauth.user.InputError:
      pass

    if user_obj:
      # If user object was created, check user is admin
      try:
        group = jots.pyauth.group.group(group_name="admin", db=DB_CON)
      except jots.pyauth.group.GroupNotFound:
        raise error_handlers.InvalidUsage("group not found", status_code=400)

      if user_obj.properties.userId not in group.properties.members:
        raise error_handlers.InvalidUsage("access denied", status_code=403)

    else:
      # No user object found, check if it's an app that's authing
      try:
        app_obj = jots.pyauth.app.app(app_name=requester_id, db=DB_CON)
      except jots.pyauth.app.AppNotFound:
        raise error_handlers.InvalidUsage("invalid requestor id", status_code=403)
      except jots.pyauth.user.InputError:
        raise error_handlers.InvalidUsage("invalid requestor id", status_code=403)

    return func(*args, **kwargs)
  return wrapper


@api_groups.route('/find', methods=['POST'])
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


@api_groups.route('/new', methods=['POST'])
@jwt_required
@protected_view
def api_newgroup():
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

  group_name = html.escape(request_content['groupname'])
  try:
    new_group = jots.pyauth.group.create_group(group_name, db=DB_CON)
    return jsonify(new_group)
  except jots.pyauth.group.GroupActionError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)


@api_groups.route('/delete', methods=['POST'])
@jwt_required
@protected_view
def api_deletegroup():
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

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



@api_groups.route('/<group_id>/members')
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


@api_groups.route('/<group_id>/members/add', methods=['POST'])
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


@api_groups.route('/<group_id>/members/remove', methods=['POST'])
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
