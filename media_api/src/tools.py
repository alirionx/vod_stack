import time
import json
from threading import Thread

from io import BytesIO
import starlette
from minio import Minio
import pika

from settings import app_settings

#--------------------------------------------------------
class FileHandler:
  def __init__(self):
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
  def get_list_of_object_names(self):
    res = self.get_list_of_objects()
    obj_name_list = []
    for item in res:
      obj_name_list.append(item._object_name)

    return obj_name_list

  #---------------------------
  
  

#--------------------------------------------------------
class JobHandler:
  def __init__(self):
    self.job_queue = app_settings.rabbitmq_job_queue
    self.status_queue = app_settings.rabbitmq_status_queue
    self.rabbitmq_connection = None

    self.credentials = pika.PlainCredentials(
      username = app_settings.rabbitmq_user, 
      password = app_settings.rabbitmq_password
    )

    self.create_rabbitmq_connection()

  #---------------------------
  def create_rabbitmq_connection(self):
    
    if app_settings.rabbitmq_noauth:
      self.rabbitmq_connection = pika.BlockingConnection(
        pika.ConnectionParameters(
          host = app_settings.rabbitmq_host,
          port = app_settings.rabbitmq_port
        ))
    else:
      self.rabbitmq_connection = pika.BlockingConnection(
        pika.ConnectionParameters(
          host = app_settings.rabbitmq_host,
          port = app_settings.rabbitmq_port,
          credentials=self.credentials
        ))

  #---------------------------
  def send_job_to_queue(self, payload:str):
    ch = self.rabbitmq_connection.channel()
    qu = ch.queue_declare(
      queue=self.job_queue,
      durable=True
    )

    ch.basic_publish(
      exchange='',
      routing_key=self.job_queue,
      body=payload,
      properties=pika.BasicProperties(
        delivery_mode=2,  # make message persistent
      )
    )
    self.close_connection_and_cleanup()

  #---------------------------
  #BRUDAL ;)
  def get_queue_state(self):  
    res = []

    #-------------
    def on_message(ch, method, properties, body):
      item = json.loads( body.decode() )
      item["delivery_tag"] = method.delivery_tag
      item["routing_key"] = method.routing_key
      res.append( item )
    
    #-------------
    def timeout_kill_func():
      time.sleep(0.2)
      ch.stop_consuming()

    #-------------
    ch = self.rabbitmq_connection.channel()
    qu = ch.queue_declare(queue=self.job_queue, durable=True)
    ch.basic_consume(on_message_callback=on_message, queue=self.job_queue)
    
    #-------------
    tmp_tread = Thread(target=timeout_kill_func)
    tmp_tread.start()
    ch.start_consuming()

    #-------------
    self.close_connection_and_cleanup()
    return res

  #---------------------------
  def delete_job_in_queue(self, delivery_tag:int):

    #-------------
    def callback(ch, method, properties, body):
      if method.delivery_tag == delivery_tag:
        ch.basic_ack(delivery_tag=delivery_tag)
        ch.stop_consuming()

    #-------------
    def timeout_kill_func():
      time.sleep(0.2)
      ch.stop_consuming()

    #-------------
    ch = self.rabbitmq_connection.channel()
    qu = ch.queue_declare(queue=self.job_queue)
    ch.basic_consume(queue=self.job_queue, on_message_callback=callback, auto_ack=False)

    #-------------
    tmp_tread = Thread(target=timeout_kill_func)
    tmp_tread.start()
    ch.start_consuming()

    #-------------
    self.close_connection_and_cleanup()
    
  #---------------------------
  def delete_queue_by_name(self, queue_name:str):
    ch = self.rabbitmq_connection.channel()
    ch_res = ch.queue_delete(queue=queue_name)
    res = {
      "queue_name": queue_name,
      "message_count": ch_res.method.message_count
    }
    return res

  #---------------------------
  def get_converter_state(self):
    ch = self.rabbitmq_connection.channel()
    qu = ch.queue_declare(
      queue = self.status_queue,
      arguments={'x-message-ttl' : 10000}
    )

    status_data = {}
    while True:
      res = ch.basic_get( queue = self.status_queue, auto_ack=True )
      if not res[0]: break
      
      item = json.loads(res[2])
      if item["object_name"] not in status_data:
        status_data[item["object_name"]] = {}
      
      status_data[item["object_name"]] = item

    # print(status_obj)
    return status_data


  #---------------------------
  def close_connection_and_cleanup(self):
    if self.rabbitmq_connection:
      self.rabbitmq_connection.close()
      self.rabbitmq_connection = None
    
  #---------------------------
  
  
  #---------------------------
  
