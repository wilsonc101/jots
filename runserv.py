import argparse
from jots.webapp import app

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("-p", "--port", type=int, help="port to bind with flask")
  args = parser.parse_args()

  if args.port < 1023:
    raise ValueError("port", "port must be in unprivileged range")

  app.config["SERVER_PORT"] = args.port
  app.run(host='0.0.0.0',
          port=args.port,
          debug=True,
          ssl_context='adhoc')
