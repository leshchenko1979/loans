FROM python:slim

LABEL Name=loans Version=0.0.1

# RUN pip install -U --no-cache wheel setuptools pip

ADD /requirements.txt /

RUN pip install -r requirements.txt --no-cache

ADD /.env /
ADD /flask_app.py /

EXPOSE 5000:8080

ENV FLASK_APP=flask_app.py

CMD ["flask", "run", "--host", "0.0.0.0", "--port", "8080"]
