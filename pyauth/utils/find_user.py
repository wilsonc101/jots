import pymongo
import json

client = pymongo.MongoClient()
db = client.pyauth
collection = db.users

documents = collection.find({"email": "chris.wilson@robotika.co.uk"})
documents = list(documents)

print(documents)
