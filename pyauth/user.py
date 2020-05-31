import bcrypt
import hashlib
import uuid
import datetime
import random
import string

from pyauth import mongo

# TODO - Add UUID check in user string method

class Error(Exception):
  pass

class InputError(Error):
  def __init__(self, expression, message):
    self.expression = expression
    self.message = message

class UserPropertyError(Error):
  def __init__(self, expression, message):
    self.expression = expression
    self.message = message

class UserActionError(Error):
  def __init__(self, expression, message):
    self.expression = expression
    self.message = message

class UserTokenError(Error):
  def __init__(self, expression, message):
    self.expression = expression
    self.message = message

class UserNotFound(Error):
  def __init__(self, expression, message):
    self.expression = expression
    self.message = message


class user_properties(object):
  ''' Readonly container for user properties
  '''
  def __init__(self, user_doc):
    for key in user_doc.keys():
      self.__dict__[key] = user_doc[key]

  def __setattr__(self, name, value):
    raise UserPropertyError("set property", "user properties are read-only, use update method")


class user(object):
  def __init__(self, email_address=None, user_id=None):
    ''' Uses supplied detail (email or ID) to find mongo record
        Dynamically populates class properties with mongo document content
    '''
    if email_address is None and user_id is None:
      raise InputError("get user", "one unique identifier must be provided - email, userid")

    if email_address is not None:
      _check_user_string(email_address)
      _check_email(email_address)

      user_details = mongo.get_user_by_email(email_address)
      if user_details is None:
        raise UserNotFound("user", "user not found")

    elif user_id is not None:
      _check_user_string(user_id)

      user_details = mongo.get_user_by_id(user_id)
      if user_details is None:
        raise UserNotFound("user", "user not found")

    # Drop Mongo doc ID before setting properties
    if "_id" in user_details:
      del user_details['_id']

    self.properties = user_properties(user_details)


  def authenticate(self, password):
    ''' Compare provided string against bcryted value
        Return boolean
    '''
    password = password.encode('utf-8')
    try:
      result = bcrypt.checkpw(password, self.properties.password)
      return result

    except AttributeError:
      # User has not set a password
      return False


  def set_password(self, password):
    password = password.encode('utf-8')
    password = bcrypt.hashpw(password, bcrypt.gensalt())
    self.update(password=password)
    return True


  def reset_password(self, service_domain, reset_validity_days=1):
    date_now = datetime.datetime.now()
    date_now_str = date_now.strftime("%d/%m/%YT%H:%M:%S.%f")
    date_reset_expiry = datetime.datetime.now() + datetime.timedelta(days=reset_validity_days)
    date_reset_expiry_str = date_reset_expiry.strftime("%d/%m/%YT%H:%M:%S.%f")

    # Convery user id back into uuid object
    user_id_uid = uuid.UUID(self.properties.userId)

    # Generate reset code
    reset_code_hash = hashlib.sha512()
    reset_code_hash.update(uuid.uuid5(user_id_uid, service_domain).hex.encode('utf-8'))
    reset_code_hash.update(date_now_str.encode('utf-8'))
    reset_code = reset_code_hash.hexdigest()

    # Set password to long random string
    temp_password = "".join([random.choice(string.ascii_letters + string.digits) for n in range(64)]).encode('utf-8')
    password = bcrypt.hashpw(temp_password, bcrypt.gensalt())

    self.update(status="reset",
                password=password,
                resetCode=reset_code,
                resetExpiry=date_reset_expiry_str)

    return reset_code


  def update(self, **kwargs):
    ''' Takes kwargs, converts to dict
        Updates mongo and local properties object if OK
    '''
    if len(kwargs.items()) < 1:
      raise InputError("update user", "no updates given")

    user_fields = dict()
    for key, value in kwargs.items():
      _check_user_string(key)
      _check_user_string(value)
      user_fields[key] = value

    updated_doc = mongo.update_user(self.properties.userId, user_fields)

    if updated_doc is None:
      raise UserActionError("update user", "no user document found to update")
    else:
      # Drop Mongo doc ID  before setting properties
      if "_id" in updated_doc:
        del updated_doc['_id']
      self.properties = user_properties(updated_doc)

    return True


## The following methods should raise errors if checks fail
## Set to pass until validation method defined
def _check_email(email_address):
  if "@" not in email_address or "." not in email_address:
    raise InputError("check_email", "invalid email address")
    # if email contains illegal chars, raise error

def _check_user_string(user_string):
  # if string contains illegal chars, raise error
  pass

def _check_password_complexity(password):
  # if password not complex, raise error
  pass


def create_user(service_domain, email_address, reset_validity_days=1):
  ''' Creates user based on email address
      domain name is used as seed for reset code
      returns reset code to be used in URL query string
      User must set initial password before login will succeed
  '''
  if not email_address:
    raise InputError("create_user", "email address required")

  if not service_domain:
    raise InputError("create_user", "domain required")

  _check_user_string(email_address)
  _check_email(email_address)

  date_now = datetime.datetime.now()
  date_now_str = date_now.strftime("%d/%m/%YT%H:%M:%S.%f")
  date_reset_expiry = datetime.datetime.now() + datetime.timedelta(days=reset_validity_days)
  date_reset_expiry_str = date_reset_expiry.strftime("%d/%m/%YT%H:%M:%S.%f")

  # Generate user ID
  user_id_uid = uuid.uuid4()
  user_id = str(user_id_uid)

  # Generate reset code
  reset_code_hash = hashlib.sha512()
  reset_code_hash.update(uuid.uuid5(user_id_uid, service_domain).hex.encode('utf-8'))
  reset_code_hash.update(date_now_str.encode('utf-8'))
  reset_code = reset_code_hash.hexdigest()

  user_fields = {"userId": user_id,
                 "status": "new",
                 "email": email_address,
                 "resetCode": reset_code,
                 "resetExpiry": date_reset_expiry_str}

  try:
    doc_id = mongo.create_user(user_fields)
    return reset_code

  except mongo.DuplicateAccount:
    raise UserActionError("create user", "user already exists")



