import pytest
import mongomock

from jots.pyauth import mongo, user, group


#@pytest.fixture
#def user_data():
#  data = {"email_address": "a@b.com",
#          "service_domain": "dev.localhost",
#          "password": "password"}
#  return data


#@pytest.fixture
#def registered_user(mongo_object, user_data):
#  ''' Create a user object that is registered but not active
#  '''
#  reset_code = user.create_user(service_domain=user_data['service_domain'],
#                                email_address=user_data['email_address'],
#                                db=mongo_object)
#
#  user_object = user.user(email_address=user_data['email_address'],
#                          db=mongo_object)
#  return user_object


#@pytest.fixture
#def client(mongo_object):
#  with jots.webapp.app.test_client() as client:
#    jots.webapp.app.config['TESTING'] = True
#    jots.webapp.app.config['TEST_DB'] = mongo_object
#
#    jots.webapp.app.config['DOMAIN_NAME'] = "dev.localhost"
#    jots.webapp.app.config['JWT_SECRET_KEY'] = "password"
#    jots.webapp.app.config['JWT_COOKIE_DOMAIN'] = "dev.localhost"
#
#    yield client


def test_get_login_form(client, monkeypatch):
  ''' Get login page for unauthenticated user
  '''
  import jots.webapp
  result = client.get("/")
  assert b'Login' in result.data


def test_get_reset_form(client, registered_user, monkeypatch):
  import jots.webapp

  result = client.get("/reset")
  assert b'missing query string' in result.data

  result = client.get("/reset?z={}".format(registered_user.properties.resetCode))
  assert b'malformed query' in result.data

  result = client.get("/reset?q={}".format(registered_user.properties.resetCode))
  assert b'Reset' in result.data


