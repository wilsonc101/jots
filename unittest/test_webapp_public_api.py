import pytest
import mongomock

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



