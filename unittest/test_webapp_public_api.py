import pytest
import mongomock
import base64

from flask_jwt_extended import (create_refresh_token, create_access_token)

import jots.webapp
from jots.pyauth import mongo, user, group


def test_post_reset_data(client, registered_user, registered_user_data):
  ''' Post reset form details
  '''
  post_data = {"username": registered_user_data['email_address'],
               "password": registered_user_data['password'],
               "resetcode": registered_user.properties.resetCode}

  result = client.post("/reset",
                       data=post_data,
                       follow_redirects=True)

  assert b'Login' in result.data


def test_post_login_data(client, example_user, example_user_data):
  ''' Post login form data
  '''
  post_data = {"username": example_user_data['email_address'],
               "password": example_user_data['password']}

  result = client.post("/login",
                       data=post_data)

  assert result.status_code < 400


  post_data = {"username": example_user_data['email_address'],
               "password": example_user_data['bad_password']}

  result = client.post("/login",
                       data=post_data)

  assert result.status_code == 403


def test_get_app_token(client, example_app, example_user):
  ''' Test app authentication
      1) Create b64 auth header, use to generate token
      2) Use token to access protected api endpoint
  '''
  key = example_app['newappZ']['key']
  secret = example_app['newappZ']['secret']
  id = example_app['newappZ']['id']

  #1
  b64_auth = base64.urlsafe_b64encode("{}:{}".format(key, secret).encode('utf-8')).decode('utf-8')
  headers = {'Authorization': "Basic {}".format(b64_auth)}
  result = client.get("/token/new",
                      headers=headers)

  assert result.status_code == 200
  access_token = result.data.decode('utf-8')

  headers = {'Authorization': "Bearer {}".format(access_token)}
  result = client.get("/api/v1/users/{}/details".format(example_user.properties.userId),
                      headers=headers)

  assert result.status_code == 200
  assert result.json['email'] == example_user.properties.email
