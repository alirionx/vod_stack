FROM ubuntu:jammy

RUN apt update && apt install -y ffmpeg python3 python3-pip

COPY ./requirements.txt /opt/requirements.txt
RUN pip install -r /opt/requirements.txt

COPY ./src /app

WORKDIR /app

CMD ["python3", "-u", "app.py"]