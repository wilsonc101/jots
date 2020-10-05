import bcrypt
import hashlib
import uuid
import datetime
import random
import string
import copy

from . import mongo
#import mongo


class Error(Exception):
  pass

class InputError(Error):
  def __init__(self, expression, message):
    self.expression = expression
    self.message = message

class AppPropertyError(Error):
  def __init__(self, expression, message):
    self.expression = expression
    self.message = message

class AppActionError(Error):
  def __init__(self, expression, message):
    self.expression = expression
    self.message = message

class AppTokenError(Error):
  def __init__(self, expression, message):
    self.expression = expression
    self.message = message

class AppNotFound(Error):
  def __init__(self, expression, message):
    self.expression = expression
    self.message = message


class app_properties:
  ''' Readonly container for app properties
  '''
  def __init__(self, app_doc):
    for key in app_doc.keys():
      self.__dict__[key] = app_doc[key]

  def __setattr__(self, name, value):
    raise AppPropertyError("set property", "app properties are read-only, use update method")

  def as_dict(self):
    attr_as_dict = copy.deepcopy(self.__dict__)
    if "secret" in attr_as_dict:
      del attr_as_dict['secret']
    return attr_as_dict


class app:
  def __init__(self, app_name=None, app_id=None, app_key=None, db=None):
    ''' Uses supplied ID  to find mongo record
        Dynamically populates class properties with mongo document content
    '''
    if db is None:
      # This assumes host and port have been set in envvars
      self.db = mongo.mongo()
    else:
      self.db = db

    if app_name is None and app_id is None and app_key is None:
      raise InputError("get app", "app id or name is required")

    if app_name is not None:
      _check_user_string(app_name)
      app_details = self.db.get_app_by_name(app_name)

    elif app_id is not None:
      _check_user_string(app_id, is_uuid=True)
      app_details = self.db.get_app_by_id(app_id)

    elif app_key is not None:
      _check_user_string(app_key)
      app_details = self.db.get_app_by_key(app_key)

    if app_details is None:
      raise AppNotFound("get app", "app not found")

    # Drop Mongo doc ID before setting properties
    if "_id" in app_details:
      del app_details['_id']

    self.properties = app_properties(app_details)


  def authenticate(self, secret):
    secret = secret.encode('utf-8')
    try:
      result = bcrypt.checkpw(secret, self.properties.secret)
      return result

    except AttributeError:
      # Secret is not set
      return False


  def update(self, **kwargs):
    pass


def _check_user_string(user_string, is_uuid=False):
  illegal_chars = ["$", ";", ",", "(", ")"]
  for char in user_string:
    if char in illegal_chars:
      raise InputError("check", "bad string")

  # If string can't be converted to a UUID, raise error
  if is_uuid:
    try:
      uuid.UUID(user_string)
    except ValueError:
      raise InputError("check", "invalid id")

  return True


def delete_app(app_id, db=None):
  if db is None:
    # This assumes host and port have been set in envvars
    db = mongo.mongo()

  if not app_id:
    raise InputError("delete app", "app id not given")

  _check_user_string(app_id, is_uuid=True)

  try:
    result = db.delete_app(app_id=app_id)
    return result
  except mongo.RecordError as err:
    raise AppActionError("delete app", err.message)


def create_app(name, attributes=None, db=None):
  if db is None:
    # This assumes host and port have been set in envvars
    db = mongo.mongo()

  if not name:
    raise InputError("new app", "name not give")
  _check_user_string(name)

  if attributes is not None:
    if not isinstance(attributes, dict):
      raise InputError("new app", "attributes must be a dict")

    for attribute_name in attributes.keys():
      _check_user_string(attribute_name)
      _check_user_string(attributes[attribute_name])
  else:
    attributes = dict()

  app_id = str(uuid.uuid4())
  app_key = "".join([random.choice(string.ascii_lowercase + string.digits) for n in range(32)])
  app_secret = "".join([random.choice(string.ascii_letters + string.digits) for n in range(64)])

  app_fields = {"appId": app_id,
                "appName": name,
                "key": app_key,
                "secret": bcrypt.hashpw(app_secret.encode('utf-8'), bcrypt.gensalt()),
                "attributes": attributes}

  try:
    doc_id = db.create_app(app_fields)
    return (app_id, app_key, app_secret)

  except mongo.DuplicateApp:
    raise AppActionError("new app", "app already exists")


def find_apps_like(app_name, db=None):
  if db is None:
    # This assumes host and port have been set in envvars
    db = mongo.mongo()

  if not app_name:
    raise InputError("find app", "app name required")

  _check_user_string(app_name)

  apps = db.find_apps_by_name(app_name)

  app_data = dict()
  for app_id, app_name in apps:
    app_data[app_name] = app_id

  return app_data

