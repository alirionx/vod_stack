#-YOU CAN CHANGE THINGS HERE---------------------
APP_PORT = 5001
MINIO_HOST = "localhost"
MINIO_PORT = 9000
MINIO_USER = "minio"
MINIO_PASSWORD = "VERYSECRET"
MINIO_TRANSFER_BUCKET = "vod-upload"
MINIO_STREAMING_BUCKET = "vod-streaming"

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

#------------------------------------------------
env_dict = {}
keys = list(SettingsModel.schema()["properties"].keys())
for key in keys:
  if os.environ.get(key.upper()):
    env_dict[key] = os.environ.get(key.upper())

app_settings = SettingsModel(**env_dict)

#------------------------------------------------