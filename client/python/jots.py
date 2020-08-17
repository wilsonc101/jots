import requests

# Get config from env vars
# These should all be env vars
API_HOST = "http://dev.localhost"
API_PORT = 5000

APP_KEY = "09mea37ii8er2qlyhxo4ee66hhm34zsw"
APP_SECRET = "QQf7tGK1GTRT82Usz3vbwLYOSPh1ct8OsRY7rgOYI02jMFRS0GePSQlCTFwi1nCX"

class Error(Exception):
  pass

class ConnectionError(Error):
  def __init__(self, expression, message):
    self.expression = expression
    self.message = message


class Client(object):
  def connect(self, key=None, secret=None,
              api_host=None, api_port=None):

    # If not set as args, try getting from env vars
    if key is None:
      key = APP_KEY

    if secret is None:
      secret = APP_SECRET

    if api_host is None:
      self.api_host = API_HOST

    if api_port is None:
      self.api_port = API_PORT

    self.api_root = "{}:{}".format(self.api_host, self.api_port)
    api_login_url = "{}/token/new".format(self.api_root)

    # This should probably be in the mod init
    self.api_session = requests.Session()
    try:
      login_request = requests.get(api_login_url, auth=(key, secret))
      login_request.raise_for_status()
      access_token = login_request.text
      self.api_session.headers.update({"Authorization": "Bearer {}".format(access_token)})

    except requests.exceptions.HTTPError as err:
      raise ConnectionError("login request error", err)
    except requests.exceptions.ConnectionError as err:
      raise ConnectionError("login connection error", err)
    except requests.exceptions.Timeout:
      raise ConnectionError("login timeout", err)


  def _api_get(self, url):
    try:
      get_response = self.api_session.get(url)
      get_response.raise_for_status()
      return get_response

    except requests.exceptions.HTTPError as err:
      raise ConnectionError("api get request error", err)
    except requests.exceptions.ConnectionError as err:
      raise ConnectionError("api get connection error", err)
    except requests.exceptions.Timeout:
      raise ConnectionError("api get timeout", err)


  def _api_post(self, url, json_data=None, string_data=None):
    if json_data is not None:
      try:
        post_response = self.api_session.post(url, json=json_data)
        post_response.raise_for_status()
        return post_response

      except requests.exceptions.HTTPError as err:
        raise ConnectionError("api put request error", err)
      except requests.exceptions.ConnectionError as err:
        raise ConnectionError("api put connection error", err)
      except requests.exceptions.Timeout:
        raise ConnectionError("api put timeout", err)

    elif string_data is not None:
      pass

    else:
      print("this is bad, raise an error")


  def find_users_by_email(self, query):
    url = "{}/api/v1/users/find".format(self.api_root)
    query_data = {"email": query}
    response = self._api_post(url, json_data=query_data)
    return response.json()


  def get_user_details(self, userId):
    url = "{}/api/v1/users/{}/details".format(self.api_root, userId)
    response = self._api_get(url)
    return response.json()


  def get_user_groups(self, userId):
    url = "{}/api/v1/groups/find".format(self.api_root)
    query_data = {"userid": userId}
    response = self._api_post(url, json_data=query_data)
    return response.json()



if __name__ == "__main__":
  client = Client()
  client.connect()

  user_id = "66c32b98-b057-491c-979d-9032a5d200b8"
  print(client.get_user_details(user_id))

  print("----------------------------")
  query = "?@?.?"
  print(client.find_users_by_email(query))

  print("----------------------------")
  print(client.get_user_groups(user_id))




