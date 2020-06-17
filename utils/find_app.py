import pymongo
import json

client = pymongo.MongoClient()
db = client.pyauth
collection = db.apps

documents = collection.find({"appName": "test"})
documents = list(documents)

print(documents)
