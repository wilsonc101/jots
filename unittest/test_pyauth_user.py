import pytest
import mongomock

from jots.pyauth import mongo, user, group


@pytest.fixture
def user_data():
  data = {"email_address": "a@b.com",
          "correct_password": "password",
          "incorrect_password": "notthepassword",
          "new_password": "password1",
          "service_domain": "dev.localhost"}
  return data


def test_user_operations(mongo_object, user_data):
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
      12) Chser find user returns matching user object
      13) Test setting a user attribute
      14) Delete user
  '''
  #1
  reset_code = user.create_user(service_domain=user_data['service_domain'],
                            email_address=user_data['email_address'],
                            db=mongo_object)
  assert isinstance(reset_code, str)

  #2
  user_object = user.user(email_address=user_data['email_address'],
                          db=mongo_object)
  assert isinstance(user_object, user.user)
  assert isinstance(user_object.properties.resetCode, str)
  assert user_object.properties.status == "new"
  assert len(user_object.properties.resetCode) > 100

  #3
  reset_result = user_object.set_password(user_data['correct_password'])
  assert reset_result
  assert user_object.properties.resetCode == ""
  assert user_object.properties.status == "active"

  #4
  auth_result_good = user_object.authenticate(user_data['correct_password'])
  assert auth_result_good

  #5
  auth_result_bad = user_object.authenticate(user_data['incorrect_password'])
  assert auth_result_bad is False

  #6
  new_reset_code = user_object.reset_password(service_domain=user_data['service_domain'])
  assert len(user_object.properties.resetCode) > 100
  assert user_object.properties.status == "reset"

  #7
  auth_result_reset = user_object.authenticate(user_data['correct_password'])
  assert auth_result_reset is False

  #8
  new_reset_result = user_object.set_password(user_data['new_password'])
  assert new_reset_result
  assert user_object.properties.resetCode == ""
  assert user_object.properties.status == "active"

  #9
  auth_result_first = user_object.authenticate(user_data['correct_password'])
  assert auth_result_first is False

  #10
  auth_result_new = user_object.authenticate(user_data['new_password'])
  assert auth_result_new

  #11
  with pytest.raises(user.UserPropertyError):
    user_object.properties.resetCode = "test"

  #12
  search_result = user.find_users_like(user_data['email_address'], db=mongo_object)
  assert isinstance(search_result, dict)
  assert search_result[user_data['email_address']] == user_object.properties.userId

  #13
  attr_result = user_object.update_named_attribute("status", "disabled")
  assert attr_result
  assert user_object.properties.status == "disabled"

  #14
  del_result = user.delete_user(user_object.properties.userId,
                                db=mongo_object)
  assert del_result
