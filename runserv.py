import jots.webapp.app as app

if __name__ == "__main__":
  app.run(host='0.0.0.0',
          port="5000",
          debug=True,
          ssl_context='adhoc')
