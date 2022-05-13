metadata={"branch_info": {"remote_branch": -1, "remote_leaf": -1}, "bios_uuid": "25d6ad97-60fa-4d3e-b2cc-4aa437c28f71", "ip_addresses": ["10.74.255.52", "2620:52:0:4af8:21a:4aff:fe00:a8a"], "fqdn": "vm255-52.gsslab.pnq2.redhat.com", "mac_addresses": ["00:1a:4a:00:0a:8a", "00:00:00:00:00:00"], "satellite_id": -1, "subscription_manager_id": "7846d4fa-6fcc-4b84-aa13-5f12e588ecca", "insights_id": "1d42f242-3828-4a00-8009-c67656c86a51", "machine_id": "25d6ad97-60fa-4d3e-b2cc-4aa437c28f71"}
identity={"identity": {"account_number": "sysaccount", "type": "System", "auth_type": "cert-auth", "system": {"cn": "1b36b20f-7fa0-4454-a6d2-008294e06378", "cert_type": "system"}, "internal": {"org_id": "3340851", "auth_time": 6300}}}
b64_identity=$(shell echo '${identity}' | base64 -w 0 -)
ifdef env
	short_env=$(shell echo '${env}' | cut -d'-' -f2)
	server=$(shell oc get clowdenvironments env-ephemeral-${short_env} -o=jsonpath='{.status.hostname}')
	username=$(shell oc get secret env-ephemeral-${short_env}-keycloak -n ephemeral-${short_env} -o=jsonpath='{.data.defaultUsername}' | base64 -d)
	password=$(shell oc get secret env-ephemeral-${short_env}-keycloak -n ephemeral-${short_env} -o=jsonpath='{.data.defaultPassword}' | base64 -d)
	auth_header=$(shell echo -n '${username}:${password}' | base64)
endif

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