import os
import json
import pymongo
import re

from bson.objectid import ObjectId

MONGO_HOST = os.environ.get("MONGOHOST")
MONGO_USER = os.environ.get("MONGOUSER")
MONGO_PASSWORD = os.environ.get("MONGOPASSWORD")
MONGO_PORT = 27017

class Error(Exception):
  pass

class ConnectionError(Error):
  def __init__(self, expression, message):
    self.expression = expression
    self.message = message

class RecordError(Error):
  def __init__(self, expression, message):
    self.expression = expression
    self.message = message

class DuplicateAccount(Error):
  def __init__(self, expression, message):
    self.expression = expression
    self.message = message

class DuplicateGroup(Error):
  def __init__(self, expression, message):
    self.expression = expression
    self.message = message

class DuplicateApp(Error):
  def __init__(self, expression, message):
    self.expression = expression
    self.message = message


class mongo(object):
  def __init__(self, mongo_host=None, mongo_port=None,
                     username=None, password=None):
    if mongo_host is not None:
      self.host = mongo_host
    elif mongo_host is None and MONGO_HOST:
      self.host = MONGO_HOST
    else:
      raise ConnectionError("new connection", "host name/address required")

    if mongo_port is not None:
      if not isinstance(mongo_port, int):
        raise ConnectionError("new connection", "port must be int")
      self.port = int(mongo_port)
    elif mongo_port is None and MONGO_PORT:
      self.port = MONGO_PORT
    else:
      raise ConnectionError("new connection", "port required")


    if username is not None:
      self.client = pymongo.MongoClient(self.host, self.port, username=username, password=password)
    else:
      self.client = pymongo.MongoClient(self.host, self.port, username=MONGO_USER, password=MONGO_PASSWORD)

    try:
      self.client.server_info()
    except pymongo.errors.ConnectionFailure:
      raise ConnectionError("new connection", "could not connect to host")

    self.users_collection = self.client.pyauth.users
    self.groups_collection = self.client.pyauth.groups
    self.apps_collection = self.client.pyauth.apps

  def clear_collections(self):
    # Required to allow unit testing to clear up after runs
    self.users_collection.delete_many({})
    self.groups_collection.delete_many({})
    self.apps_collection.delete_many({})


  def create_user(self, data):
    try:
      doc_id = self.users_collection.insert_one(data).inserted_id
      return doc_id

    except pymongo.errors.DuplicateKeyError:
      raise DuplicateAccount("create user", "an account exists with this email address")


  def update_user(self, user_id, data):
    doc = self.users_collection.find_one_and_update({"userId" : str(user_id)},
                                              {"$set": data},
                                               upsert=False,
                                               return_document=pymongo.collection.ReturnDocument.AFTER)
    return doc


  def get_user_by_email(self, email_address):
    documents = self.users_collection.find({"email": email_address})
    documents = list(documents)

    if len(documents) > 1:
      raise RecordError("get user", "to many records returned")

    elif len(documents) == 0:
      return None

    return documents[0]


  def get_user_by_id(self, user_id):
    documents = self.users_collection.find({"userId": user_id})
    documents = list(documents)

    if len(documents) > 1:
      raise RecordError("get user", "to many records returned")

    elif len(documents) == 0:
      return None

    return documents[0]


  def get_user_by_reset_code(self, reset_code):
    documents = self.users_collection.find({"$and": [{"status": {"$eq": "new"}}, {"resetCode": {"$eq": reset_code}}]})
    documents = list(documents)

    if len(documents) > 1:
      raise RecordError("user reset", "to many records returned")

    elif len(documents) == 0:
      return None

    return documents[0]


  def delete_user(self, user_id):
    result = self.users_collection.delete_one({"userId": str(user_id)})

    if result.deleted_count > 1:
      raise RecordError("delete user", "unexpected number of documents deleted")

    elif result.deleted_count == 0:
      raise RecordError("delete user", "no documents to be deleted")

    else:
      return True


  def find_users_by_email_address(self, email_address):
    ''' Use basic regex to find names like that supplied
        Returns list of tuples: (ID, name)
    '''
    regex = re.compile('.*{}.*'.format(email_address))
    docs = self.users_collection.find({'email': regex})

    user_ids = list()
    for doc in docs:
      user_ids.append((doc['userId'], doc['email']))

    return user_ids


  def create_group(self, data):
    try:
      doc_id = self.groups_collection.insert_one(data).inserted_id
      return doc_id

    except pymongo.errors.DuplicateKeyError:
      raise DuplicateGroup("create group", "a group exists with this name")


  def get_group_by_name(self, group_name):
    documents = self.groups_collection.find({"groupName": group_name})
    documents = list(documents)

    if len(documents) > 1:
      raise RecordError("get group", "to many records returned")

    elif len(documents) == 0:
      return None

    return documents[0]


  def get_group_by_id(self, group_id):
    documents = self.groups_collection.find({"groupId": group_id})
    documents = list(documents)

    if len(documents) > 1:
      raise RecordError("get group", "to many records returned")

    elif len(documents) == 0:
      return None

    return documents[0]


  def update_group(self, group_id, data):
    doc = self.groups_collection.find_one_and_update({"groupId" : str(group_id)},
                                                     {"$set": data},
                                                      upsert=False,
                                                      return_document=pymongo.collection.ReturnDocument.AFTER)
    return doc


  def find_groups_by_name(self, group_name):
    ''' Use basic regex to find names like that supplied
        Returns list of tuples: (ID, name)
    '''
    regex = re.compile('.*{}.*'.format(group_name))
    docs = self.groups_collection.find({'groupName': regex})

    groups = list()
    for doc in docs:
      groups.append((doc['groupId'], doc['groupName']))

    return groups


  def delete_group(self, group_id):
    result = self.groups_collection.delete_one({"groupId": str(group_id)})

    if result.deleted_count > 1:
      raise RecordError("delete group", "unexpected number of documents deleted")

    elif result.deleted_count == 0:
      raise RecordError("delete group", "no documents to be deleted")

    else:
      return True


  def find_user_groups(self, user_id):
    docs = self.groups_collection.find({"members": str(user_id)})
    docs = list(docs)

    groups = list()
    for doc in docs:
      groups.append((doc['groupId'], doc['groupName']))

    return groups


  def create_app(self, data):
    try:
      doc_id = self.apps_collection.insert_one(data).inserted_id
      return doc_id

    except pymongo.errors.DuplicateKeyError:
      raise DuplicateApp("create app", "an app exists with this name")


  def get_app_by_id(self, app_id):
    documents = self.apps_collection.find({"appId": app_id})
    documents = list(documents)

    if len(documents) > 1:
      raise RecordError("get app", "to many records returned")

    elif len(documents) == 0:
      return None

    return documents[0]


  def get_app_by_name(self, app_name):
    documents = self.apps_collection.find({"appName": app_name})
    documents = list(documents)

    if len(documents) > 1:
      raise RecordError("get app", "to many records returned")

    elif len(documents) == 0:
      return None

    return documents[0]


  def get_app_by_key(self, app_key):
    documents = self.apps_collection.find({"key": app_key})
    documents = list(documents)

    if len(documents) > 1:
      raise RecordError("get app", "to many records returned")

    elif len(documents) == 0:
      return None

    return documents[0]


  def delete_app(self, app_id):
    result = self.apps_collection.delete_one({"appId": str(app_id)})

    if result.deleted_count > 1:
      raise RecordError("delete app", "unexpected number of documents deleted")

    elif result.deleted_count == 0:
      raise RecordError("delete app", "no documents to be deleted")

    else:
      return True


  def find_apps_by_name(self, app_name):
    ''' Use basic regex to find names like that supplied
        Returns list of tuples: (ID, name)
    '''
    regex = re.compile('.*{}.*'.format(app_name))
    docs = self.apps_collection.find({'appName': regex})

    apps = list()
    for doc in docs:
      apps.append((doc['appId'], doc['appName']))

    return apps
