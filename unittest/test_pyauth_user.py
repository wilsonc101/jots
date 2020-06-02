import pytest
import mongomock

from jots.pyauth import mongo, user, group


@pytest.fixture
@mongomock.patch(servers=(('dev.localhost', 27017),))
def mongo_object():
  db = mongo.mongo(mongo_host='dev.localhost', mongo_port=27017)
  return db


@pytest.fixture
def user_data():
  data = {"email_address": "a@b.com",
          "correct_password": "password",
          "incorrect_password": "notthepassword",
          "new_password": "password1",
          "service_domain": "dev.localhost"}
  return data


def test_user_registration(mongo_object, user_data):
  ''' Test user registration workflow
      1) Create user object
      2) Check user object can be retrieved and properties are as expected
      3) Reset user password and confirm sensitive fields are blanked
      4 & 5) Check authentication mechanism
      6) Check resetting password results in a long reset code
      7) Check that previous password no longer works
      8) Check that setting new password clears sensitive fields
      9 & 10) Check that old password is invalid and new one works
      11) Check user properties are read-only (raise exception on set)
  '''
  reset_code = user.create_user(service_domain=user_data['service_domain'],
                            email_address=user_data['email_address'],
                            db=mongo_object)
  assert isinstance(reset_code, str)

  user_object = user.user(email_address=user_data['email_address'],
                          db=mongo_object)
  assert isinstance(user_object, user.user)
  assert isinstance(user_object.properties.resetCode, str)
  assert user_object.properties.status == "new"
  assert len(user_object.properties.resetCode) > 100

  reset_result = user_object.set_password(user_data['correct_password'])
  assert reset_result
  assert user_object.properties.resetCode == ""
  assert user_object.properties.status == "active"

  auth_result_good = user_object.authenticate(user_data['correct_password'])
  assert auth_result_good

  auth_result_bad = user_object.authenticate(user_data['incorrect_password'])
  assert auth_result_bad is False

  new_reset_code = user_object.reset_password(service_domain=user_data['service_domain'])
  assert len(user_object.properties.resetCode) > 100
  assert user_object.properties.status == "reset"

  auth_result_reset = user_object.authenticate(user_data['correct_password'])
  assert auth_result_reset is False

  new_reset_result = user_object.set_password(user_data['new_password'])
  assert new_reset_result
  assert user_object.properties.resetCode == ""
  assert user_object.properties.status == "active"


  auth_result_first = user_object.authenticate(user_data['correct_password'])
  assert auth_result_first is False

  auth_result_new = user_object.authenticate(user_data['new_password'])
  assert auth_result_new

  with pytest.raises(user.UserPropertyError):
    user_object.properties.resetCode = "test"

  search_result = user.find_users_like(user_data['email_address'], db=mongo_object)
  assert isinstance(search_result, dict)
  assert search_result[user_data['email_address']] == user_object.properties.userId
