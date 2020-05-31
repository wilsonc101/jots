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
import pyauth.group


def _check_group_permission(group_name, user_id):
  try:
    group = pyauth.group.group(group_name=group_name)
  except pyauth.group.GroupNotFound:
    raise error_handlers.InvalidUsage("group not found", status_code=400)

  if user_id not in group.properties.members:
    raise error_handlers.InvalidUsage("access denied", status_code=403)

  return True


@app.route('/api')
@jwt_required
def api_index():
  username = get_jwt_identity()
  user = pyauth.user.user(email_address=username)

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
  user = pyauth.user.user(email_address=username)
  _check_group_permission("admin", user.properties.userId)

  try:
    response = pyauth.group.find_groups_like(groupname)
    return jsonify(response)

  except pyauth.group.GroupNotFound:
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
    user = pyauth.user.user(email_address=username)
  except pyauth.user.UserNotFound:
    raise error_handlers.InvalidUsage("invalid user", status=403)

  try:
    group = pyauth.group.group(group_id=group_id)
    group_members_with_email = group.get_members_detail(attribute="email")
    return jsonify(group_members_with_email)
  except pyauth.group.GroupNotFound:
    return jsonify(dict())
  except pyauth.group.GroupActionError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)
  except pyauth.group.InputError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)


@app.route('/api/v1/groups/<group_id>/members/add', methods=['POST'])
@jwt_required
def api_groupmember_add(group_id):
  group_id = html.escape(group_id)

  username = get_jwt_identity()
  try:
    user = pyauth.user.user(email_address=username)
  except pyauth.user.UserNotFound:
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
    group = pyauth.group.group(group_id=group_id)
    new_member_list = group.add_member(email=email)
  except pyauth.group.GroupNotFound:
    raise error_handlers.InvalidUsage("group not found", status_code=400)
  except pyauth.group.InputError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)
  except pyauth.group.GroupActionError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)

  try:
    new_member_list = group.get_members_detail(attribute="email")
    return jsonify(new_member_list)
  except pyauth.group.GroupActionError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)
  except pyauth.group.InputError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)





@app.route('/api/v1/groups/<group_id>/members/remove', methods=['POST'])
@jwt_required
def api_groupmember_remove(group_id):
  group_id = html.escape(group_id)

  username = get_jwt_identity()
  try:
    user = pyauth.user.user(email_address=username)
  except pyauth.user.UserNotFound:
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
    group = pyauth.group.group(group_id=group_id)
    new_member_list = group.remove_member(user_id=user_id)
  except pyauth.group.GroupNotFound:
    raise error_handlers.InvalidUsage("group not found", status_code=400)
  except pyauth.group.InputError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)
  except pyauth.group.GroupActionError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)

  try:
    new_member_list = group.get_members_detail(attribute="email")
    return jsonify(new_member_list)
  except pyauth.group.GroupActionError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)
  except pyauth.group.InputError as err:
    raise error_handlers.InvalidUsage(err.message, status_code=400)


