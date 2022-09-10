import os
import sys
import time
import json
import uuid

from io import BytesIO

import uvicorn
from fastapi import FastAPI, Request, HTTPException, UploadFile, Depends
from fastapi import status as HTTPStatus
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, validator
from typing import Literal

from settings import app_settings, allowed_mimes
from tools import FileHandler, JobHandler

#-App Globals--------------------------------------------------


#-Models-------------------------------------------------------
class TestModel(BaseModel):
  message: str 
  timestamp: int | None = None

  @validator('message')
  def test_chk(cls, val):
    if len(val) < 5:
      raise ValueError('Invalid database object id')
    return val

#--------------
class VodModel(BaseModel):
  object_name: str
  media_name: str 
  media_description: str | None = None
  publisher: str | None = None
  id: uuid.UUID | None = uuid.uuid4()

  @validator("object_name")
  def check_object_name_in_list(cls, val):
    obj_name_list = FileHandler().get_list_of_object_names()
    if val not in obj_name_list:
      raise ValueError("object with name '%s' does not exist" %val)
    return val

#--------------

#--------------



#-Build and prep the App----------------------------------------
app = FastAPI()
app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_methods=["*"],
  allow_headers=["*"],
  allow_credentials=True
)


#-Initial Things-------------------------------------------------
@app.on_event("startup")
async def startup_event():
  inf = "Do startup things here"


#-The Routes----------------------------------------------------
@app.get("/", tags=["root"], response_model=TestModel)
async def api_root():
  data = {
    "message": "Hello from the API",
    "timestamp": int(time.time())
  }
  return data


#--------------------------------------------
@app.get("/media", tags=["transfer"])
async def get_media_list():
  file_handler = FileHandler()
  res = file_handler.get_list_of_objects()
  return res

#--------------------------------------------
@app.post("/media", tags=["transfer"])
async def upload_media_file(file: UploadFile):

  if file.content_type not in allowed_mimes:
    raise HTTPException(
      status_code=HTTPStatus.HTTP_400_BAD_REQUEST,
      detail="invalid file type. Please upload one of the following %s" %allowed_mimes
    )

  # content = await file.read()

  file_handler = FileHandler()
  await file_handler.upload_media_from_byte(file=file)

  return {"filename": file.filename}

#--------------------------------------------
@app.delete("/media/{filename}", tags=["transfer"])
async def delete_media_file(filename):
  file_handler = FileHandler()
  file_handler.delete_media_by_filename(filename=filename)

#--------------------------------------------
@app.get("/jobs", tags=["jobs"])
async def vod_job_get():

  job_handler = JobHandler()
  res = job_handler.get_queue_state()

  return res

#--------------------------------------------
@app.post("/job", tags=["jobs"])
async def vod_job_post(item:VodModel):

  job_handler = JobHandler()
  payload = json.dumps(dict(item), default=str)
  job_handler.send_job_to_queue(payload=payload)

  return item

#--------------------------------------------
@app.delete("/job/{delivery_tag}", tags=["jobs"])
async def vod_job_delete(delivery_tag:int):

  job_handler = JobHandler()
  job_handler.delete_job_in_queue(delivery_tag=delivery_tag)

  return {"delivery_tag": delivery_tag}

#--------------------------------------------
@app.delete("/queue/{queue_name}", tags=["jobs"])
async def vod_queue_delete(queue_name:str):

  job_handler = JobHandler()
  res = job_handler.delete_queue_by_name(queue_name=queue_name)

  return res

#--------------------------------------------


#--------------------------------------------



#-The Runner---------------------------------------------------------
if __name__ == "__main__":
  if "dev".lower() in sys.argv:
    print("Dev Mode")
    uvicorn.run(app="__main__:app", host="0.0.0.0", port=app_settings.app_port, debug=True, reload=True)
  else:
    print("Prod Mode")
    uvicorn.run(app="__main__:app", host="0.0.0.0", port=app_settings.app_port)