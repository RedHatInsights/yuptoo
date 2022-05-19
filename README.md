# Yupana Upload Processor II

## How it Works

![UML](https://www.plantuml.com/plantuml/png/VLBBRjim4BphAmZrsXXDa-PW54OEhOzDWAQ78Wu4YbhPsrAaibmwLGt_UxXKZDXvM1V3iuyPpknbO4qSErimiWNr-zVrpTMLkYPl80HqIpMt_g40byg3wgtcrbCtYRtrkfdSz-QzqbfRR3IZTqMV6D1Whnsh8VRi_QiXTEi4UHecAnyuqL9YFnXSrLYyGNyo6pTELHUMnG_Fe0YNArQ-VKljL6rAWli8WIjiogagTMsQqyzdv-N7XIkrCJuw5loJVASPxGcTgB22I--NYum7_0y2oM-5hge7XZ1MWDPeSh41UKysGkrWQJ6QOPaUB3qjMb0x85SZPR8wch_0bVmJjBuuJwf7xt9P1zY3gi2KhCkj7R1EzklKjjaktBOORNgswvj_SE9AK9hC2jUWMlBTmlqyKoFhgudl_vYquQ08Ua-iWaK38O_jTXJQ9ZmQ8-cfzBtSSKFQ1Sb4ISw7FSUF8GUS-mz37gSbrwVdtcxALcJcb-SmXi3GLJrvyJd3spifx0YhFRE--hGvvMMhH5Vz2TxDjWNOaEpHQ2F1dkJR3t8Zy_cTQ7_l-b_ejj3kopv-ZizRfFGae4nwN5CST-jajgfnfBvCtR6pZm00 "Yuptoo Processing Flow")

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
