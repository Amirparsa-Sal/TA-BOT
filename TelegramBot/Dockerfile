FROM python:3.8-slim

WORKDIR /app

RUN apt-get update
RUN apt-get install -y python3 python3-pip python-dev build-essential python3-venv

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3",  "-u", "bot.py"]