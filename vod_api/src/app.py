import s3fs
import os
import sys
import time
import json
import uuid

from io import BytesIO

import uvicorn
from fastapi import FastAPI, Request, HTTPException, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi import status as HTTPStatus
from fastapi.responses import StreamingResponse

# from fastapi.staticfiles import StaticFiles
# from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, validator

from settings import app_settings
from tools import StreamServ

#-App Globals--------------------------------------------------
stream_serve = StreamServ()

#-Models-------------------------------------------------------
class TestModel(BaseModel):
  test: str | None = None



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


#--------------------------------------------
@app.get("/stream/{id}/{filename}", tags=["stream"])
async def stream_file_get(id:uuid.UUID, filename:str):
  
  object_path = str(id) + "/" + filename
  # stream_serve = StreamServ()
  
  chk_res = stream_serve.check_object_exist(object_path)
  if not chk_res:
    raise HTTPException(
      status_code=HTTPStatus.HTTP_404_NOT_FOUND,
      detail="file '%s' not found in bucket '%s'" %(id, filename))

  res = stream_serve.get_object_as_bytes(object_name=object_path)
  content_type = res.headers['Content-Type']
  data = res.read()
  
  # return {"id": id, "filename":filename}
  return StreamingResponse(BytesIO(data), media_type=content_type)
  



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