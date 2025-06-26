#!/bin/bash

pip3 install pip-tools pybuild-deps
pip3 install "pip<25"
cd /var/tmp

pybuild-deps compile --generate-hashes requirements.txt -o requirements-build.txt