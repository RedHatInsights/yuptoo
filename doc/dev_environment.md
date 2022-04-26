# Yuptoo Development environment.

Below are the instructions to setup yuptoo development environment.

## Installation

1. Clone the repository
   ```
   git clone https://github.com/RedHatInsights/yuptoo.git
   ```
2. Install librdkafka and librdkafka-devel packages
   ```
   dnf install -y librdkafka librdkafka-devel
   ```
3. Spin up required containers/services.
   ```
   cd scripts/
   docker login quay.io
   . .env 
   docker-compose up
   ```
4. Run the yuptoo service
   ```
   pipenv install
   pipenv run python main.py
   ```

## Usage

For testing create the sample-data and upload it to yuptoo. 

```
make sample-data
make local-upload-data file=temp/sample_data_ready_******.tar.gz
```

## Extra

Commands for monitoring kafka topic

```bash
# docker-compose exec kafka kafka-console-consumer --topic=platform.upload.qpc --bootstrap-server=localhost:29092
# docker-compose exec kafka kafka-console-consumer --topic=platform.inventory.host-ingress --bootstrap-server=localhost:29092
```