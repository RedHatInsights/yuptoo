#!/bin/bash

#
# A script to run a series of 'make' commands in sequence.
# It accepts optional named arguments for BASE_IMAGE, COMMAND_TYPES, and IMAGE_ARCH,
# pulls the image, inspects it, and then passes it to each command.
# If no arguments are provided, default values are used.
# It checks the return code of each command and exits immediately
# if a command fails, printing an error message.
#

# --- Configuration ---
# Set 'e' option to exit immediately if a command exits with a non-zero status.
# This provides a safety net, although the script also has explicit checks.
set -e

# --- Default Values ---
DEFAULT_BASE_IMAGE="registry.access.redhat.com/ubi9/ubi-minimal:latest"
DEFAULT_COMMAND_TYPES="all"
DEFAULT_IMAGE_ARCH="x86_64"

# --- Helper Functions ---

# Prints the usage information for the script.
usage() {
  echo "Usage: $0 [--base-image <IMAGE>] [--image-arch <ARCH>] [--command-types <TYPE1,TYPE2,...>] [--skip-pull]"
  echo "  --base-image      Optional. The base container image to use. Defaults to '$DEFAULT_BASE_IMAGE'."
  echo "  --image-arch      Optional. The architecture for the base image. Defaults to '$DEFAULT_IMAGE_ARCH'."
  echo "  --command-types   Optional. A comma-separated list of command types to run. Valid types are: all, rpm, python. Defaults to '$DEFAULT_COMMAND_TYPES'."
  echo "  --skip-pull       Optional. If set, skips pulling and inspecting the base image."
  echo "Example: $0 --base-image my/custom-image:latest --command-types rpm,python"
}

# Executes any command passed to it and checks the exit code.
run_command() {
  echo "🚀 Executing: $@"
  "$@"
  local exit_code=$?
  if [ $exit_code -ne 0 ]; then
    echo "❌ ERROR: Command '$@' failed with exit code $exit_code." >&2
    exit $exit_code
  else
    echo "✅ SUCCESS: Command '$@' finished."
  fi
  echo
}

# Checks if a given element is present in an array.
containsElement () {
  local e match="$1"
  shift
  for e; do [[ "$e" == "$match" ]] && return 0; done
  return 1
}

# --- Argument Parsing ---
# Initialize variables with default values.
BASE_IMAGE="$DEFAULT_BASE_IMAGE"
COMMAND_TYPES="$DEFAULT_COMMAND_TYPES"
IMAGE_ARCH="$DEFAULT_IMAGE_ARCH"
SKIP_PULL=false

while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --base-image)
      BASE_IMAGE="$2"
      shift # past argument
      shift # past value
      ;;
    --image-arch)
      IMAGE_ARCH="$2"
      shift # past argument
      shift # past value
      ;;
    --command-types)
      COMMAND_TYPES="$2"
      shift # past argument
      shift # past value
      ;;
    --skip-pull)
      SKIP_PULL=true
      shift # past argument
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)    # unknown option
      echo "❌ ERROR: Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

echo "ℹ️ Using BASE_IMAGE: $BASE_IMAGE"
echo "ℹ️ Using IMAGE_ARCH: $IMAGE_ARCH"
echo "ℹ️ Running command types: $COMMAND_TYPES"
echo

# --- Command Type Validation ---
# Convert the comma-separated string into an array.
IFS=',' read -r -a requested_command_types <<< "$COMMAND_TYPES"
valid_command_types=("all" "rpm" "python")

for type in "${requested_command_types[@]}"; do
  if ! containsElement "$type" "${valid_command_types[@]}"; then
    echo "❌ ERROR: Invalid command type '$type'. Valid types are: all, rpm, python." >&2
    exit 1
  fi
done

# --- Image Preparation ---
if [ "$SKIP_PULL" = false ]; then
  echo "--- Preparing Base Image ---"
  echo

  # 1. Pull the base image
  run_command podman pull --arch "$IMAGE_ARCH" "$BASE_IMAGE"

  # 2. Inspect the image to find all its tags
  echo "🔍 Inspecting image for all associated tags..."
  tags_output=$(podman inspect --format '{{.RepoTags}}' "$BASE_IMAGE")
  tags_list=${tags_output//[\[\]]/}

  if [ -z "$tags_list" ]; then
      echo "⚠️ No tags found for $BASE_IMAGE"
  else
      echo "Found the following tags:"
      for tag in $tags_list; do
        echo "  - $tag"
      done
  fi
  echo
else
  echo "ℹ️ Skipping image pull and inspect as requested by --skip-pull flag."
  echo
fi

# --- Command Definitions ---
# Define the commands to be run in arrays for easy looping.
RPM_COMMANDS=(
  "make generate-repo-file"
  "make generate-rpms-in-yaml"
  "make generate-rpm-lockfile"
)

PYTHON_COMMANDS=(
  "make generate-requirements-txt"
  "make generate-requirements-build-in"
  "make generate-requirements-build-txt"
)


# --- Main Script Logic ---
echo "--- Starting Build Process ---"
echo

# Check if we need to run the RPM-related commands (type "rpm" or "all")
if containsElement "all" "${requested_command_types[@]}" || containsElement "rpm" "${requested_command_types[@]}"; then
  echo "--- Processing RPM Commands (type: rpm) ---"
  echo
  for cmd in "${RPM_COMMANDS[@]}"; do
    run_command $cmd BASE_IMAGE=$BASE_IMAGE
  done
fi

# Check if we need to run the Python-related commands (type "python" or "all")
if containsElement "all" "${requested_command_types[@]}" || containsElement "python" "${requested_command_types[@]}"; then
  echo "--- Processing Python Requirements (type: python) ---"
  echo
  for cmd in "${PYTHON_COMMANDS[@]}"; do
    run_command $cmd BASE_IMAGE=$BASE_IMAGE
  done
fi


# If the script reaches this point, all requested commands have succeeded.
echo "🎉 All commands completed successfully!"

# Exit with a success code.
exit 0
