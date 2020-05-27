import pymongo
import json

client = pymongo.MongoClient()
db = client.pyauth
collection = db.groups

documents = collection.find({"groupName": "admin"})
documents = list(documents)

print(documents)
