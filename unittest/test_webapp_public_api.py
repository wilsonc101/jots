import pytest
import mongomock

from flask_jwt_extended import (create_refresh_token, create_access_token)

import jots.webapp
from jots.pyauth import mongo, user, group


@pytest.fixture
@mongomock.patch(servers=(('dev.localhost', 27017),))
def mongo_object():
  db = mongo.mongo(mongo_host='dev.localhost', mongo_port=27017)
  return db


@pytest.fixture
def registered_user_data():
  data = {"email_address": "a@b.com",
          "password": "password",
          "service_domain": "dev.localhost"}
  return data


@pytest.fixture
def registered_user(mongo_object, registered_user_data):
  ''' Create a user object that is registered but not active
  '''
  reset_code = user.create_user(service_domain=registered_user_data['service_domain'],
                                email_address=registered_user_data['email_address'],
                                db=mongo_object)

  user_object = user.user(email_address=registered_user_data['email_address'],
                          db=mongo_object)
  return user_object


@pytest.fixture
def example_user_data():
  data = {"email_address": "c@d.com",
          "password": "password",
          "bad_password": "notthepassword",
          "service_domain": "dev.localhost"}
  return data


@pytest.fixture
def example_user(mongo_object, example_user_data):
  ''' Create a demo user object that may be added to groups
  '''
  reset_code = user.create_user(service_domain=example_user_data['service_domain'],
                                email_address=example_user_data['email_address'],
                                db=mongo_object)

  user_object = user.user(email_address=example_user_data['email_address'],
                          db=mongo_object)

  reset_result = user_object.set_password(example_user_data['password'])
  return user_object


@pytest.fixture
def client(mongo_object):
  with jots.webapp.app.test_client() as client:
    jots.webapp.app.config['TESTING'] = True
    jots.webapp.app.config['TEST_DB'] = mongo_object

    jots.webapp.app.config['DOMAIN_NAME'] = "dev.localhost"
    jots.webapp.app.config['JWT_SECRET_KEY'] = "password"
    jots.webapp.app.config['JWT_COOKIE_DOMAIN'] = "dev.localhost"

    yield client


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



