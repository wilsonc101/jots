import pytest
import mongomock

from flask_jwt_extended import (create_refresh_token, create_access_token)

import jots.webapp
from jots.pyauth import mongo, user, group


@pytest.fixture(scope="function")
@mongomock.patch(servers=(('dev.localhost', 27017),))
def mongo_object():
  db = mongo.mongo(mongo_host='dev.localhost', mongo_port=27017)

  def fin():
    db.clear_collections()

  return db


@pytest.fixture(scope="function")
def registered_user_data():
  data = {"email_address": "a@b.com",
          "password": "password",
          "service_domain": "dev.localhost"}
  return data


@pytest.fixture(scope="function")
def registered_user(mongo_object, registered_user_data):
  ''' Create a user object that is registered but not active
  '''
  reset_code = user.create_user(service_domain=registered_user_data['service_domain'],
                                email_address=registered_user_data['email_address'],
                                db=mongo_object)

  user_object = user.user(email_address=registered_user_data['email_address'],
                          db=mongo_object)

  yield user_object
  mongo_object.clear_collections()



@pytest.fixture(scope="function")
def example_user_data():
  data = {"email_address": "c@d.com",
          "password": "password",
          "bad_password": "notthepassword",
          "service_domain": "dev.localhost"}
  return data


@pytest.fixture(scope="function")
def example_user(mongo_object, example_user_data):
  ''' Create a demo user object that may be added to groups
  '''
  reset_code = user.create_user(service_domain=example_user_data['service_domain'],
                                email_address=example_user_data['email_address'],
                                db=mongo_object)

  user_object = user.user(email_address=example_user_data['email_address'],
                          db=mongo_object)

  reset_result = user_object.set_password(example_user_data['password'])

  yield user_object
  mongo_object.clear_collections()


@pytest.fixture(scope="function")
def example_group_data():
  data = {"groupname": "admin"}
  return data


@pytest.fixture(scope="function")
def example_group(mongo_object, example_group_data, example_user):
  group_id = group.create_group(group_name=example_group_data['groupname'],
                                group_members=[example_user.properties.userId],
                                db=mongo_object)

  group_object = group.group(group_name=example_group_data['groupname'],
                             db=mongo_object)

  yield group_object
  mongo_object.clear_collections()


@pytest.fixture(scope="function")
def client(mongo_object):
  with jots.webapp.app.test_client() as client:
    jots.webapp.app.config['TESTING'] = True
    jots.webapp.app.config['TEST_DB'] = mongo_object

    jots.webapp.app.config['DOMAIN_NAME'] = "dev.localhost"
    jots.webapp.app.config['JWT_SECRET_KEY'] = "password"
    jots.webapp.app.config['JWT_COOKIE_DOMAIN'] = "dev.localhost"

    yield client

