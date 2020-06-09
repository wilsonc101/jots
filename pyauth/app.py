import bcrypt
import hashlib
import uuid
import datetime
import random
import string
import copy

from . import mongo


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


class app_properties(object):
  ''' Readonly container for app properties
  '''
  def __init__(self, app_doc):
    for key in app_doc.keys():
      self.__dict__[key] = app_doc[key]

  def __setattr__(self, name, value):
    raise AppPropertyError("set property", "app properties are read-only, use update method")

  def as_dict(self):
    attr_as_dict = copy.deepcopy(self.__dict__)
    if "password" in attr_as_dict:
      del attr_as_dict['password']
    return attr_as_dict


class app(object):
  def __init__(self, app_id=None, db=None):
    ''' Uses supplied ID  to find mongo record
        Dynamically populates class properties with mongo document content
    '''
    if db is None:
      # This assumes host and port have been set in envvars
      self.db = mongo.mongo()
    else:
      self.db = db

    if app_id is None:
      raise InputError("get app", "app id not given")

    _check_user_string(app_id, is_uuid=True)

    app_details = self.db.get_app_by_id(app_id)
    if app_details is None:
      raise AppNotFound("get app", "app not found")

    # Drop Mongo doc ID before setting properties
    if "_id" in app_details:
      del app_details['_id']

    self.properties = app_properties(app_details)


  def authenticate(self, password):
    pass


  def update(self, **kwargs):
    pass


def _check_user_string(user_string, is_uuid=False):
  illegal_chars = ["$", ";", ","]
  for char in user_string:
    if char in illegal_chars:
      raise InputError("check", "bad string")

  # If string can't be converted to a UUID, raise error
  if is_uuid:
    try:
      uuid.UUID(user_string)
    except ValueError:
      raise InputError("group", "invalid user id given")

  return True


def delete_app(app_id, db=None):
  pass

def create_app(service_domain, db=None):
  pass

