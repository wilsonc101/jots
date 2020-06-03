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


def test_get_protected_page(client, example_user, example_user_data):
  ''' Post reset form details
  '''

  with client.application.app_context():
    access_token = create_access_token(example_user.properties.email)

  client.set_cookie(example_user_data['service_domain'], "access_token_cookie", access_token)
  result = client.get("/page",
                      follow_redirects=True)

  assert result.status_code < 400
  assert b"This is a protected page" in result.data


