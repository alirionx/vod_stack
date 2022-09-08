import os
import sys
import time
import json

from io import BytesIO

from fastapi import FastAPI, Request, HTTPException, UploadFile, Depends
from fastapi import status as HTTPStatus
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, validator, EmailStr


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


#--------------------------------------------


#--------------------------------------------



#--------------------------------------------



#-The Runner---------------------------------------------------------
if __name__ == "__main__":
  if "dev".lower() in sys.argv:
    print("Dev Mode")
    uvicorn.run(app="__main__:app", host="0.0.0.0", port=conf_settings.settings_API_Port, debug=True, reload=True)
  else:
    print("Prod Mode")
    # import webbrowser
    # webbrowser.open("http://localhost:%s" %conf_settings.API_PORT)
    uvicorn.run(app="__main__:app", host="0.0.0.0", port=conf_settings.settings_API_Port)