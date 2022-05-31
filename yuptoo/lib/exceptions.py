class FailDownloadException(Exception):
    """Use to report download errors that should not be retried."""

    pass


class FailExtractException(Exception):
    """Use to report extract errors that should not be retried."""

    pass


class KafkaMsgHandlerError(Exception):
    """Kafka msg handler error."""

    pass


class QPCReportException(Exception):
    """Use to report errors during qpc report processing."""

    pass


class QPCKafkaMsgException(Exception):
    """Use to report errors with kafka message.
    Used when we think the kafka message is useful
    in debugging.  Error with external services
    (connected via kafka).
    """

    pass


class QPCMsgValidationException(Exception):
    """Use to report validation errors with kafka message."""

    pass
