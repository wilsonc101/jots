import datetime

def write_to_file(recipient, mail_body):
  date_now = datetime.datetime.now()
  date_now_str = date_now.strftime("%d%m%YT_%H%M%S")

  with open("{}_{}.html".format(date_now_str, recipient), "w") as email_file:
    email_file.write(mail_body)

  return True

