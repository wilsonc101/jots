import pymongo
import json

client = pymongo.MongoClient()
db = client.pyauth
collection = db.users

documents = collection.find({"email": "chris.wilson@robotika.co.uk"})
#documents = collection.find({"email": "a@b.com"})
documents = list(documents)

print(documents)
