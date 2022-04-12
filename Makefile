local-upload-data:
	curl -vvvv -F "upload=@$(file);type=application/vnd.redhat.qpc.$(basename $(basename $(notdir $(file))))+tgz" \
		-H "x-rh-identity: eyJpZGVudGl0eSI6IHsiYWNjb3VudF9udW1iZXIiOiAic3lzYWNjb3VudCIsICJ0eXBlIjogIlN5c3RlbSIsICJhdXRoX3R5cGUiOiAiY2VydC1hdXRoIiwgInN5c3RlbSI6IHsiY24iOiAiMWIzNmIyMGYtN2ZhMC00NDU0LWE2ZDItMDA4Mjk0ZTA2Mzc4IiwgImNlcnRfdHlwZSI6ICJzeXN0ZW0ifSwgImludGVybmFsIjogeyJvcmdfaWQiOiAiMzM0MDg1MSIsICJhdXRoX3RpbWUiOiA2MzAwfX19" \
		-H "x-rh-request_id: testtesttest" \
		localhost:3000/api/ingress/v1/upload