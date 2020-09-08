import pymongo
import json

client = pymongo.MongoClient(username="pyauthadmin", password="password")

db = client.pyauth
collection = db.groups

groupid="7e3548cc-e0d1-4931-9f1b-f1a5402dd1a5"

documents = collection.find({"groupName": "admin"})
#documents = collection.find({"groupId": groupid})
documents = list(documents)

print(documents)
