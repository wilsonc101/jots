import pymongo
client = pymongo.MongoClient()
db = client.pyauth

col_u = db.users
col_u.drop()

col_g = db.groups
col_g.drop()

col_u = db.users
col_u.create_index("email", unique=True)

col_g = db.groups
col_g.create_index("groupName", unique=True)

