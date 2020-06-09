import uuid

from . import mongo


class Error(Exception):
  pass

class InputError(Error):
  def __init__(self, expression, message):
    self.expression = expression
    self.message = message

class GroupActionError(Error):
  def __init__(self, expression, message):
    self.expression = expression
    self.message = message

class GroupPropertyError(Error):
  def __init__(self, expression, message):
    self.expression = expression
    self.message = message

class GroupNotFound(Error):
  def __init__(self, expression, message):
    self.expression = expression
    self.message = message


class group_properties(object):
  ''' Readonly container for group properties
  '''
  def __init__(self, group_doc):
    for key in group_doc.keys():
      self.__dict__[key] = group_doc[key]

  def __setattr__(self, name, value):
    raise GroupPropertyError("set property", "group properties are read-only, use update methods")


class group(object):
  def __init__(self, group_name=None, group_id=None, db=None):
    if db is None:
      # This assumes host and port have been set in envvars
      self.db = mongo.mongo()
    else:
      self.db = db

    if group_name is None and group_id is None:
      raise InputError("group", "one unique identifier must be provided - name, groupid")

    if group_name is not None:
      _check_user_string(group_name)
      group_details = self.db.get_group_by_name(group_name)
      if group_details is None:
        raise GroupNotFound("group", "group not found")

    elif group_id is not None:
      _check_user_string(group_id)
      group_details = self.db.get_group_by_id(group_id)
      if group_details is None:
        raise GroupNotFound("group", "group not found")

    # Drop Mongo doc ID before setting properties
    if "_id" in group_details:
      del group_details['_id']

    self.properties = group_properties(group_details)


  def add_member(self, user_id=None, email=None):
    if user_id is None and email is None:
      raise InputError("group member", "one unique identifier must be provided - user id, email address")

    if user_id is not None:
      # Check user is real
      _check_user_string(user_id, is_uuid=True)

      user_details = self.db.get_user_by_id(user_id)
      if user_details is None:
        raise GroupActionError("group member", "user not found, can't be added")

    elif email is not None:
      _check_email(email)

      user_details = self.db.get_user_by_email(email)
      if user_details is None:
        raise GroupActionError("group member", "user not found, can't be added")

    if user_details['userId'] in self.properties.members:
      raise GroupActionError("group member", "user already in group")

    members_list = self.properties.members.copy()
    members_list.append(user_details['userId'])
    result = self.update(members=members_list)
    if result:
      return members_list


  def get_members_detail(self, attribute=None):
    ''' Iterate group member list
        Get user document
        Returns named attribute or whole document if not given
    '''
    if attribute is not None:
      if not isinstance(attribute, str):
        raise InputError("group member", "attribute must be a string")
      _check_user_string(attribute)

    user_details = dict()
    for user_id in self.properties.members:
      try:
        user_doc = self.db.get_user_by_id(user_id)
        if user_doc is None:
          raise GroupActionError("group member", "could not get details, user does not exist")
      except mongo.RecordError as err:
        raise GroupActionError("group member", err.message)

      if attribute is not None:
        if attribute in user_doc:
          user_details[user_id] = user_doc[attribute]
        else:
          user_details[user_id] = str()
      else:
        # Drop Mongo doc ID before setting properties
        if "_id" in user_doc:
          del user_doc['_id']

        user_details[user_id] = user_doc

    return user_details


  def remove_member(self, user_id=None, email=None, force=False):
    ''' Remove user from group member list
        Forcing allows the removal of user, by id, from member list
        regardless if they exist or not. This is to handle non-existent users
        where their details cannot be looked-up (i.e. email address will not be usable)
    '''
    if user_id is None and email is None:
      raise InputError("group member", "one unique identifier must be provided - user id, email address")

    if force and user_id is None:
      raise InputError("group member", "to forcefully remove a user, user id must be provided")

    if user_id is not None:
      _check_user_string(user_id, is_uuid=True)

      if not force:
        # If forcing, don't check for a valid user
        user_details = self.db.get_user_by_id(user_id)
        if user_details is None:
          raise GroupActionError("group member", "user not found, can't be removed")
        user_id = user_details['userId']

    elif email is not None:
      _check_email(email)

      user_details = self.db.get_user_by_email(email)
      if user_details is None:
        raise GroupActionError("group member", "user not found, can't be removed")
      user_id = user_details['userId']

    if user_id not in self.properties.members:
      raise GroupActionError("group member", "user not in group")

    members_list = self.properties.members.copy()
    members_list.remove(user_id)
    result = self.update(members=members_list)
    if result:
      return members_list


  def update(self, **kwargs):
    ''' Takes kwargs, converts to dict
        Updates mongo and local properties object if OK
    '''
    if len(kwargs.items()) < 1:
      raise InputError("update group", "no updates given")

    group_fields = dict()
    for key, value in kwargs.items():
      _check_user_string(key)
      _check_user_string(value)
      group_fields[key] = value

    updated_doc = self.db.update_group(self.properties.groupId, group_fields)

    if updated_doc is None:
      raise GroupActionError("update group", "no group document found to update")
    else:
      # Drop Mongo doc ID  before setting properties
      if "_id" in updated_doc:
        del updated_doc['_id']
      self.properties = group_properties(updated_doc)

    return True


def _check_email(email_address):
  if "@" not in email_address or "." not in email_address:
    raise InputError("check_email", "invalid email address")


def _check_user_string(user_string, is_uuid=False):
  illegal_chars = [".", "$"]
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


def delete_group(group_id, db=None):
  ''' Requires group ID
      Returns boolean
  '''
  if db is None:
    # This assumes host and port have been set in envvars
    db = mongo.mongo()

  if not group_id:
    raise InputError("group", "group id not given")

  _check_user_string(group_id, is_uuid=True)

  group_obj = group(group_id=group_id, db=db)
  if group_obj.properties.groupName == "admin":
    raise GroupActionError("delete group", "admin group cannot be deleted")

  try:
    result = db.delete_group(group_id)
    return result
  except mongo.RecordError as err:
    raise GroupActionError("delete group", err.message)



def create_group(group_name, group_members=[], db=None):
  ''' Requires a name
      Members must be given by their ID (uuid)
      Returns group ID
  '''
  if db is None:
    # This assumes host and port have been set in envvars
    db = mongo.mongo()

  if not group_name:
    raise InputError("group", "group name not given")

  _check_user_string(group_name)

  if not isinstance(group_members, list):
    raise InputError("group", "members must be in a list")

  # Check each member ID for illegal chars and that it's a valid uuid
  for member_id in group_members:
    _check_user_string(member_id, is_uuid=True)

  group_id = str(uuid.uuid4())

  group_fields = {"groupName": group_name,
                  "groupId": group_id,
                  "members": group_members}

  try:
    doc_id = db.create_group(group_fields)
    return {group_name: group_id}

  except mongo.DuplicateGroup:
      raise GroupActionError("group", "group already exists")


def find_groups_like(group_name, db=None):
  if db is None:
    # This assumes host and port have been set in envvars
    db = mongo.mongo()

  if not group_name:
    raise InputError("group", "group name not given")

  _check_user_string(group_name)

  groups = db.find_groups_by_name(group_name)

  if len(groups) == 0:
    raise GroupNotFound("find group", "no groups found")

  # Repack tuples for easier javascript iteration
  group_data = dict()
  for group_id, group_name in groups:
    group_data[group_name] = group_id

  return group_data


def find_user_in_group(user_id, db=None):
  ''' Returns tuple of group ID and name for all groups
      the given user ID is a memeber of
  '''
  if db is None:
    # This assumes host and port have been set in envvars
    db = mongo.mongo()

  if not user_id:
    raise InputError("find user groups", "user id not given")

  _check_user_string(user_id, is_uuid=True)
  groups = db.find_user_groups(user_id)

  # Repack tuples for easier javascript iteration
  group_data = dict()
  for group_id, group_name in groups:
    group_data[group_name] = group_id

  return group_data
