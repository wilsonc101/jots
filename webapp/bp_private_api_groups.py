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
from jots.webapp.authorisation_decorators import (
    valid_id_required, app_write_enabled_required, user_is_admin
)

import jots.pyauth.user
import jots.pyauth.group
import jots.pyauth.app

api_groups = Blueprint('groups', __name__)
# /api/v1/groups/

@api_groups.route('/find', methods=['POST'])
@jwt_required
@valid_id_required
@user_is_admin
def api_findgroups():
  ''' Search for groups based on either group name or a user ID
      The two use different methods wihin the group moduel
      but should result in the same output
  '''
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidAPIUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  # Search by group name
  if 'groupname' in request_content:
    groupname = html.escape(request_content['groupname'])

    try:
      response = jots.pyauth.group.find_groups_like(groupname, db=DB_CON)
      return jsonify(response)

    except jots.pyauth.group.GroupNotFound:
      return jsonify(dict())

  # Search for group by member user id
  elif 'userid' in request_content:
    userid = html.escape(request_content['userid'])

    try:
      response = jots.pyauth.group.find_user_in_group(userid, db=DB_CON)
      return jsonify(response)

    except jots.pyauth.group.GroupNotFound:
      return jsonify(dict())

  else:
    raise error_handlers.InvalidAPIUsage("bad payload", status_code=400)


@api_groups.route('/new', methods=['POST'])
@jwt_required
@valid_id_required
@user_is_admin
@app_write_enabled_required
def api_newgroup():
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidAPIUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  if 'groupname' not in request_content:
    raise error_handlers.InvalidAPIUsage("bad payload", status_code=400)

  group_name = html.escape(request_content['groupname'])
  try:
    new_group = jots.pyauth.group.create_group(group_name, db=DB_CON)
    return jsonify(new_group)
  except jots.pyauth.group.GroupActionError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)


@api_groups.route('/delete', methods=['POST'])
@jwt_required
@valid_id_required
@user_is_admin
@app_write_enabled_required
def api_deletegroup():
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidAPIUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  if 'groupid' not in request_content:
    raise error_handlers.InvalidAPIUsage("bad payload", status_code=400)

  group_id = html.escape(request_content['groupid'])
  try:
    result = jots.pyauth.group.delete_group(group_id, db=DB_CON)
    return jsonify({"result": str(result)})
  except jots.pyauth.group.GroupNotFound as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)
  except jots.pyauth.group.GroupActionError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)



@api_groups.route('/<group_id>/members')
@jwt_required
@valid_id_required
@user_is_admin
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
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)
  except jots.pyauth.group.InputError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)


@api_groups.route('/<group_id>/members/add', methods=['POST'])
@jwt_required
@valid_id_required
@user_is_admin
@app_write_enabled_required
def api_groupmember_add(group_id):
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  group_id = html.escape(group_id)

  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidAPIUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  if 'email' not in request_content:
    raise error_handlers.InvalidAPIUsage("bad payload", status_code=400)

  email = html.escape(request_content['email'])
  try:
    print("-------------------------------")
    print(group_id)
    print("-------------------------------")
    group = jots.pyauth.group.group(group_id=group_id, db=DB_CON)
    new_member_list = group.add_member(email=email)
  except jots.pyauth.group.GroupNotFound as Err:
    raise error_handlers.InvalidAPIUsage("group not found - {}".format(Err), status_code=400)
  except jots.pyauth.group.InputError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)
  except jots.pyauth.group.GroupActionError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)

  try:
    new_member_list = group.get_members_detail(attribute="email")
    return jsonify(new_member_list)
  except jots.pyauth.group.GroupActionError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)
  except jots.pyauth.group.InputError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)


@api_groups.route('/<group_id>/members/remove', methods=['POST'])
@jwt_required
@valid_id_required
@user_is_admin
@app_write_enabled_required
def api_groupmember_remove(group_id):
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  group_id = html.escape(group_id)

  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidAPIUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  if 'userid' not in request_content:
    raise error_handlers.InvalidAPIUsage("bad payload", status_code=400)

  user_id = html.escape(request_content['userid'])

  try:
    group = jots.pyauth.group.group(group_id=group_id, db=DB_CON)
    new_member_list = group.remove_member(user_id=user_id, force=True)
  except jots.pyauth.group.GroupNotFound:
    raise error_handlers.InvalidAPIUsage("group not found", status_code=400)
  except jots.pyauth.group.InputError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)
  except jots.pyauth.group.GroupActionError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)

  try:
    new_member_list = group.get_members_detail(attribute="email")
    return jsonify(new_member_list)
  except jots.pyauth.group.GroupActionError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)
  except jots.pyauth.group.InputError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)
