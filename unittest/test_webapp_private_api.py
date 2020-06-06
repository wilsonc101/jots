import pytest
import mongomock
import json

from flask_jwt_extended import (create_refresh_token, create_access_token, get_csrf_token)

import jots.webapp
from jots.pyauth import mongo, user, group


def test_get_protected_endpoint(client, example_user, example_user_data, example_group):
  ''' Access a restricted page
      1) Get base API response
      2) Get group members, confirm example user is present in result
  '''
  with client.application.app_context():
    access_token = create_access_token(example_user.properties.email)

  client.set_cookie(example_user_data['service_domain'], "access_token_cookie", access_token)

  #1
  result = client.get("/api")

  assert result.status_code == 200
  assert result.json['version'] == 'v1'

  #2
  result = client.get("/api/v1/groups/{}/members".format(example_group.properties.groupId))

  assert result.status_code == 200
  assert example_user.properties.userId in result.json


def test_post_protected_endpoint(client, example_user, example_user_data, registered_user, example_group):
  ''' Access a restricted API endpoint using CSRF token signature
      1) Post groupname and confirm found group matches fixtures
      2) Add group member
      3) Remove group member
      4) Find user and confirm matching content
      5) Create and delete a new group
      6) Delete user
  '''
  with client.application.app_context():
    access_token = create_access_token(example_user.properties.email)
    csrf_code = get_csrf_token(access_token)

  client.set_cookie(example_user_data['service_domain'], "access_token_cookie", access_token)

  headers = {"Content-Type": "application/json",
             "X-CSRF-TOKEN": csrf_code}

  #1
  post_data = {"groupname": example_group.properties.groupName}
  result = client.post("/api/v1/groups/find",
                       data=json.dumps(post_data),
                       headers=headers,
                       follow_redirects=True)

  assert result.status_code == 200
  assert example_group.properties.groupName in result.json
  assert example_group.properties.groupId in result.json[example_group.properties.groupName]

  #2
  post_data = {"email": registered_user.properties.email}
  result = client.post("/api/v1/groups/{}/members/add".format(example_group.properties.groupId),
                       data=json.dumps(post_data),
                       headers=headers,
                       follow_redirects=True)

  assert result.status_code == 200
  assert registered_user.properties.userId in result.json

  #3
  post_data = {"userid": registered_user.properties.userId}
  result = client.post("/api/v1/groups/{}/members/remove".format(example_group.properties.groupId),
                       data=json.dumps(post_data),
                       headers=headers,
                       follow_redirects=True)

  assert result.status_code == 200
  assert registered_user.properties.userId not in result.json

  #4
  post_data = {"email": example_user.properties.email}
  result = client.post("/api/v1/users/find",
                       data=json.dumps(post_data),
                       headers=headers,
                       follow_redirects=True)

  assert result.status_code == 200
  assert example_user.properties.email in result.json

  #5
  post_data = {"groupname": "newgroupA"}
  result = client.post("/api/v1/groups/new",
                       data=json.dumps(post_data),
                       headers=headers,
                       follow_redirects=True)

  assert result.status_code == 200
  assert post_data['groupname'] in result.json
  new_group_id = result.json[post_data['groupname']]

  post_data = {"groupid": new_group_id}
  result = client.post("/api/v1/groups/delete",
                       data=json.dumps(post_data),
                       headers=headers,
                       follow_redirects=True)

  assert result.status_code == 200
  assert "result" in result.json

  #6
  post_data = {"userid": example_user.properties.userId}
  result = client.post("/api/v1/users/delete",
                       data=json.dumps(post_data),
                       headers=headers,
                       follow_redirects=True)

  assert result.status_code == 200
  assert "result" in result.json

