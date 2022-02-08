from yuptoo.processor.report_consumer import ReportConsumer
import threading


def report_consumer():
    report_consumer = ReportConsumer()
    report_consumer.run()


if __name__ == "__main__":
    # Start running processor in different threads
    report_consumer_thread = threading.Thread(name='report-consumer', target=report_consumer)
    report_consumer_thread.start()
    # Wait until the thread terminates
    report_consumer_thread.join()
