import os
import json
import pymongo
import re

from bson.objectid import ObjectId

MONGO_HOST = os.environ.get("MONGOHOST")
MONGO_PORT = 27017

class Error(Exception):
  pass

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


def create_user(data):
  client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
  db = client.pyauth
  collection = db.users

  try:
    doc_id = collection.insert_one(data).inserted_id
    return doc_id

  except pymongo.errors.DuplicateKeyError:
    raise DuplicateAccount("create user", "an account exists with this email address")


def update_user(user_id, data):
  client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
  db = client.pyauth
  collection = db.users

  doc = collection.find_one_and_update({"userId" : str(user_id)},
                                       {"$set": data},
                                        upsert=False,
                                        return_document=pymongo.collection.ReturnDocument.AFTER)
  return doc


def get_user_by_email(email_address):
  client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
  db = client.pyauth
  collection = db.users
  documents = collection.find({"email": email_address})
  documents = list(documents)

  if len(documents) > 1:
    raise RecordError("get_users", "to many records returned")

  elif len(documents) == 0:
    return None

  return documents[0]


def get_user_by_id(user_id):
  client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
  db = client.pyauth
  collection = db.users
  documents = collection.find({"userId": user_id})
  documents = list(documents)

  if len(documents) > 1:
    raise RecordError("get_users", "to many records returned")

  elif len(documents) == 0:
    return None

  return documents[0]


def get_user_by_reset_code(reset_code):
  client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
  db = client.pyauth
  collection = db.users
  documents = collection.find({"$and": [{"status": {"$eq": "new"}}, {"resetCode": {"$eq": reset_code}}]})
  documents = list(documents)

  if len(documents) > 1:
    raise RecordError("get_users_for_reset", "to many records returned")

  elif len(documents) == 0:
    return None

  return documents[0]


def delete_user():
  # TODO - Once a way of setting permissions is added
  pass


def create_group(data):
  client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
  db = client.pyauth
  collection = db.groups

  try:
    doc_id = collection.insert_one(data).inserted_id
    return doc_id

  except pymongo.errors.DuplicateKeyError:
    raise DuplicateGroup("create group", "a group exists with this name")


def get_group_by_name(group_name):
  client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
  db = client.pyauth
  collection = db.groups
  documents = collection.find({"groupName": group_name})
  documents = list(documents)

  if len(documents) > 1:
    raise RecordError("get_group", "to many records returned")

  elif len(documents) == 0:
    return None

  return documents[0]


def get_group_by_id(group_id):
  client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
  db = client.pyauth
  collection = db.groups
  documents = collection.find({"groupId": group_id})
  documents = list(documents)

  if len(documents) > 1:
    raise RecordError("get_group", "to many records returned")

  elif len(documents) == 0:
    return None

  return documents[0]


def update_group(group_id, data):
  client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
  db = client.pyauth
  collection = db.groups

  doc = collection.find_one_and_update({"groupId" : str(group_id)},
                                       {"$set": data},
                                        upsert=False,
                                        return_document=pymongo.collection.ReturnDocument.AFTER)
  return doc


def find_groups_by_name(group_name):
  ''' Use basic regex to find names like that supplied
      Returns list of tuples: (ID, name)
  '''
  client = pymongo.MongoClient(MONGO_HOST, MONGO_PORT)
  db = client.pyauth
  collection = db.groups

  regex = re.compile('.*{}.*'.format(group_name))
  docs = collection.find({'groupName': regex})

  group_ids = list()
  for doc in docs:
    group_ids.append((doc['groupId'], doc['groupName']))

  return group_ids


if __name__ == "__main__":
  doc = find_groups_by_name("min")
  print(doc)
