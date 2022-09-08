#-YOU CAN CHANGE THINGS HERE---------------------
APP_PORT = 5000
MINIO_HOST = "localhost"
MINIO_PORT = 9000
RABBITMQ_HOST = "localhost"
RABBITMQ_PORT = 5672

#------------------------------------------------
import os
from pydantic import BaseModel

class SettingsModel(BaseModel):
  app_port: int | None = APP_PORT
  minio_host: str | None = MINIO_HOST
  minio_port: int | None = MINIO_PORT
  rabbitmq_host: str | None = RABBITMQ_HOST
  rabbitmq_port: int | None = RABBITMQ_PORT

#------------------------------------------------
env_dict = {}
keys = list(SettingsModel.schema()["properties"].keys())
for key in keys:
  if os.environ.get(key.upper()):
    env_dict[key] = os.environ.get(key.upper())

AppSettings = SettingsModel(**env_dict)

#------------------------------------------------
