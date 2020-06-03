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

from jots.webapp import app
from jots.webapp import error_handlers

import jots.pyauth.user
import jots.pyauth.group

# Allow the use of a mock DB during testing
if app.config['TESTING']:
  DB_CON = app.config['TEST_DB']
else:
  DB_CON = None


def _check_group_permission(group_name, user_id):
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
  username = get_jwt_identity()
  user = jots.pyauth.user.user(email_address=username, db=DB_CON)

  response = {"version": "v1",
              "your_user": user.properties.userId}
  return jsonify(response)


@app.route('/api/v1/groups/find', methods=['POST'])
@jwt_required
def api_findgroups():
  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  if 'groupname' not in request_content:
    raise error_handlers.InvalidUsage("bad payload", status_code=400)

  groupname = html.escape(request_content['groupname'])

  username = get_jwt_identity()
  user = jots.pyauth.user.user(email_address=username, db=DB_CON)
  _check_group_permission("admin", user.properties.userId)

  try:
    response = jots.pyauth.group.find_groups_like(groupname, db=DB_CON)
    return jsonify(response)

  except jots.pyauth.group.GroupNotFound:
    return jsonify(dict())


@app.route('/api/v1/groups/new', methods=['POST'])
@jwt_required
def api_newgroup():
  pass

@app.route('/api/v1/groups/<group_id>/delete', methods=['POST'])
@jwt_required
def api_deletegroup():
  pass


@app.route('/api/v1/groups/<group_id>/members')
@jwt_required
def api_groupmembers(group_id):
  group_id = html.escape(group_id)

  username = get_jwt_identity()
  try:
    user = jots.pyauth.user.user(email_address=username, db=DB_CON)
  except jots.pyauth.user.UserNotFound:
    raise error_handlers.InvalidUsage("invalid user", status=403)

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
def api_groupmember_add(group_id):
  group_id = html.escape(group_id)

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
def api_groupmember_remove(group_id):
  group_id = html.escape(group_id)

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
  if 'userid' not in request_content:
    raise error_handlers.InvalidUsage("bad payload", status_code=400)

  user_id = html.escape(request_content['userid'])

  try:
    group = jots.pyauth.group.group(group_id=group_id, db=DB_CON)
    new_member_list = group.remove_member(user_id=user_id)
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
def api_findusers():
  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  if 'email' not in request_content:
    raise error_handlers.InvalidUsage("bad payload", status_code=400)

  email_address = html.escape(request_content['email'])

  username = get_jwt_identity()
  user = jots.pyauth.user.user(email_address=username, db=DB_CON)
  _check_group_permission("admin", user.properties.userId)

  try:
    response = jots.pyauth.user.find_users_like(email_address, db=DB_CON)
    return jsonify(response)

  except jots.pyauth.group.GroupNotFound:
    return jsonify(dict())
