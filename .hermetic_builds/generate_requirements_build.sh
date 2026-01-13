#!/bin/bash

pip3 install pip-tools pybuild-deps
pip3 install "pip<25"
cd /var/tmp

pybuild-deps compile --generate-hashes requirements.txt -o requirements-build.txt --verbose
pip-compile requirements-build.in --allow-unsafe --generate-hashes -o requirements-extras.txt --verbose
