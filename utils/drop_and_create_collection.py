import pymongo
import uuid

client = pymongo.MongoClient()
db = client.pyauth

col_u = db.users
col_u.drop()

col_g = db.groups
col_g.drop()

col_a = db.apps
col_a.drop()

col_a = db.apps

col_u = db.users
col_u.create_index("email", unique=True)

col_g = db.groups
col_g.create_index("groupName", unique=True)

admin_group = {"groupName": "admin",
               "groupId": str(uuid.uuid4()),
               "members": []}

doc_id = col_g.insert_one(admin_group).inserted_id

