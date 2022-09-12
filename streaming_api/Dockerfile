FROM python:3.10

RUN apt update && apt install -y ffmpeg 

COPY ./src /app
RUN pip install -r /app/requirements.txt

WORKDIR /app
EXPOSE 5000

CMD ["python", "-u", "app.py"]