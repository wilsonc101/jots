FROM python:3.8

ADD jots.tar jots
RUN ["mv", "jots/runserv.py", "."]
RUN ["mv", "jots/requirements.txt", "."]
RUN ["pip", "install", "-r", "requirements.txt"]

ENTRYPOINT ["python", "runserv.py", "-p", "5000"]
EXPOSE 5000/tcp
