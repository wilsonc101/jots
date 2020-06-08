import pytest

from jots.mailer import send

@pytest.fixture
def user_data():
  data = {"email_address": "test@dev.local",
          "template": "reset",
          "data": {"site_name": "dev.local",
                   "reset_url": "https://dev.local/reset?q=theresetcode"}}
  return data

def test_mailer(user_data):
  email_obj = send.personalised_email(recipient=user_data['email_address'],
                                      template_name=user_data['template'],
                                      data=user_data['data'])
  assert isinstance(email_obj, send.personalised_email)
  assert email_obj.recipient == user_data['email_address']

  result = email_obj.send(mail_agent="string")
  assert "theresetcode" in result
  assert user_data['data']['site_name'] in result

