import pymongo
import json
import sys

client = pymongo.MongoClient()
db = client.pyauth
collection = db.groups


member_id = sys.argv[1]

documents = collection.find({"members": member_id})
documents = list(documents)

print(documents)
print("--------------------")
for i in documents:
  print(i["groupName"])

