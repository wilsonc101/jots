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
from jots.webapp.authorisation_decorators import (
    valid_id_required, app_write_enabled_required, user_is_admin
)

import jots.pyauth.user
import jots.pyauth.group

web_private_admin = Blueprint('private_webview_admin', __name__)
# /admin

@web_private_admin.route('/groups')
@jwt_required
@valid_id_required
@user_is_admin
def page_admin_group():
  return render_template("group_admin.tmpl",
                         api_url=app.config['DOMAIN_NAME'],
                         server_port=app.config['SERVER_PORT'],
                         protocol=app.config['SERVER_PROTOCOL'])


@web_private_admin.route('/users')
@jwt_required
@valid_id_required
@user_is_admin
def page_admin_user():
  return render_template("user_admin.tmpl",
                         api_url=app.config['DOMAIN_NAME'],
                         server_port=app.config['SERVER_PORT'],
                         protocol=app.config['SERVER_PROTOCOL'])


@web_private_admin.route('/apps')
@jwt_required
@valid_id_required
@user_is_admin
def page_admin_app():
  return render_template("app_admin.tmpl",
                         api_url=app.config['DOMAIN_NAME'],
                         server_port=app.config['SERVER_PORT'],
                         protocol=app.config['SERVER_PROTOCOL'])

