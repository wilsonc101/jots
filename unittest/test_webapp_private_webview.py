import pytest
import mongomock

from flask_jwt_extended import (create_refresh_token, create_access_token)

import jots.webapp
from jots.pyauth import mongo, user, group


def test_get_protected_page(client, example_user, example_user_data):
  ''' Access a restricted page
  '''
  with client.application.app_context():
    access_token = create_access_token(example_user.properties.email)

  client.set_cookie(example_user_data['service_domain'], "access_token_cookie", access_token)
  result = client.get("/page",
                      follow_redirects=True)

  assert result.status_code < 400
  assert b"This is a protected page" in result.data


def test_get_protected_privileged_page(client, example_user, example_user_data, example_group):
  ''' Access a restricted page
      1) Check that a member of the admin group can access the user admin page
      2) Remove user from admin group and confim access is denied
  '''
  with client.application.app_context():
    access_token = create_access_token(example_user.properties.email)

  client.set_cookie(example_user_data['service_domain'], "access_token_cookie", access_token)
  result = client.get("/admin/users",
                      follow_redirects=True)
  assert result.status_code < 400
  assert b"Admin - User Management" in result.data

  removed_member_list = example_group.remove_member(user_id=example_user.properties.userId)
  result = client.get("/admin/users",
                      follow_redirects=True)
  assert result.status_code == 403




