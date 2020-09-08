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

web_private_example = Blueprint('private_webview_example', __name__)


@web_private_example.route('/page')
@jwt_required
def page():
  ''' Demo Landing page for all valid logins
      Page template performs AJAX request to API endpoint
      Outputs reponse to browser console log
  '''
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

  groups = jots.pyauth.group.find_user_in_group(user.properties.userId, db=DB_CON)

  group_links = list()
  if "admin" in groups.keys():
    group_links.append({"name": "user admin", "url": "/admin/users"})
    group_links.append({"name": "group admin", "url": "/admin/groups"})

  for group in groups.keys():
    group_obj = jots.pyauth.group.group(group_name=group, db=DB_CON)
    if "url" in group_obj.properties.as_dict():
      group_links.append({"name": group, "url": group_obj.properties.url})

  return render_template("page.tmpl",
                         api_url=app.config['DOMAIN_NAME'],
                         server_port=app.config['SERVER_PORT'],
                         protocol=app.config['SERVER_PROTOCOL'],
                         groups=group_links)


@web_private_example.route('/demo')
@jwt_required
def demo():
  ''' Text return for testing app calls
  '''
  return str(request.headers)
