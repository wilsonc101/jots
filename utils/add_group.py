import pymongo
import uuid
import sys

client = pymongo.MongoClient()
db = client.pyauth
col_g = db.groups

new_group = {"groupName": str(sys.argv[1]),
               "groupId": str(uuid.uuid4()),
               "members": []}

doc_id = col_g.insert_one(new_group).inserted_id

