#!/bin/bash

# Pin every generator input exactly: this script produces hash-locked files, so a
# floating version here leaks non-determinism into its output.
# pip-tools is capped at 7.6.0 because 7.6.1 removed the `generate_hashes` argument
# from OutputWriter, which pybuild-deps 0.5.0 still passes. pybuild-deps 0.6.1
# carries the same `pip-tools<7.6.1` cap in its own metadata.
# pip is held at 26.1.2: it is the CVE-2026-8643 floor and the last pip compatible
# with pip-tools 7.6.0. This pin governs only the generator; the shipped image
# installs its own pip in the Dockerfile.
pip3 install "pip==26.1.2"
pip3 install "pip-tools==7.6.0" "pybuild-deps==0.5.0"
cd /var/tmp

pybuild-deps compile --generate-hashes requirements.txt -o requirements-build.txt

# Strip setuptools stanzas at or above SETUPTOOLS_CEILING.
#
# Several packages declare an unbounded `setuptools>=N` build requirement, so
# pybuild-deps resolves those to the newest setuptools on PyPI and emits a second
# setuptools stanza alongside the one matching the runtime pin. That newer stanza
# can exceed what other packages can actually build against.
#
# The binding constraint is charset-normalizer, whose pyproject.toml declares
# `setuptools>=68,<84.1` (as of 3.5.2). It is currently the only setuptools
# consumer in requirements.txt with an upper bound that applies on python 3.11.
# Re-check this ceiling whenever charset-normalizer is bumped.
#
# Historical note: an earlier version of this filter matched the literal string
# "82." and was guarded by a `grep -q`. When setuptools moved to 84 the guard
# stopped matching, the filter never ran, and the script still exited 0. It
# failed open. Hence the numeric comparison below and no guard.
SETUPTOOLS_CEILING_MAJOR=84
SETUPTOOLS_CEILING_MINOR=1

awk -v cmaj="$SETUPTOOLS_CEILING_MAJOR" -v cmin="$SETUPTOOLS_CEILING_MINOR" '
BEGIN { skip=0 }
{
  if (skip) {
    if ($0 ~ /^[[:space:]]/) { next }   # indented continuation (hashes / # via)
    skip=0                               # non-indented line ends the stanza
  }
  if ($0 ~ /^setuptools==/) {
    v=$0; sub(/^setuptools==/,"",v); sub(/[^0-9.].*/,"",v); sub(/\.$/,"",v)
    n=split(v,part,".")
    maj=part[1]+0; min=(n>1 ? part[2]+0 : 0)
    if (maj > cmaj+0 || (maj == cmaj+0 && min >= cmin+0)) { skip=1; next }
  }
  print
}
' requirements-build.txt > requirements-build.txt.tmp
mv requirements-build.txt.tmp requirements-build.txt

pip-compile requirements-build.in --allow-unsafe --generate-hashes -o requirements-extras.txt
