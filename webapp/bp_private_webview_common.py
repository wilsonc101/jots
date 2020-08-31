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

web_private_common = Blueprint('private_webview_common', __name__)

def protected_view(func):
  ''' Decorator for views only accessible to administryators
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


@web_private_common.route('/token/refresh')
@jwt_refresh_token_required
def refresh_get():
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  # Create the new access token
  current_user = get_jwt_identity()
  current_refresh_jti = get_raw_jwt()['jti']

  try:
    user = jots.pyauth.user.user(email_address=current_user, db=DB_CON)
  except jots.pyauth.user.UserNotFound:
    raise error_handlers.InvalidUsage("access denied", status_code=403)
  except jots.pyauth.user.InputError:
    raise error_handlers.InvalidUsage("access denied", status_code=403)

  # Check that refresh token given matches what is stored
  if current_refresh_jti != user.properties.refreshJti:
    return redirect(url_for('public_webview_common.logout', request_path=request.path))

  access_token = create_access_token(identity=current_user)

  if "request_path" in request.args:
    referrer_path = request.args.get("request_path")
    # if // or . is given, assumption is that it is a domain name so must be checked
    if "//" in referrer_path or "." in referrer_path:
      # Don't redirect to sites that don't share the same root domain.
      parsed_url = urlparse(referrer_path)
      domain_name = '{url.scheme}://{url.netloc}'.format(url=parsed_url)
      if app.config['DOMAIN_NAME'] not in domain_name:
        raise error_handlers.InvalidUsage("out of domain request", status_code=403)

    request_path = html.escape(request.args.get("request_path"))
  else:
    request_path = "/page"

  print("token refreshed, redirecting to {}".format(request_path))
  response = make_response(redirect(request_path))
  set_access_cookies(response, access_token)

  return response
