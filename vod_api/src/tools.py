import os
import sys
import shutil
import time
import datetime
import json

from io import BytesIO

from minio import Minio
import couchdb	


from settings import app_settings


#--------------------------------------------------------
class StreamMgmt:
  def __init__(self):
    self.minio_cli = None
    self.bucket_name = app_settings.minio_streaming_bucket

    self.couchdb_cli = None

    self.create_minio_cli()
    self.check_minio_bucket()

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
    self.couchdb_cli = couchdb.Server('https://username:password@host:port/')

    
  #---------------------------------


  
  
  #---------------------------------
  
  
  #---------------------------------
  
  
  #---------------------------------
  
  
  #---------------------------------



#--------------------------------------------------------
class StreamServ:
  def __init__(self):
    self.test = ""
    self.bucket_name = app_settings.minio_streaming_bucket

    self.create_minio_cli()
    self.check_minio_bucket()
  
  #---------------------------
  def create_minio_cli(self):
    self.minio_cli = Minio(
      app_settings.minio_host + ":" + str(app_settings.minio_port),
      access_key = app_settings.minio_user,
      secret_key = app_settings.minio_password,
      secure=False
    )

  #---------------------------
  def check_minio_bucket(self):
    if not self.minio_cli.bucket_exists(self.bucket_name):
      self.minio_cli.make_bucket(self.bucket_name)

  #---------------------------
  def check_object_exist(self, object_name:str):
    try:
      tags = self.minio_cli.get_object_tags(
        bucket_name = self.bucket_name,
        object_name = object_name
      )
      return True
    except:
      return False

  #-------------------------------
  def get_object_as_bytes(self, object_name:str):
    
    res = self.minio_cli.get_object(
      bucket_name = self.bucket_name,
      object_name = object_name
    )
    
    return res

  #-------------------------------
  def download_files_to_tmp(self, id:str):
    obj_list = self.minio_cli.list_objects(
      bucket_name = self.bucket_name,
      prefix=id,
      recursive=True
    )
    for obj in obj_list:
      # print(obj.object_name)
      self.minio_cli.fget_object(
        bucket_name = self.bucket_name,
        object_name = obj.object_name, 
        file_path = "./tmp/"+obj.object_name)


  #-------------------------------


#--------------------------------------------------------