FROM python:3.10

COPY ./requirements.txt /opt/requirements.txt
RUN pip install -r /opt/requirements.txt

COPY ./src /app

WORKDIR /app

CMD ["python", "-u", "app.py"]