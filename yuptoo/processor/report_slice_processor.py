from confluent_kafka import Producer


class ReportSliceProcessor:
    def __init__(self):
        self.producer = Producer({
            'bootstrap.servers': INSIGHTS_KAFKA_ADDRESS,
            'max.request.size': KAFKA_PRODUCER_OVERRIDE_MAX_REQUEST_SIZE
        })

    def validate_report_details()
    def upload_to_host_inventory_via_kafka()
    def generate_upload_candidates()
    def transform_tags(self, host: dict)
    def remove_display_name(self, host: dict)
    def remove_empty_ip_addresses(self, host: dict)
    def transform_mac_addresses(self, host: dict)
    def is_valid_uuid(uuid)
    def remove_invalid_bios_uuid(self, host)
    def match_regex_and_find_os_details(self, os_release)
    def transform_os_release(self, host: dict)
    def transform_os_kernel_version(self, host: dict)
    def transform_network_interfaces(self, host: dict)
    def transform_ipv6(nic: dict, increment_counts: dict)
    def transform_mtu(nic: dict, increment_counts: dict)
    def remove_installed_packages(self, host: dict)
    def transform_single_host(self, host: dict)
    def upload_to_host_inventory_via_kafka(self, hosts)

