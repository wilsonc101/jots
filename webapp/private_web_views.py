import html
import sys

from flask import Flask, request, render_template, jsonify, make_response, redirect
from flask_jwt_extended import (
    JWTManager, jwt_required, jwt_optional, jwt_refresh_token_required,
    create_refresh_token, create_access_token,
    set_access_cookies, set_refresh_cookies, unset_jwt_cookies,
    get_jwt_identity, verify_jwt_in_request
)

from webapp import app
import pyauth.user
import pyauth.group
from webapp import error_handlers


def _check_group_permission(group_name, user_id):
  try:
    group = pyauth.group.group(group_name=group_name)
  except pyauth.group.GroupNotFound:
    raise error_handlers.InvalidUsage("group not found", status_code=400)

  if user_id not in group.properties.members:
    raise error_handlers.InvalidUsage("access denied", status_code=403)

  return True


@app.route('/token/refresh')
@jwt_refresh_token_required
def refresh_get():
  # Create the new access token
  current_user = get_jwt_identity()
  access_token = create_access_token(identity=current_user)

  if "request_path" in request.args:
    request_path = html.escape(request.args.get("request_path"))
  else:
    request_path = "/page"

  print("token refreshed, redirecting to {}".format(request_path))
  response = make_response(redirect(request_path))
  set_access_cookies(response, access_token)

  return response


@app.route('/admin')
@jwt_required
def page_admin():
  username = get_jwt_identity()
  user = pyauth.user.user(email_address=username)

  _check_group_permission("admin", user.properties.userId)

  return render_template("admin.tmpl", api_url=app.config['DOMAIN_NAME'])


@app.route('/page')
@jwt_required
def page():
  ''' Demo Landing page for all valid logins
      Page template performs AJAX request to API endpoint
      Outputs reponse to browser console log
  '''
  username = get_jwt_identity()
  user = pyauth.user.user(email_address=username)
  return render_template("page.tmpl", api_url=app.config['DOMAIN_NAME'])


