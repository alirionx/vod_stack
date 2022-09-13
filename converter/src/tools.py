from ast import arg
import os
import sys
import shutil
import time
import datetime
import json

from subprocess import PIPE
from threading import Thread
from io import BytesIO

from minio import Minio
import pika

import ffmpegio
from ffmpegio import ffmpeg, ffprobe, ffmpegprocess
import ffmpeg_streaming

from settings import app_settings


#--------------------------------------------------------
class JobWorker:
  def __init__(self):
    self.job_queue = app_settings.rabbitmq_job_queue
    self.status_queue = app_settings.rabbitmq_status_queue
    self.rabbitmq_connection = None

    self.credentials = pika.PlainCredentials(
      username = app_settings.rabbitmq_user, 
      password = app_settings.rabbitmq_password
    )

    self.create_rabbitmq_connection()

    shutil.rmtree(app_settings.job_temp_dir, ignore_errors=True)

  #-------------------------------
  def create_rabbitmq_connection(self):
    self.rabbitmq_connection = pika.BlockingConnection(
      pika.ConnectionParameters(
        host = app_settings.rabbitmq_host,
        port = app_settings.rabbitmq_port,
        credentials=self.credentials
      ))

  #-------------------------------
  def on_job_receive(self, ch, method, properties, body):
    #----------
    item = json.loads( body.decode() )
    # item["delivery_tag"] = method.delivery_tag
    # item["routing_key"] = method.routing_key
    print(item)

    #----------
    converter = Converter(object_item=item)
    converter.download_object()
    # converter.get_media_info()

    #----------
    thread_convert = Thread(target=converter.media_to_hls, args=(True,))
    thread_convert.start()
    while thread_convert.is_alive():  # Loop while the thread is processing
      ch._connection.sleep(2.0)

    thread_upload = Thread(target=converter.upload_stream_data)
    thread_upload.start()
    while thread_upload.is_alive():  # Loop while the thread is processing
      ch._connection.sleep(2.0)

    #----------
    ch.basic_ack(delivery_tag=method.delivery_tag)
    

  #-------------------------------
  def start_consuming_jobs(self):
    ch = self.rabbitmq_connection.channel()
    qu = ch.queue_declare(queue=self.job_queue, durable=True)
    ch.basic_consume(
      queue = self.job_queue, 
      on_message_callback = self.on_job_receive, 
      auto_ack = False
    )
    ch.start_consuming()



  #-------------------------------


  #-------------------------------


  #-------------------------------


#--------------------------------------------------------
class Converter:

  _480p  = ffmpeg_streaming.Representation(ffmpeg_streaming.Size(854, 480), ffmpeg_streaming.Bitrate(750 * 1024, 192 * 1024))
  _720p  = ffmpeg_streaming.Representation(ffmpeg_streaming.Size(1280, 720), ffmpeg_streaming.Bitrate(2048 * 1024, 320 * 1024))
  _1080p = ffmpeg_streaming.Representation(ffmpeg_streaming.Size(1920, 1080), ffmpeg_streaming.Bitrate(4096 * 1024, 320 * 1024))

  def __init__(self, object_item:dict):
    #--------------
    self.minio_cli = None
    self.object_item = object_item
    self.object_name = object_item["object_name"]

    #--------------
    self.media_tmp_path = os.path.join(app_settings.job_temp_dir, self.object_name).replace("\\", "/")
    self.stream_tmp_path = os.path.join(app_settings.job_temp_dir, "stream")
    
    #--------------
    self.rabbitmq_connection = None
    self.status_queue = app_settings.rabbitmq_status_queue
    self.credentials = pika.PlainCredentials(
      username = app_settings.rabbitmq_user, 
      password = app_settings.rabbitmq_password
    )

    #--------------
    self.create_rabbitmq_connection()
    self.create_minio_cli()
    self.check_minio_bucket()
    self.check_object()
    
    #--------------
    shutil.rmtree(app_settings.job_temp_dir, ignore_errors=True)
    os.makedirs(app_settings.job_temp_dir, exist_ok=True)
  
  #-------------------------------
  def create_rabbitmq_connection(self):
    self.rabbitmq_connection = pika.BlockingConnection(
      pika.ConnectionParameters(
        host = app_settings.rabbitmq_host,
        port = app_settings.rabbitmq_port,
        credentials=self.credentials
      ))

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
    if not self.minio_cli.bucket_exists(app_settings.minio_transfer_bucket):
      raise Exception(
        "Media Souce bucket '%s' does not exist" %app_settings.minio_transfer_bucket
      )

  #---------------------------
  def check_object(self):
    tags = self.minio_cli.get_object_tags(
      bucket_name = app_settings.minio_transfer_bucket,
      object_name = self.object_name
    )

  #---------------------------
  def get_list_of_objects(self):
    res = self.minio_cli.list_objects(
      bucket_name = app_settings.minio_transfer_bucket
    )
    return res

  #---------------------------
  def download_object(self):
    #-----------
    status_payload = {
      "job_state": "transcoding",
      "object_name": self.object_name,
      "percentage_done": 0,
      "time_left": "n.a."
    }
    self.publish_stats(payload=status_payload)
    
    #-----------
    response = self.minio_cli.get_object(
      bucket_name = app_settings.minio_transfer_bucket,
      object_name = self.object_name
    )
    
    #-----------
    with open(self.media_tmp_path, "wb") as fl:
      fl.write(response.read())

  #---------------------------
  def get_media_info(self):
    if not os.path.isfile(self.media_tmp_path):
      raise Exception("no media! download it first eg. via 'download_object'")   

    str_res = ffprobe(
      '-v quiet -print_format json -show_format -show_streams -print_format json %s' 
      % self.media_tmp_path,
      stdout=PIPE, universal_newlines=True).stdout
    
    res = json.loads(str_res)
    # print(res)
    return res
  
  #-------------------------------
  def upload_stream_data(self):

    status_payload = {
      "job_state": "uploading",
      "object_name": self.object_name,
      "percentage_done": 0,
      "time_left": "n.a."
    }
    self.publish_stats(payload=status_payload)

    #--------------
    if not self.minio_cli.bucket_exists(bucket_name = app_settings.minio_streaming_bucket):
      self.minio_cli.make_bucket( bucket_name = app_settings.minio_streaming_bucket)
      public_policy = {
        "Version": "2012-10-17",
        "Statement": [
          {
              "Effect": "Allow",
              "Principal": {"AWS": "*"},
              "Action": ["s3:GetBucketLocation", "s3:ListBucket"],
              "Resource": "arn:aws:s3:::%s" %app_settings.minio_streaming_bucket,
          },
          {
              "Effect": "Allow",
              "Principal": {"AWS": "*"},
              "Action": "s3:GetObject",
              "Resource": "arn:aws:s3:::%s/*" %app_settings.minio_streaming_bucket,
          },
        ],
      }
      self.minio_cli.set_bucket_policy(app_settings.minio_streaming_bucket, json.dumps(public_policy))
    
    #--------------
    # tgt_bucket = self.object_item["id"]

    # if self.minio_cli.bucket_exists(bucket_name = tgt_bucket):
    #   tmp_list = self.minio_cli.list_objects(bucket_name = tgt_bucket)
    #   self.minio_cli.remove_objects(bucket_name = tgt_bucket, delete_object_list=tmp_list)
    # else:
    #   self.minio_cli.make_bucket( bucket_name = tgt_bucket)

    #--------------
    with open( os.path.join(self.stream_tmp_path,"object_item.json"), "w" ) as fl:
      fl.write(json.dumps(self.object_item))

    #--------------
    file_list = os.listdir(self.stream_tmp_path)
    num_files = len(file_list)
    i = 0
    for filename in file_list:
      i += 1
      print("upload file %s of %s" %(i, num_files), end='\n')

      cur_path = os.path.join(self.stream_tmp_path, filename)
      self.minio_cli.fput_object(
        bucket_name = app_settings.minio_streaming_bucket,
        file_path = cur_path,
        object_name = self.object_item["id"]+"/"+filename
      )

    #--------------
    status_payload = {
      "job_state": "uploading",
      "object_name": self.object_name,
      "percentage_done": 100,
      "time_left": "n.a."
    }
    self.publish_stats(payload=status_payload)

  #-------------------------------
  def publish_stats(self, payload:dict):
    ch = self.rabbitmq_connection.channel()
    qu = ch.queue_declare(
      queue=self.status_queue,
      arguments={'x-message-ttl' : 10000}
    )

    ch.basic_publish(
      exchange = '',
      routing_key = self.status_queue,
      body = json.dumps(payload)
    )
    ch.close()
    
  #---------------------------
  def media_to_hls(self, monitor=True):
    if not os.path.isfile(self.media_tmp_path):
      raise Exception("no media! download it first eg. via 'download_object'")   

    #----------
    video = ffmpeg_streaming.input(self.media_tmp_path)
    hls = video.dash(ffmpeg_streaming.Formats.h264())
    # hls.auto_generate_representations()
    hls.representations(self._480p, self._720p, self._1080p)

    #----------
    shutil.rmtree(self.stream_tmp_path, ignore_errors=True)
    os.makedirs(self.stream_tmp_path, exist_ok=True)
    tgt_path = os.path.join(self.stream_tmp_path, "stream.mpd")
    
    #----------
    if monitor:
      hls.output(tgt_path, monitor=self.status_monitor)
    else:
      hls.output(tgt_path)

  #---------------------------
  def status_monitor(self, ffmpeg, duration, time_, time_left, process):
    
    percentage_done = round(time_ / duration * 100)
    time_left_str = str(datetime.timedelta(seconds=int(time_left)))

    status_payload = {
      "job_state": "transcoding",
      "object_name": self.object_name,
      "percentage_done": percentage_done,
      "time_left": time_left_str
    }
    self.publish_stats(payload=status_payload)

    sys.stdout.write(
      "\rTranscoding...(%s%%) %s left [%s%s]" %
      (percentage_done, time_left_str, '#' * percentage_done, '-' * (100 - percentage_done))
    )
    sys.stdout.flush()


  #---------------------------



#--------------------------------------------------------