import pymongo
import json

client = pymongo.MongoClient()
db = client.pyauth
collection = db.users

doc = collection.find_one_and_update({"email": "chris.wilson@robotika.co.uk"},
                                      {"$set": {"refreshJti": "notcorrect"}},
                                       upsert=False,
                                       return_document=pymongo.collection.ReturnDocument.AFTER)
doc = list(doc)
print(doc)
