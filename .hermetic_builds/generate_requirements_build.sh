#!/bin/bash

pip3 install --upgrade "pip>=26.1.2"
pip3 install pip-tools pybuild-deps
cd /var/tmp

pybuild-deps compile --generate-hashes requirements.txt -o requirements-build.txt

# pybuild-deps may emit setuptools==82 even when requirements.txt pins <82.
if grep -q '^setuptools==82\.' requirements-build.txt; then
    # Drop the setuptools==82 pin block (package line + indented continuations).
    awk '
      /^setuptools==82\./ { skip=1; next }
      skip && /^[[:space:]]/ { next }
      skip { skip=0 }
      { print }
    ' requirements-build.txt > requirements-build.txt.tmp \
      && mv requirements-build.txt.tmp requirements-build.txt
fi

pip-compile requirements-build.in --allow-unsafe --generate-hashes -o requirements-extras.txt
