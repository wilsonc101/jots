import html
import sys
from urllib.parse import urlparse

from functools import wraps

from flask import Flask, request, render_template, jsonify, make_response, redirect, url_for, Blueprint
from flask_jwt_extended import (
    JWTManager, jwt_required, jwt_optional, jwt_refresh_token_required,
    create_refresh_token, create_access_token,
    set_access_cookies, set_refresh_cookies, unset_jwt_cookies,
    get_jwt_identity, verify_jwt_in_request, get_raw_jwt
)

from jots.webapp import app
from jots.webapp import error_handlers

import jots.pyauth.user
import jots.pyauth.group

web_private_admin = Blueprint('private_webview_admin', __name__)
# /admin

def protected_view(func):
  ''' Decorator for views only accessible to administrators
  '''
  @wraps(func)
  def wrapper(*args, **kwargs):
    # Allow the use of a mock DB during testing
    if app.config['TESTING']:
      DB_CON = app.config['TEST_DB']
    else:
      DB_CON = None

    username = get_jwt_identity()
    try:
      user = jots.pyauth.user.user(email_address=username, db=DB_CON)
    except jots.pyauth.user.UserNotFound:
      raise error_handlers.InvalidUsage("access denied", status_code=403)
    except jots.pyauth.user.InputError:
      raise error_handlers.InvalidUsage("access denied", status_code=403)

    try:
      group = jots.pyauth.group.group(group_name="admin", db=DB_CON)
    except jots.pyauth.group.GroupNotFound:
      raise error_handlers.InvalidUsage("group not found", status_code=400)

    if user.properties.userId not in group.properties.members:
      raise error_handlers.InvalidUsage("access denied", status_code=403)

    return func(*args, **kwargs)
  return wrapper


@web_private_admin.route('/groups')
@jwt_required
@protected_view
def page_admin_group():
  return render_template("group_admin.tmpl",
                         api_url=app.config['DOMAIN_NAME'],
                         server_port=app.config['SERVER_PORT'])


@web_private_admin.route('/users')
@jwt_required
@protected_view
def page_admin_user():
  return render_template("user_admin.tmpl",
                         api_url=app.config['DOMAIN_NAME'],
                         server_port=app.config['SERVER_PORT'])


@web_private_admin.route('/apps')
@jwt_required
@protected_view
def page_admin_app():
  return render_template("app_admin.tmpl",
                         api_url=app.config['DOMAIN_NAME'],
                         server_port=app.config['SERVER_PORT'])

