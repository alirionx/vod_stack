## A K8s Ready Example Stack for Video on Demand Services



### Minio Things
docker run -d \
  --name some-minio \
  -p 9000:9000 \
  -p 9001:9001 \
  -e "MINIO_ROOT_USER=minio" \
  -e "MINIO_ROOT_PASSWORD=VERYSECRET" \
  minio/minio server /data --console-address ":9001"