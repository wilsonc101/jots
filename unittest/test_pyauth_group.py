import pytest
import mongomock
import uuid

from jots.pyauth import mongo, user, group


@pytest.fixture
def group_data():
  data = {"groupname": "testgroup"}
  return data

def test_group_management(mongo_object, example_user, group_data):
  ''' Test user registration workflow
      1) Create group and check a valid UUID is returned
      2) Get group by name returns a group object, it's ID is the same as previously created and member is present
      3) Get group by ID and check it's ID is the same as found by name
      4) Remove member and confirm user ID is not in members list (returned or in object)
      5) Add member and confirm user ID is in member list (returned and in object)
      6 & 7) Repeat of 4 & 5 using email rather than ID
      8 & 9) Get member details, whole document and specific attribute, confirm matches example user
      10) Check find returns matching group details
  '''
  # 1
  new_group_data = group.create_group(group_name=group_data['groupname'],
                                group_members=[example_user.properties.userId],
                                db=mongo_object)
  assert group_data['groupname'] in new_group_data
  group_id = new_group_data[group_data['groupname']]
  try:
    uuid.UUID(group_id)
  except ValueError:
    pytest.fail("group_id is not a valid UUID")

  #2
  group_object_by_name = group.group(group_name=group_data['groupname'],
                                     db=mongo_object)
  assert isinstance(group_object_by_name, group.group)
  assert group_object_by_name.properties.groupId == new_group_data[group_data['groupname']]
  assert example_user.properties.userId in group_object_by_name.properties.members

  #3
  group_object_by_id = group.group(group_id=group_id,
                                   db=mongo_object)
  assert isinstance(group_object_by_id, group.group)
  assert group_object_by_name.properties.groupId == group_object_by_id.properties.groupId

  #4
  removed_member_list = group_object_by_name.remove_member(user_id=example_user.properties.userId)
  assert example_user.properties.userId not in removed_member_list
  assert example_user.properties.userId not in group_object_by_name.properties.members

  #5
  added_member_list = group_object_by_name.add_member(user_id=example_user.properties.userId)
  assert example_user.properties.userId in added_member_list
  assert example_user.properties.userId in group_object_by_name.properties.members

  #6
  removed_member_list = group_object_by_name.remove_member(email=example_user.properties.email)
  assert example_user.properties.userId not in removed_member_list
  assert example_user.properties.userId not in group_object_by_name.properties.members

  #7
  added_member_list = group_object_by_name.add_member(email=example_user.properties.email)
  assert example_user.properties.userId in added_member_list
  assert example_user.properties.userId in group_object_by_name.properties.members

  #8
  member_details_all = group_object_by_name.get_members_detail()
  assert example_user.properties.userId in member_details_all
  assert member_details_all[example_user.properties.userId]['email'] == example_user.properties.email

  #9
  member_details_all = group_object_by_name.get_members_detail(attribute="email")
  assert example_user.properties.userId in member_details_all
  assert member_details_all[example_user.properties.userId] == example_user.properties.email

  #10
  search_result = group.find_groups_like(group_data['groupname'], db=mongo_object)
  assert isinstance(search_result, dict)
  assert search_result[group_data['groupname']] == group_object_by_name.properties.groupId

