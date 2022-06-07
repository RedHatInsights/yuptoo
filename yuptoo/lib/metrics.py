from prometheus_client import Counter

archive_downloaded_success = Counter(
    "yuptoo_archive_downloaded_success",
    "Total number of archives downloaded successfully"
)

archive_failed_to_download = Counter(
    "yuptoo_archive_failed_to_download",
    "Total number of archives that failed to download",
    ["account_number"]
)

report_extract_failures = Counter(
    "yuptoo_report_extract_failures",
    "Total number of failures while processing report",
    ["account_number"]
)

kafka_failures = Counter(
    "yuptoo_kafka_failures",
    "Total number of kafka failures while processing messages",
    ["account_number"]
)

HOSTS_COUNTER = Counter(
    'yupana_hosts_count',
    'Total number of hosts uploaded',
    ['source']
)
