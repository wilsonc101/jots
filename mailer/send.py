import os
import jinja2

import to_file

class Error(Exception):
  pass

class InputError(Error):
  def __init__(self, expression, message):
    self.expression = expression
    self.message = message

class MailActionError(Error):
  def __init__(self, expression, message):
    self.expression = expression
    self.message = message


class personalised_email(object):
  def __init__(self, recipient, template_name, data=None, template_path="templates/"):
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

    # Templates must exist, each with a handle
    available_templates = {"reset": "reset.tmpl"}

    _check_user_string(template_name)
    if template_name not in available_templates.keys():
      raise InputError("new email", "unknown template")
    self.template_filename = available_templates[template_name]

    _check_user_string(template_path)
    if not os.path.isfile("{}/{}".format(template_path, self.template_filename)):
      raise ("email", "template file does not exist")
    self.template_path = template_path

    for key in data.keys():
      _check_user_string(key)
      _check_user_string(data[key])
    self.data = data


  def _render_template(self):
    try:
        j2_env = jinja2.Environment(loader=jinja2.FileSystemLoader(self.template_path))
        template = j2_env.get_template(self.template_filename)
        return template.render(self.data)
    except jinja2.TemplateNotFound:
      raise MailActionError("render", "could not find template {}".format(self.template_filename))
    except jinja2.TemplateSyntaxError:
      raise MailActionError("render", "syntax error while rendering template {}".format(self.template_filename))
    except:
      raise MailActionError("render", "error rendering template {}".format(self.template_filename))


  def send(self, mail_agent="file"):
    available_agents = {"file": to_file.write_to_file}

    _check_user_string(mail_agent)
    if mail_agent not in available_agents.keys():
      raise MailActionError("send", "{} is not a valid mail agent".format(mail_agent))

    html_mail_body = self._render_template()

    try:
      result = available_agents[mail_agent](self.recipient, html_mail_body)
      return result
    except:
      raise MailActionError("send", "could not send email to {}".format(self.recipient))


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


if __name__ == "__main__":
  data = {"reset_url": "https://thing?reset=abs",
          "site_name": "https://thing"}
  email = personalised_email("chris.wilson@robotika.co.uk",
                             "reset",
                             data=data)
  print(email)
  print(email.recipient)
  print(email.send())
