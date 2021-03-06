import html
import sys

from flask import Flask, request, render_template, jsonify, make_response, redirect, Blueprint
from flask_jwt_extended import (
    JWTManager, jwt_required, jwt_optional, jwt_refresh_token_required,
    create_refresh_token, create_access_token,
    set_access_cookies, set_refresh_cookies, unset_jwt_cookies,
    get_jwt_identity, verify_jwt_in_request, get_jwt_claims
)

from jots.webapp import app
from jots.webapp import error_handlers


web_root = Blueprint("public_webview_common", __name__)
# /

@web_root.route('/')
@jwt_optional
def index():
  if get_jwt_identity() is None:
    return render_template("login.tmpl",
                           api_url=app.config['DOMAIN_NAME'],
                           server_port=app.config['SERVER_PORT'],
                           protocol=app.config['SERVER_PROTOCOL'])

  else:
    return make_response(redirect("/page"))


@web_root.route('/logout')
def logout():
  response = make_response(redirect("/"))
  unset_jwt_cookies(response)
  return response


@web_root.route('/reset')
def reset():
  if not request.args:
    raise error_handlers.InvalidUsage("missing query string", status_code=400)

  args = request.args
  if "q" not in args:
    raise error_handlers.InvalidUsage("malformed query", status_code=400)

  reset_code = html.escape(request.args.get("q"))

  return render_template("reset.tmpl", reset_code=reset_code)






