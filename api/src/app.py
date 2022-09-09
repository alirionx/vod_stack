import os
import sys
import time
import json

from io import BytesIO

import uvicorn
from fastapi import FastAPI, Request, HTTPException, UploadFile, Depends
from fastapi import status as HTTPStatus
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, validator, EmailStr

from settings import app_settings, allowed_mimes
from tools import FileHandler

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



#--------------------------------------------



#-The Runner---------------------------------------------------------
if __name__ == "__main__":
  if "dev".lower() in sys.argv:
    print("Dev Mode")
    uvicorn.run(app="__main__:app", host="0.0.0.0", port=app_settings.app_port, debug=True, reload=True)
  else:
    print("Prod Mode")
    uvicorn.run(app="__main__:app", host="0.0.0.0", port=app_settings.app_port)