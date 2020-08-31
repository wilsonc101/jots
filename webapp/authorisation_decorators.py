from functools import wraps

from flask import g
from flask_jwt_extended import get_jwt_identity

from jots.webapp import app
from jots.webapp import error_handlers
import jots.pyauth.user
import jots.pyauth.group
import jots.pyauth.app


def valid_id_required(func):
  ''' Decorator for views only accessible to valid apps or users
      If valid app or user is found, populate 'g' object
  '''
  @wraps(func)
  def id_wrapper(*args, **kwargs):
    # Allow the use of a mock DB during testing
    if app.config['TESTING']:
      DB_CON = app.config['TEST_DB']
    else:
      DB_CON = None

    g.app_obj = None
    g.user_obj = None

    # Extract requesters identidy and confirm it's a valid app
    requester_id = get_jwt_identity()

    # App errors passed as we need to check that a user isn't authing before raising an error
    try:
      g.app_obj = jots.pyauth.app.app(app_name=requester_id, db=DB_CON)
    except jots.pyauth.app.AppNotFound:
      pass
    except jots.pyauth.user.InputError:
      pass

    try:
      g.user_obj = jots.pyauth.user.user(email_address=requester_id, db=DB_CON)
    except jots.pyauth.user.UserNotFound:
      pass
    except jots.pyauth.user.InputError:
      pass

    # Catch all - if neither object is populated, raise error
    if g.app_obj is None and g.user_obj is None:
      raise error_handlers.InvalidAPIUsage("access denied", status_code=403)

    return func(*args, **kwargs)
  return id_wrapper


def app_write_enabled_required(func):
  ''' Decorator for views only accessible to apps with write access
  '''
  @wraps(func)
  def app_req_rw_wrapper(*args, **kwargs):
    if g.app_obj is not None:
      if 'writeEnabled' not in g.app_obj.properties.attributes:
        raise error_handlers.InvalidAPIUsage("access denied", status_code=403)

      if not bool(strtobool(g.app_obj.properties.attributes['writeEnabled'])):
        raise error_handlers.InvalidAPIUsage("access denied", status_code=403)

    return func(*args, **kwargs)
  return app_req_rw_wrapper


def user_is_admin(func):
  ''' Decorator for views only accessible to users in admin group
  '''
  @wraps(func)
  def usr_adm_wrapper(*args, **kwargs):
    # Allow the use of a mock DB during testing
    if app.config['TESTING']:
      DB_CON = app.config['TEST_DB']
    else:
      DB_CON = None

    if g.user_obj is not None:
      # If user object was created, check user is admin
      try:
        group = jots.pyauth.group.group(group_name="admin", db=DB_CON)
      except jots.pyauth.group.GroupNotFound:
        raise error_handlers.InvalidAPIUsage("admin group not found", status_code=500)

      if g.user_obj.properties.userId not in group.properties.members:
        raise error_handlers.InvalidAPIUsage("access denied", status_code=403)

    return func(*args, **kwargs)
  return usr_adm_wrapper



