from confluent_kafka import Producer


class ReportProcessor:
    def __init__(self):
        self.producer = Producer({
            'bootstrap.servers': INSIGHTS_KAFKA_ADDRESS
        })

    def download_report()
    def extract_and_create_slices(report_tar)
    def create_report_slice(self, options)
    def deduplicate_reports()
    def validate_report_details()
    def send_confirmation(self, file_hash)
    def validate_metadata_file(self, tar, metadata)


