metadata={"branch_info": {"remote_branch": -1, "remote_leaf": -1}, "bios_uuid": "25d6ad97-60fa-4d3e-b2cc-4aa437c28f71", "ip_addresses": ["10.74.255.52", "2620:52:0:4af8:21a:4aff:fe00:a8a"], "fqdn": "vm255-52.gsslab.pnq2.redhat.com", "mac_addresses": ["00:1a:4a:00:0a:8a", "00:00:00:00:00:00"], "satellite_id": -1, "subscription_manager_id": "7846d4fa-6fcc-4b84-aa13-5f12e588ecca", "insights_id": "1d42f242-3828-4a00-8009-c67656c86a51", "machine_id": "25d6ad97-60fa-4d3e-b2cc-4aa437c28f71"}
identity={"identity": {"org_id": "3340851", "type": "System", "auth_type": "cert-auth", "system": {"cn": "1b36b20f-7fa0-4454-a6d2-008294e06378", "cert_type": "system"}, "internal": {"org_id": "3340851", "auth_time": 6300}}}
b64_identity=$(shell echo '${identity}' | base64 -w 0 -)
ifdef env
	short_env=$(shell echo '${env}' | cut -d'-' -f2)
	server=$(shell oc get clowdenvironments env-ephemeral-${short_env} -o=jsonpath='{.status.hostname}')
	username=$(shell oc get secret env-ephemeral-${short_env}-keycloak -n ephemeral-${short_env} -o=jsonpath='{.data.defaultUsername}' | base64 -d)
	password=$(shell oc get secret env-ephemeral-${short_env}-keycloak -n ephemeral-${short_env} -o=jsonpath='{.data.defaultPassword}' | base64 -d)
	auth_header=$(shell echo -n '${username}:${password}' | base64)
endif

# Default value for BASE_IMAGE
BASE_IMAGE ?= registry.access.redhat.com/ubi9/ubi-minimal:latest
# Default value for CONTAINERFILE
CONTAINERFILE ?= Dockerfile
# Default value of IMAGE_ARCH
IMAGE_ARCH ?= x86_64
# Define the AWK command based on platform (gawk on macOS, awk elsewhere)
AWK = awk
ifeq ($(shell uname),Darwin)
AWK = gawk
endif

ensure_image = \
	@if ! podman image exists $(BASE_IMAGE); then \
		echo "--- Image '$(BASE_IMAGE)' not found. Pulling..."; \
		podman pull $(BASE_IMAGE) --arch $(IMAGE_ARCH); \
	else \
		echo "--- Image '$(BASE_IMAGE)' already exists locally. Skipping pull."; \
	fi

local-upload-data:
	curl -vvvv -F "upload=@$(file);type=application/vnd.redhat.qpc.$(basename $(basename $(notdir $(file))))+tgz" \
		-H "x-rh-identity: ${b64_identity}" \
		-H "x-rh-request_id: testtesttest" \
		http://localhost:3000/api/ingress/v1/upload

ephemeral-upload-data:
	curl -vvvv -F "upload=@$(file);type=application/vnd.redhat.qpc.$(basename $(basename $(notdir $(file))))+tgz" \
		-H "x-rh-request_id: testtesttest" \
		-H "Authorization: Basic ${auth_header}" \
		https://${server}/api/ingress/v1/upload

sample-data:
	mkdir -p temp/reports
	mkdir -p temp/old_reports_temp
	tar -xvzf sample.tar.gz -C temp/old_reports_temp
	python scripts/change_uuids.py
	@NEW_FILENAME="sample_data_ready_$(shell date +%s).tar.gz"; \
	cd temp; COPYFILE_DISABLE=1 tar -zcvf $$NEW_FILENAME reports; \
	echo ""; \
	echo "The updated report was written to" temp/$$NEW_FILENAME; \
	echo ""; \
	rm -rf reports; \
	rm -rf old_reports_temp

runtest:
	pipenv run python -m pytest --cov=yuptoo tests/
	pipenv run flake8


# Generate the ubi.repo file from the specified BASE_IMAGE
# Usage: make generate-repo-file [BASE_IMAGE=<image>]
# Example: make generate-repo-file BASE_IMAGE=registry.access.redhat.com/ubi9/ubi:latest
#          make generate-repo-file (uses default BASE_IMAGE)
.PHONY: generate-repo-file
generate-repo-file:
	$(ensure_image)
	podman run --arch $(IMAGE_ARCH) -it $(BASE_IMAGE) cat /etc/yum.repos.d/ubi.repo > ubi.repo
	sed -i '' 's/ubi-9-appstream-source-rpms/ubi-9-for-x86_64-appstream-source-rpms/' ubi.repo
	sed -i '' 's/ubi-9-appstream-rpms/ubi-9-for-x86_64-appstream-rpms/' ubi.repo
	sed -i '' 's/ubi-9-baseos-source-rpms/ubi-9-for-x86_64-baseos-source-rpms/' ubi.repo
	sed -i '' 's/ubi-9-baseos-rpms/ubi-9-for-x86_64-baseos-rpms/' ubi.repo
	sed -i '' 's/\r$$//' ubi.repo
	sed -i '' '/\[.*x86_64.*\]/,/^\[/ s/enabled[[:space:]]*=[[:space:]]*0/enabled = 1/g' ubi.repo

# Generate rpms.in.yaml listing RPM packages installed via yum, dnf, or microdnf from CONTAINERFILE
# Usage: make generate-rpms-in-yaml [CONTAINERFILE=<path>]
# Example: make generate-rpms-in-yaml CONTAINERFILE=Containerfile
#          make generate-rpms-in-yaml (uses default CONTAINERFILE=Dockerfile)
.PHONY: generate-rpms-in-yaml
generate-rpms-in-yaml:
	@if [ ! -f "$(CONTAINERFILE)" ]; then \
		exit 1; \
	fi
	@if ! command -v $(AWK) >/dev/null 2>&1; then \
		exit 1; \
	fi; \
	packages=$$(grep -E '^(RUN[[:space:]]+)?(.*[[:space:]]*(yum|dnf|microdnf)[[:space:]]+.*install.*)' "$(CONTAINERFILE)" | \
		sed -E 's/\\$$//' | \
		$(AWK) '{ \
			start=0; \
			for (i=1; i<=NF; i++) { \
				if ($$i == "install") { start=1; continue } \
				if (start && $$i ~ /^[a-zA-Z0-9][a-zA-Z0-9_.+-]*$$/ && \
					$$i !~ /^-/ && $$i != "&&" && $$i != "clean" && $$i != "all" && $$i != "upgrade") { \
					print $$i \
				} \
				if ($$i == "&&") { start=0 } \
			} \
		}' | sort -u); \
	if [ -z "$$packages" ]; then \
		exit 1; \
	else \
		echo "packages: [$$(echo "$$packages" | tr '\n' ',' | sed -E 's/,/, /g; s/, $$//')]" > rpms.in.yaml; \
		echo "contentOrigin:" >> rpms.in.yaml; \
		echo "  repofiles: [\"./ubi.repo\"]" >> rpms.in.yaml; \
		echo "arches: [x86_64]" >> rpms.in.yaml; \
	fi

# Generate rpms.lock.yaml using rpm-lockfile-prototype
# Usage: make generate-rpm-lockfile [BASE_IMAGE=<image>]
# Example: make generate-rpm-lockfile BASE_IMAGE=registry.access.redhat.com/ubi9/ubi:latest
#          make generate-rpm-lockfile (uses default BASE_IMAGE)
.PHONY: generate-rpm-lockfile
generate-rpm-lockfile: rpms.in.yaml
	@curl -s https://raw.githubusercontent.com/konflux-ci/rpm-lockfile-prototype/refs/heads/main/Containerfile | \
	podman build --arch $(IMAGE_ARCH) -t localhost/rpm-lockfile-prototype -
	@container_dir=/work; \
	podman run --arch $(IMAGE_ARCH) --rm -v $${PWD}:$${container_dir} localhost/rpm-lockfile-prototype:latest --outfile=$${container_dir}/rpms.lock.yaml --image $(BASE_IMAGE) $${container_dir}/rpms.in.yaml
	@if [ ! -f rpms.lock.yaml ]; then \
		echo "Error: rpms.lock.yaml was not generated"; \
		exit 1; \
	fi

# Generate requirements.txt from Poetry or Pipenv lock files
# Usage: make generate-requirements-txt
# Example: make generate-requirements-txt
.PHONY: generate-requirements-txt
generate-requirements-txt:
	@if [ -f poetry.lock ]; then \
		poetry export --format requirements.txt --output requirements.txt; \
	elif [ -f Pipfile.lock ]; then \
		pipenv requirements > requirements.txt; \
	elif [ -f requirements.txt ]; then \
		exit 0; \
	else \
		echo "Error: Unable to generate requirements.txt file"; \
		exit 1; \
	fi
	@if [ ! -f requirements.txt ]; then \
		echo "Error: requirements.txt was not generated"; \
		exit 1; \
	fi

# Generate requirements-build.in from [build-system] in pyproject.toml
# Usage: make generate-requirements-build-in
# Example: make generate-requirements-build-in
.PHONY: generate-requirements-build-in
generate-requirements-build-in:
	@> requirements-build.in
	@if [ ! -f pyproject.toml ]; then \
		echo "Error: pyproject.toml not found"; \
		exit 1; \
	fi
	@if ! grep -q '^\[build-system\]' pyproject.toml; then \
		exit 0; \
	fi
	@requires=$$(sed -n '/^\[build-system\]/,/^\[/p' pyproject.toml | \
	grep 'requires[[:space:]]*=' | \
	sed 's/.*requires[[:space:]]*=[[:space:]]*\[\(.*\)\]/\1/' | \
	sed 's/"//g; s/,[[:space:]]*/\n/g' | \
	sed 's/^[[:space:]]*//; s/[[:space:]]*$$//; /^$$/d'); \
	if [ -z "$$requires" ]; then \
		exit 0; \
	fi; \
	> requirements-build.in; \
	for pkg in $$requires; do \
		if echo "$$pkg" | grep -q "=="; then \
			echo "$$pkg" >> requirements-build.in; \
		else \
			version=$$(curl -s "https://pypi.org/pypi/$$pkg/json" | \
			sed -n 's/.*"version":[[:space:]]*"\([^"]*\)".*/\1/p' | head -1); \
			if [ -z "$$version" ]; then \
				echo "Error: Failed to fetch version for $$pkg from PyPI"; \
				exit 1; \
			fi; \
			echo "$$pkg==$$version" >> requirements-build.in; \
		fi; \
	done
	@if [ ! -f .hermetic_builds/add_manual_build_dependencies.sh ] || [ ! -f .hermetic_builds/add_manual_build_dependencies.sh ]; then \
		echo "Error: Missing scripts in .hermetic_builds directory"; \
		exit 1; \
	fi
	.hermetic_builds/add_manual_build_dependencies.sh
	@if [ ! -f requirements-build.in ]; then \
		echo "Error: requirements-build.in was not generated"; \
		exit 1; \
	fi

# Generate requirements-build.txt using pip-tools and pybuild-deps
# Usage: make generate-requirements-build-txt [BASE_IMAGE=<image>]
# Example: make generate-requirements-build-txt BASE_IMAGE=registry.access.redhat.com/ubi9/ubi:latest
.PHONY: generate-requirements-build-txt
generate-requirements-build-txt:
	@if [ ! -f requirements.txt ]; then \
		echo "Error: requirements.txt not found"; \
		exit 1; \
	fi
	@if [ ! -f .hermetic_builds/prep_python_build_container_dependencies.sh ] || [ ! -f .hermetic_builds/generate_requirements_build.sh ]; then \
		echo "Error: Missing scripts in .hermetic_builds directory"; \
		exit 1; \
	fi
	@podman run --arch $(IMAGE_ARCH) -it -v "$$(pwd)":/var/tmp:rw --user 0:0 $(BASE_IMAGE) bash -c "/var/tmp/.hermetic_builds/prep_python_build_container_dependencies.sh && /var/tmp/.hermetic_builds/generate_requirements_build.sh"
	@if [ ! -f requirements-build.txt ]; then \
		echo "Error: requirements-build.txt was not generated"; \
		exit 1; \
	fi
