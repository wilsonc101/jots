import os


class Error(Exception):
  pass

class InputError(Error):
  def __init__(self, expression, message):
    self.expression = expression
    self.message = message


class unique_email(object):
  def __init__(self, recipient, template_name, data=None, template_path="templates")
    if recipient is None:
      raise InputError("new email", "recipient not given")
    if not isinstance(recipient, str):
      raise InputError("new email", "recipient must be str")

    if template_name is None:
      raise InputError("new email", "template name not given")
    if not isinstance(template_name, str):
      raise InputError("new email", "template name must be str")

    if data is not None and not isinstance(data, dict):
        raise InputError("new email", "email data must be dict")

    _check_user_string(recipient)
    _check_email(recipient)
    self.recipient = recipient

    _check_user_string(template_name)
    if not os.path.isfile("{}/{}".format(template_path, template_name))
      raise ("email", "template does not exist")
    self.template_path = "{}/{}".format(template_path, template_name)

    for key in data.keys()
      _check_user_string(key)
      _check_user_string(data[key])
    self.data = data

  def _render_template(self):
    #Use jinja to make HTML content
    pass

  def send(self, mail_agent=None):
    # pass template and other data to mail agent
    pass


def _check_user_string(user_string):
  illegal_chars = ["$", ";", ","]
  for char in user_string:
    if char in illegal_chars:
      raise InputError("check", "bad string")

  return True


def _check_email(email_address):
  if "@" not in email_address or "." not in email_address:
    raise InputError("check_email", "invalid email address")
    # if email contains illegal chars, raise error

  return True

