import os

from flask import Flask, request, render_template, jsonify, make_response, redirect

from flask_jwt_extended import (
    JWTManager, jwt_required, jwt_optional, jwt_refresh_token_required,
    create_refresh_token, create_access_token,
    set_access_cookies, set_refresh_cookies, unset_jwt_cookies,
    get_jwt_identity, verify_jwt_in_request
)

SECRET = os.environ.get("JWTSECRET")
ISSUER = os.environ.get("JWTISSUER")
BASE_URL = ISSUER # This shoud be a seperate envvar

app = Flask(__name__)
app.config['DOMAIN_NAME'] = BASE_URL
app.config['JWT_SECRET_KEY'] = SECRET
app.config['JWT_COOKIE_DOMAIN'] = ISSUER
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
app.config['JWT_COOKIE_SECURE'] = True
app.config['JWT_COOKIE_SAMESITE'] = "lax"
app.config['JWT_COOKIE_CSRF_PROTECT'] = True
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 30
app.config['JWT_LOGIN_URL'] = "https://dev.localhost:5000/"
app.config['JWT_REFRESH_URL'] = "https://dev.localhost:5000/token/refresh"


jwt = JWTManager(app)


@jwt.expired_token_loader
def expired_token_callback(token):
  token_type = token['type']
  if token_type == "access":
    print("access token has expired - goto refresh")
    return redirect("{}?request_path={}".format(app.config['JWT_REFRESH_URL'], request.url), code=307)

  elif token_type == "refresh":
    print("refresh token has expired - goto root/login")
    response = make_response(redirect("{}".format(app.config['JWT_LOGIN_URL'])))
    return response

  else:
    raise InvalidUsage("unknown token type", status_code=403)

@jwt.needs_fresh_token_loader
def fresh_token_loader_callback():
  print("token is not fresh - goto refresh")
  return redirect("{}?request_path={}".format(app.config['JWT_REFRESH_URL'], request.url), code=307)


@jwt.invalid_token_loader
def invalid_token_callback():
  print("token is invalid - goto root/login")
  response = make_response(redirect("{}".format(app.config['JWT_LOGIN_URL'])))
  return response


@jwt.unauthorized_loader
def missing_token_callback(token):
  print("token is missing - goto root/login")
  response = make_response(redirect("{}".format(app.config['JWT_LOGIN_URL'])))
  return response



@app.route('/')
@jwt_required
def index():
  return str(get_jwt_identity())






if __name__ == "__main__":
  app.run(host='0.0.0.0',
          port="5500",
          debug=True,
          ssl_context='adhoc')




