import pymongo
import json


client = pymongo.MongoClient(username="pyauthadmin", password="password")
db = client.pyauth
collection = db.apps

documents = collection.find({"appName": "a"})
documents = list(documents)
print(documents)

documents = collection.find({"appName": "b"})
documents = list(documents)
print(documents)
