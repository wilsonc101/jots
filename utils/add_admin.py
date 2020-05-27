import pymongo
import json
import sys

client = pymongo.MongoClient()
db = client.pyauth
collection = db.groups

documents = collection.find({"groupName": "admin"})
documents = list(documents)

members = documents[0]['members'].copy()

members.append(sys.argv[1])

doc = collection.find_one_and_update({"groupName": "admin"},
                                     {"$set": {"members": members}},
                                      upsert=False,
                                      return_document=pymongo.collection.ReturnDocument.AFTER)

