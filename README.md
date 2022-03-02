# Yupana Upload Processor II

Yuptoo is a service that works with the Insights Platform services.  It's primary purpose is to receive bulk uploads of hosts.  A client will create a specially crafted tarball and send the file to the Insights Ingress service.  The Ingress service will notify yuptoo via Kafka that a tarball has arrived for processing. Yuptoo downloads the tarball, performs top level validation, and sends the host JSON to the Insight's Host Based Inventory service.

## How it Works

Architecture Diagram

## Running Yuptoo Locally

### Within docker
To run the dependent services within docker.
```bash
docker-compose -f full-stack-dev.yml up
```

### On host machine
In order to properly run the application from the host machine, you need to have modified your `/etc/hosts` file.
```
127.0.0.1       kafka
127.0.0.1       minio
```

#### Running the yuptoo consumer locally
```bash
pipenv run python3 -m yuptoo.processor.main
```

#### Uploading the archive to yuptoo via ingress
```bash
curl -vvvvF "file=@temp/sample.tar.gz;type=application/vnd.redhat.qpc.sample+tgz" -H "x-rh-identity: eyJpZGVudGl0eSI6IHsiYWNjb3VudF9udW1iZXIiOiAic3lzYWNjb3VudCIsICJ0eXBlIjogIlN5c3RlbSIsICJhdXRoX3R5cGUiOiAiY2VydC1hdXRoIiwgInN5c3RlbSI6IHsiY24iOiAiMWIzNmIyMGYtN2ZhMC00NDU0LWE2ZDItMDA4Mjk0ZTA2Mzc4IiwgImNlcnRfdHlwZSI6ICJzeXN0ZW0ifSwgImludGVybmFsIjogeyJvcmdfaWQiOiAiMzM0MDg1MSIsICJhdXRoX3RpbWUiOiA2MzAwfX19" -H "x-rh-request_id: testtesttest" http://localhost:8080/api/ingress/v1/upload
```