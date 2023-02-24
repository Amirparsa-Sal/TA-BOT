FROM python:3.8-slim

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt && \
    mkdir db

COPY . .