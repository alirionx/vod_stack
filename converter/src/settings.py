#-YOU CAN CHANGE THINGS HERE---------------------
APP_PORT = 5000
MINIO_HOST = "localhost"
MINIO_PORT = 9000
MINIO_USER = "minio"
MINIO_PASSWORD = "VERYSECRET"
MINIO_TRANSFER_BUCKET = "vod-upload"
MINIO_STREAMING_BUCKET = "vod-streaming"
RABBITMQ_HOST = "localhost"
RABBITMQ_PORT = 5672
RABBITMQ_USER = "rabbitmq"
RABBITMQ_PASSWORD = "VERYSECRET"
RABBITMQ_JOB_QUEUE = "jobs"
RABBITMQ_STATUS_QUEUE = "status"
JOB_TEMP_DIR = "./tmp"

#------------------------------------------------
import os
from pydantic import BaseModel
from typing import Literal

class SettingsModel(BaseModel):
  app_port: int | None = APP_PORT
  minio_host: str | None = MINIO_HOST
  minio_port: int | None = MINIO_PORT
  minio_user: str | None = MINIO_USER
  minio_password: str | None = MINIO_PASSWORD
  minio_transfer_bucket: str | None = MINIO_TRANSFER_BUCKET
  minio_streaming_bucket: str | None = MINIO_STREAMING_BUCKET
  rabbitmq_host: str | None = RABBITMQ_HOST
  rabbitmq_port: int | None = RABBITMQ_PORT
  rabbitmq_user: str | None = RABBITMQ_USER
  rabbitmq_password: int | None = RABBITMQ_PASSWORD
  rabbitmq_job_queue: int | None = RABBITMQ_JOB_QUEUE
  rabbitmq_status_queue: int | None = RABBITMQ_STATUS_QUEUE
  job_temp_dir:str | None = JOB_TEMP_DIR

#------------------------------------------------
env_dict = {}
keys = list(SettingsModel.schema()["properties"].keys())
for key in keys:
  if os.environ.get(key.upper()):
    env_dict[key] = os.environ.get(key.upper())

app_settings = SettingsModel(**env_dict)

#------------------------------------------------