import pymongo
import json
import re

regex = re.compile('.*admin.*', re.IGNORECASE)

client = pymongo.MongoClient()
db = client.pyauth
collection = db.groups

documents = collection.find({"groupName": regex})
documents = list(documents)

print(documents)
