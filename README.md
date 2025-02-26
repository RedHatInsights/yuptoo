# Yupana Upload Processor II

## How it Works

![UML](https://www.plantuml.com/plantuml/png/VLF1Rjim3BtxAmJlkXRhslKG344FMuvhWNM7eIaCMgOJRRBaaNIwBCY_JvGRD6cHw1BalIVoyL6-OG6IeVE5EF5eVlwukx-zDNSKBJAxi30p7vyA38bUczw3j96wyw7t4Pfp224EmU8nVWNUDI0kXg874cTT3q7CUkWbnZUNN5WbADBwV1bPKcz2veEBozeLnpoSJSUo4zFnelWM1GsvnL9CR8_wdfXDIVXdG9RADUN4b53RvkBZvLNvVXvAi3R9HF4FUYuosfCBwiShhjfFrnbdzmyLqj_AXQfU2_B88AsSpMI3EbcEnEnWbLWGNAJHLTCwZsO7P7QWtAmUx6-KIlyfMbzV9TTZYfa6nZseOg4KOfPsAD20G99jjlEmBSQiNZBx4f-2HiC6o2xT2arBiPk7xvTcxFhcnjU_Gc253M4VIGnxPv7pjLsD0dp21sjrZoQTrpNk2GBhOenk_51p-bdaBMVzuQPtbJVbyxWFcx9Lctdol8mr2tPLJr5ppl3sKObTmselhCynLNO1V9NQLRyuXkcsGCyf7d1-8Dop_F1EtyXizgZUZtq7htnxRFTjdtwEBrMKUZPG9Z-XAKwdTJPTrcviVPFKG-V_0m00 "Yuptoo Processing Flow")

See more details in this [Yuptoo Documentation](https://inscope.corp.redhat.com/docs/default/Component/yuptoo/).

## What is different in yuptoo compared to legacy yupana
- No database.
- No explicit state-machine.
- No django service for readiness and liveness probes.
- More robust and decoupled code.

## Usage

```python
pipenv install --dev
pipenv run python main.py
```

## Modifiers
Yuptoo has the concept of modifiers which are used for manipulating host data before sending it to host inventory.

Read more about modifiers - [yuptoo/modifiers](https://github.com/RedHatInsights/yuptoo/tree/main/yuptoo/modifiers)

## Testing and Linting

To run pytest hit the below command in yuptoo root directory
```
pipenv run python -m pytest
```

For linting run the below command.
```
pipenv run flake8
```

## Running with Docker Compose

Two docker-compose files are made available in this repo for standing up a local dev environment. The `full-stack.yml` file stands up ingress, kafka, yuptoo, minio, and inventory components so that the entire first bits of the platform pipeline can be tested. The `docker-compose.yml` file stands up services without yuptoo, the yuptoo can be run manaully in local for development tests.

Stand Up Full Stack

```sh
cd scripts && source .env && sudo docker-compose -f full-stack.yml up
```

Stand Up Yuptoo Manually outside the docker-compose

```sh
cd scripts && source .env && sudo docker-compose up
```
Read more about local development tests env - [docs/local_environment.md](https://github.com/RedHatInsights/yuptoo/tree/main/docs/local_environment.md)


**NOTE**: The full stack expects you to have an ingress and inventory image available, by default, those will be pulled from quay.io. See those projects for steps for building the images needed.
