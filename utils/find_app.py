import pymongo
import json


client = pymongo.MongoClient(username="pyauthadmin", password="password")
db = client.pyauth
collection = db.apps

documents = collection.find({"appName": "testR"})
documents = list(documents)
print(documents)

documents = collection.find({"appName": "testRW"})
documents = list(documents)
print(documents)

