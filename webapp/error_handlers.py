from flask import make_response, redirect, jsonify, render_template, request, url_for

from jots.webapp import app, jwt

class InvalidUsage(Exception):
  status_code = 400
  def __init__(self, message, status_code=None, payload=None):
    Exception.__init__(self)
    self.message = message

    if status_code is not None:
        self.status_code = status_code

    self.payload = payload

  def to_dict(self):
    rv = dict(self.payload or ())
    rv['message'] = self.message
    return rv


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
  return render_template("error.tmpl",
                         error_message=error.message,
                         error_code=error.status_code,
                         error_data=error.payload), int(error.status_code)


@jwt.expired_token_loader
def expired_token_callback(token):
  token_type = token['type']
  if token_type == "access":
    print("access token has expired - goto refresh")
    return redirect(url_for('refresh_get', request_path=request.path))

  elif token_type == "refresh":
    print("refresh token has expired - goto root/login")
    response = make_response(redirect("/"))
    return response

  else:
    raise InvalidUsage("unknown token type", status_code=403)


@jwt.needs_fresh_token_loader
def fresh_token_loader_callback():
  print("token is not fresh - goto refresh")
  response = make_response(redirect("/token/refresh"))
  return response


@jwt.invalid_token_loader
def invalid_token_callback():
  print("token is invalid - goto root/login")
  response = make_response(redirect("/"))
  return response


@jwt.unauthorized_loader
def missing_token_callback(token):
  print("token is missing - goto root/login")
  response = make_response(redirect("/"))
  return response

