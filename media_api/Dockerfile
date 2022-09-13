FROM python:3.10

COPY ./requirements.txt /opt/requirements.txt
RUN pip install -r /opt/requirements.txt

COPY ./src /app

WORKDIR /app
EXPOSE 5000

CMD ["python", "-u", "app.py"]