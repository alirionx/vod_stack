from io import BytesIO
from socket import timeout
import starlette
from minio import Minio


from settings import app_settings

class FileHandler:
  def __init__(self):
    self.test = "test"
    self.minio_cli = None

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
    # if not self.minio_cli: self.create_minio_cli()
    if not self.minio_cli.bucket_exists(app_settings.minio_transfer_bucket):
      self.minio_cli.make_bucket(app_settings.minio_transfer_bucket)

  #---------------------------
  async def upload_media_from_byte(self, file:starlette.datastructures.UploadFile):
    data = await file.read() 
    stream = BytesIO(data)
    # print(len(data), type(data))
    # print(data[0:10])

    self.minio_cli.put_object(
      bucket_name = app_settings.minio_transfer_bucket, 
      object_name = file.filename,
      data=stream,
      length=len(data)
    )

  #---------------------------
  def upload_media_from_path(self, filename:str, path:str):
    self.minio_cli.fput_object(
      app_settings.minio_transfer_bucket, 
      filename,
      path
    )

  #---------------------------
  def delete_media_by_filename(self, filename:str):
    self.minio_cli.remove_object(
      bucket_name = app_settings.minio_transfer_bucket, 
      object_name = filename
    )

  #---------------------------
  def get_list_of_objects(self):
    res = self.minio_cli.list_objects(
      bucket_name = app_settings.minio_transfer_bucket
    )
    return res

  #---------------------------
  
  
  #---------------------------