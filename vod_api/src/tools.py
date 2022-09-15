import os
import sys
import shutil
import time
import datetime
import json
import uuid

from io import BytesIO

from pydantic import BaseModel

from minio import Minio
import couchdb	


from settings import app_settings


#--------------------------------------------------------
# class StreamingDoc(BaseModel):
#   object_name: str
#   id: uuid.UUID
#   media_name: str
#   media_description: str | None = None
#   publisher: str | None = None
#   tmdb_id: int | None = None
  

#--------------------------------------------------------
class StreamMgmt:
  def __init__(self):
    
    self.bucket_name = app_settings.minio_streaming_bucket
    self.database_name = app_settings.couchdb_database

    self.minio_cli = None
    self.couchdb_cli = None

    self.streamings_list = [] 
    self.docs_list = [] 

    #----------
    self.create_minio_cli()
    self.check_minio_bucket()

    self.create_couchdb_cli()

  #---------------------------------
  def create_minio_cli(self):
    self.minio_cli = Minio(
      app_settings.minio_host + ":" + str(app_settings.minio_port),
      access_key = app_settings.minio_user,
      secret_key = app_settings.minio_password,
      secure=False
    )

  #---------------------------------
  def check_minio_bucket(self):
    if not self.minio_cli.bucket_exists(self.bucket_name):
      raise Exception(
        "Media Souce bucket '%s' does not exist" %app_settings.minio_streaming_bucket
      )

  #---------------------------------
  def create_couchdb_cli(self):
    couch = couchdb.Server(
      'http://%s:%s@%s:%s/' %(
        app_settings.couchdb_user, 
        app_settings.couchdb_password, 
        app_settings.couchdb_host, 
        app_settings.couchdb_port
      )
    )
    if not self.database_name in couch:
      couch.create(self.database_name)
    self.couchdb_cli = couch[self.database_name]

  #---------------------------------
  def insert_vod_doc(self, item:dict):
    item["_id"] = item["id"] 
    res = self.couchdb_cli.save(item)

  #---------------------------------
  def update_vod_doc(self, id, item:dict):
    doc = self.couchdb_cli[id]
    for key,val in item.items():
      doc[key] = val
    self.couchdb_cli.save(doc)


  #---------------------------------
  def get_docs_from_db(self):
    self.docs_list = []
    for id in self.couchdb_cli:
      item = dict(self.couchdb_cli.get(id=id))
      del item["_id"]
      del item["_rev"]
      self.docs_list.append( item )
  
  #---------------------------------
  def get_doc_by_id(self, id:str):
    res = dict(self.couchdb_cli[id])
    del res["_id"]
    del res["_rev"]
    return res
  
  #---------------------------------
  def delete_doc_by_id(self, id:str):
    item = self.get_doc_by_id(id=id)
    res = self.couchdb_cli.delete(item)

  #---------------------------------
  def delete_all_docs_in_db(self):
    for id in self.couchdb_cli:
      res = self.couchdb_cli[id]
      self.couchdb_cli.delete(res)
  
  #---------------------------------
  def get_vod_items_from_bucket(self):
    self.streamings_list = [] 
    res = self.minio_cli.list_objects(bucket_name=self.bucket_name)

    #---------------
    for item in res:
      try:
        res2 = self.minio_cli.get_object(
          bucket_name=self.bucket_name, 
          object_name=item.object_name+"object_item.json"
        )
      except Exception as e:
        print(e)
        continue
      
      #-----------
      data = json.loads( res2.read().decode() )
      self.streamings_list.append( data )
      
  #---------------------------------
  def delete_streaming(self, id:str):
    res = self.minio_cli.list_objects(
      bucket_name=self.bucket_name, 
      prefix=id, 
      recursive=True
    )
    for obj in res:
      self.minio_cli.remove_object(
        bucket_name=self.bucket_name, 
        object_name=obj.object_name
      )

    self.delete_doc_by_id(id=id)

  #---------------------------------
  def sync_bucket_with_db(self):
    
    # self.get_docs_from_db()
    self.get_vod_items_from_bucket()
    streams_id_list = []

    #--------
    for item in self.streamings_list:
      if item["id"] not in list(self.couchdb_cli):
        self.insert_vod_doc(item)
      streams_id_list.append(item["id"])

    #--------
    for id in self.couchdb_cli:
      if id not in streams_id_list:
        try:
          self.delete_doc_by_id(id=id)
        except Exception as e:
          print(e)

  #---------------------------------

  
  #---------------------------------



#--------------------------------------------------------
# class StreamServ:
#   def __init__(self):
#     self.test = ""
#     self.bucket_name = app_settings.minio_streaming_bucket

#     self.create_minio_cli()
#     self.check_minio_bucket()
  
#   #---------------------------
#   def create_minio_cli(self):
#     self.minio_cli = Minio(
#       app_settings.minio_host + ":" + str(app_settings.minio_port),
#       access_key = app_settings.minio_user,
#       secret_key = app_settings.minio_password,
#       secure=False
#     )

#   #---------------------------
#   def check_minio_bucket(self):
#     if not self.minio_cli.bucket_exists(self.bucket_name):
#       self.minio_cli.make_bucket(self.bucket_name)

#   #---------------------------
#   def check_object_exist(self, object_name:str):
#     try:
#       tags = self.minio_cli.get_object_tags(
#         bucket_name = self.bucket_name,
#         object_name = object_name
#       )
#       return True
#     except:
#       return False

#   #-------------------------------
#   def get_object_as_bytes(self, object_name:str):
    
#     res = self.minio_cli.get_object(
#       bucket_name = self.bucket_name,
#       object_name = object_name
#     )
    
#     return res

#   #-------------------------------
#   def download_files_to_tmp(self, id:str):
#     obj_list = self.minio_cli.list_objects(
#       bucket_name = self.bucket_name,
#       prefix=id,
#       recursive=True
#     )
#     for obj in obj_list:
#       # print(obj.object_name)
#       self.minio_cli.fget_object(
#         bucket_name = self.bucket_name,
#         object_name = obj.object_name, 
#         file_path = "./tmp/"+obj.object_name)


  #-------------------------------


#--------------------------------------------------------