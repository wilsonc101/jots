db.createCollection("users")
db.createCollection("groups")
db.createCollection("apps")

db.users.createIndex({"email": 1}, {unique: true})
db.groups.createIndex({"groupName": 1}, {unique: true})
db.apps.createIndex({"appName": 1}, {unique: true})

db.groups.insert({groupName: "admin", groupId: UUID(), members: []})
