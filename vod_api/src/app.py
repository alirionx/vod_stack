import os
import sys
import time
import json
import uuid
from threading import Thread

from io import BytesIO

import uvicorn
from fastapi import FastAPI, Request, HTTPException, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi import status as HTTPStatus
from fastapi.responses import StreamingResponse, FileResponse 

# from fastapi.staticfiles import StaticFiles
# from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pydantic import BaseModel, validator

from settings import app_settings
from tools import StreamMgmt #, StreamServ

#-App Globals--------------------------------------------------
# stream_serve = StreamServ()
# stream_mgmt = StreamMgmt()

#-Models-------------------------------------------------------
class StreamingsModel(BaseModel):
  object_name: str 
  media_name: str 
  media_description: str | None = None
  publisher: str | None = None
  id: uuid.UUID | None = None
  tmdb: int | None = None



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
@app.get("/", tags=["root"])
async def api_root():
  data = {
    "message": "Hello from the VOD_API",
    "timestamp": int(time.time())
  }
  return data

#--------------------------------------------
@app.get("/streamings", tags=["streamings"] )
async def api_streamings_get():
  #-----------
  try:
    stream_mgmt = StreamMgmt()
  except Exception as e:
    raise HTTPException(
      status_code=HTTPStatus.HTTP_500_INTERNAL_SERVER_ERROR,
      detail="Something went wrong: '%s' not found" %e
    )

  #-----------
  stream_mgmt.sync_bucket_with_db()
  stream_mgmt.get_docs_from_db()

  #-----------
  res = []
  for item in stream_mgmt.docs_list:
    new_item = item.copy()
    new_item["streaming_url"] = "%s/%s/%s/stream.mpd" %(
      app_settings.s3_streaming_endpoint,
      app_settings.minio_streaming_bucket,
      item["id"]
    )
    res.append(new_item)

  return res

#--------------------------------------------
@app.get("/streamings/{id}", tags=["streamings"], response_model=StreamingsModel)
async def api_streaming_get(id:uuid.UUID):
  stream_mgmt = StreamMgmt()
  if str(id) not in stream_mgmt.couchdb_cli:
    raise HTTPException(
      status_code=HTTPStatus.HTTP_404_NOT_FOUND,
      detail="Streaminf Doc with id '%s' not found" %id
    )

  res = stream_mgmt.get_doc_by_id(id=str(id))
  return res

#--------------------------------------------
@app.put("/streamings/{id}", tags=["streamings"])
async def api_streaming_put(id:uuid.UUID, item:StreamingsModel):
  stream_mgmt = StreamMgmt()
  if str(id) not in stream_mgmt.couchdb_cli:
    raise HTTPException(
      status_code=HTTPStatus.HTTP_404_NOT_FOUND,
      detail="Streaming Doc with id '%s' not found" %id
    )

  data = dict(item)
  data["id"] = str(id)
  stream_mgmt.update_vod_doc(id=str(id), item=data)

  return item

#--------------------------------------------
@app.delete("/streamings/{id}", tags=["streamings"])
async def api_streaming_put(id:uuid.UUID):
  stream_mgmt = StreamMgmt()
  if str(id) not in stream_mgmt.couchdb_cli:
    raise HTTPException(
      status_code=HTTPStatus.HTTP_404_NOT_FOUND,
      detail="Streaming Doc with id '%s' not found" %id
    )

  stream_mgmt.delete_streaming(id=str(id))
  return id

#--------------------------------------------
@app.get("/player", tags=["streamings"])
async def api_streamings_player_get():
  cur_dir = os.path.dirname(os.path.realpath(__file__))
  cur_path = os.path.join(cur_dir, 'player.html')
  return FileResponse(cur_path)

#--------------------------------------------
# @app.get("/stream/{id}/{filename}", tags=["stream"])
# async def stream_file_get(id:uuid.UUID, filename:str):
  
#   object_path = str(id) + "/" + filename
#   # stream_serve = StreamServ()
  
#   chk_res = stream_serve.check_object_exist(object_path)
#   if not chk_res:
#     raise HTTPException(
#       status_code=HTTPStatus.HTTP_404_NOT_FOUND,
#       detail="file '%s' not found in bucket '%s'" %(id, filename))

#   res = stream_serve.get_object_as_bytes(object_name=object_path)
#   content_type = res.headers['Content-Type']
#   data = res.read()
  
#   # return {"id": id, "filename":filename}
#   return StreamingResponse(BytesIO(data), media_type=content_type)
  



#--------------------------------------------




#--------------------------------------------
def bucket_db_sync_fw_func():
  while True:
    print( "bucket_db_sync: %s" %int( time.time()) )
    try:
      stream_mgmt = StreamMgmt()
      stream_mgmt.sync_bucket_with_db()
    except Exception as e:
      print(e)
    time.sleep(10)

#-The Runner---------------------------------------------------------
if __name__ == "__main__":

  # th = Thread(target=bucket_db_sync_fw_func, daemon=True)
  # th.start()

  if "dev".lower() in sys.argv:
    print("Dev Mode")
    uvicorn.run(app="__main__:app", host="0.0.0.0", port=app_settings.app_port, debug=True, reload=True)
  else:
    print("Prod Mode")
    uvicorn.run(app="__main__:app", host="0.0.0.0", port=app_settings.app_port)