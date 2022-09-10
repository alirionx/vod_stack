## A K8s Ready Example Stack for Video on Demand Services



### Minio Things
docker run -d \
  --name some-minio \
  -p 9000:9000 \
  -p 9001:9001 \
  -e "MINIO_ROOT_USER=minio" \
  -e "MINIO_ROOT_PASSWORD=VERYSECRET" \
  minio/minio server /data --console-address ":9001"


### RabbitMQ Things
-Simple-
docker run -d \
  --name some-rabbitmq \
  -p 5672:5672 \
  rabbitmq:3

-With MGMT WebUi-
docker run -d \
  --hostname some-rabbit \
  --name some-rabbit-mgmt \
  -e RABBITMQ_DEFAULT_USER=guest \
  -e RABBITMQ_DEFAULT_PASS=guest \
  -p 15672:15672 \
  -p 5672:5672 \
  rabbitmq:3-management