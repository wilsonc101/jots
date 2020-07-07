FROM python:3.8

ADD jots.tar jots
RUN ["mv", "jots/runserv.py", "."]
RUN ["mv", "jots/requirements.txt", "."]
RUN ["pip", "install", "-r", "requirements.txt"]

ENTRYPOINT ["python", "runserv.py"]
EXPOSE 5000/tcp
