from yuptoo.processor.abstract_processor import AbstractProcessor
from yuptoo.processor.report_consumer import ReportConsumer
from yuptoo.processor.report_processor import ReportProcessor
from yuptoo.processor.report_slice_processor import ReportSliceProcessor
from yuptoo.processor.garbage_collection import GarbageCollector
import threading


def abstract_processor():
    processor = AbstractProcessor()
    processor.run()

def report_consumer():
    processor = ReportConsumer()
    processor.run()

def report_processor():
    processor = ReportProcessor()
    processor.run()

def report_slice_processor():
    processor = ReportSliceProcessor()
    processor.run()

def garbage_collector():
    collector = GarbageCollector()
    collector.run()


if __name__ == "__main__":
    # Start running processors in different threads
    process_abstract_processor = threading.Thread(name='abstract-processor', target=abstract_processor)
    process_report_consumer = threading.Thread(name='report-consumer', target=report_consumer)
    process_report_processor = threading.Thread(name='report-processor', target=report_processor)
    process_report_slice_processor = threading.Thread(name='report-slice-processor', target=report_slice_processor)
    process_garbage_collector = threading.Thread(name='garbage-collector', target=garbage_collector)
    process_abstract_processor.start()
    process_report_consumer.start()
    process_report_processor.start()
    process_report_slice_processor.start()
    process_garbage_collector.start()
    # Wait until the thread terminates
    process_abstract_processor.join()
    process_report_consumer.join()
    process_report_processor.join()
    process_report_slice_processor.join()
    process_garbage_collector.join()

