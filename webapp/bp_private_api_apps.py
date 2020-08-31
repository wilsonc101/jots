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

api_apps = Blueprint('apps', __name__)
# /api/v1/apps


@api_apps.route('/find', methods=['POST'])
@jwt_required
@valid_id_required
@user_is_admin
def api_findapps():
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidAPIUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  if 'appname' not in request_content:
    raise error_handlers.InvalidAPIUsage("bad payload", status_code=400)

  app_name = html.escape(request_content['appname'])

  try:
    response = jots.pyauth.app.find_apps_like(app_name, db=DB_CON)
    return jsonify(response)

  except jots.pyauth.app.AppNotFound:
    return jsonify(dict())


@api_apps.route('/new', methods=['POST'])
@jwt_required
@valid_id_required
@user_is_admin
@app_write_enabled_required
def api_newapp():
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidAPIUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  if 'appname' not in request_content:
    raise error_handlers.InvalidAPIUsage("bad payload", status_code=400)

  # Default to read-only apps
  app_attributes = {"writeEnabled": "False"}
  if 'writeenabled' in request_content:
    if request_content['writeenabled'] is True:
      app_attributes['writeEnabled'] = "True"

  app_name = html.escape(request_content['appname'])
  try:
    app_id, app_key, app_secret = jots.pyauth.app.create_app(app_name, attributes=app_attributes, db=DB_CON)
    return jsonify({app_name: {"id": app_id, "key": app_key, "secret": app_secret}})
  except jots.pyauth.app.AppActionError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)


@api_apps.route('/delete', methods=['POST'])
@jwt_required
@valid_id_required
@user_is_admin
@app_write_enabled_required
def api_deleteapp():
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  # Reject non-JSON payload
  if not request.json:
    raise error_handlers.InvalidAPIUsage("bad payload format", status_code=400)

  request_content = request.get_json()
  if 'appid' not in request_content:
    raise error_handlers.InvalidAPIUsage("bad payload", status_code=400)

  app_id = html.escape(request_content['appid'])
  try:
    result = jots.pyauth.app.delete_app(app_id, db=DB_CON)
    return jsonify({"result": str(result)})
  except jots.pyauth.group.AppNotFound as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)
  except jots.pyauth.group.AppActionError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)


@api_apps.route('/<app_id>/key')
@jwt_required
@valid_id_required
@user_is_admin
def api_get_appkey(app_id):
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  app_id = html.escape(app_id)
  try:
    app_object = jots.pyauth.app.app(app_id=app_id, db=DB_CON)
  except jots.pyauth.app.InputError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)
  except jots.pyauth.app.AppNotFound as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)

  return app_object.properties.key


@api_apps.route('/<app_id>/details')
@jwt_required
@valid_id_required
@user_is_admin
def api_get_appdetails(app_id):
  # Allow the use of a mock DB during testing
  if app.config['TESTING']:
    DB_CON = app.config['TEST_DB']
  else:
    DB_CON = None

  app_id = html.escape(app_id)
  try:
    app_object = jots.pyauth.app.app(app_id=app_id, db=DB_CON)
  except jots.pyauth.app.InputError as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)
  except jots.pyauth.app.AppNotFound as err:
    raise error_handlers.InvalidAPIUsage(err.message, status_code=400)

  return app_object.properties.as_dict()
