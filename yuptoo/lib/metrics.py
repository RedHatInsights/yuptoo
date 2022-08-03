from prometheus_client import Counter

archive_downloaded_success = Counter(
    "yuptoo_archive_downloaded_success",
    "Total number of archives downloaded successfully"
)

archive_failed_to_download = Counter(
    "yuptoo_archive_failed_to_download",
    "Total number of archives that failed to download",
    ["org_id"]
)

extract_report_slices_failures = Counter(
    "yuptoo_extract_report_slices_failures",
    "Total number of failures while extracting report slice",
    ["org_id"]
)

report_processing_exceptions = Counter(
    "yuptoo_report_processing_exceptions",
    "Total number of exceptions while processing report",
    ["org_id"]
)

host_uploaded = Counter(
    "yuptoo_host_uploaded",
    "Total number of hosts uploaded to inventory",
    ["org_id"]
)

host_upload_failures = Counter(
    "yuptoo_host_upload_failures",
    "Total number of hosts failed to upload",
    ["org_id"]
)

kafka_failures = Counter(
    "yuptoo_kafka_failures",
    "Total number of kafka failures while processing messages",
    ["org_id"]
)

incoming_hosts_counter = Counter(
    'yupana_incoming_hosts_counter',
    'Total number of hosts in report as per source',
    ["org_id", "source"]
)
