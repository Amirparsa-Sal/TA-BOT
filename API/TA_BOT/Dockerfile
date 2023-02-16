FROM python:3.12.0a5-alpine3.17

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt && \
    mkdir db

COPY . .