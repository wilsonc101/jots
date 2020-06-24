import pytest
import mongomock

from jots.pyauth import mongo, user, group, app


@pytest.fixture
def app_data():
  data = {"app_name": "test"}
  return data


def test_app_operations(mongo_object, app_data):
  ''' Test app workflow
      1) Create app
      2) Get app by name, key and id, confirm all are equal
      3) Test authentication
      4) Test search
      5) Test app delete
  '''
  #1
  app_id, app_key, app_secret = app.create_app(name=app_data['app_name'],
                                db=mongo_object)
  assert isinstance(app_id, str)

  #2
  app_object_by_name = app.app(app_name=app_data['app_name'],
                               db=mongo_object)
  assert isinstance(app_object_by_name, app.app)

  app_object_by_key = app.app(app_key=app_key,
                              db=mongo_object)
  assert isinstance(app_object_by_key, app.app)

  app_object_by_id = app.app(app_id=app_id,
                             db=mongo_object)
  assert isinstance(app_object_by_id, app.app)
  assert app_object_by_name.properties.appId == app_object_by_key.properties.appId == app_object_by_id.properties.appId

  #3
  auth_result = app_object_by_id.authenticate(app_secret)
  assert auth_result

  #4
  search_result = app.find_apps_like(app_data['app_name'], db=mongo_object)
  assert isinstance(search_result, dict)
  assert search_result[app_data['app_name']] == app_object_by_id.properties.appId

  #5
  del_result = app.delete_app(app_object_by_id.properties.appId,
                              db=mongo_object)
  assert del_result
