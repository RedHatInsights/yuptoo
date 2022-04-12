def format_message(prefix, message, account_number=None,
                   report_platform_id=None):
    """Format log messages in a consistent way.
    :param prefix: (str) A meaningful prefix to be displayed in all caps.
    :param message: (str) A short message describing the state
    :param account_number: (str) The account sending the report.
    :param report_platform_id: (str) The qpc report id.
    :returns: (str) containing formatted message
    """
    if not report_platform_id and not account_number:
        actual_message = 'Report %s - %s' % (prefix, message)
    elif account_number and not report_platform_id:
        actual_message = 'Report(account=%s) %s - %s' % (account_number, prefix, message)
    else:
        actual_message = 'Report(account=%s, report_platform_id=%s) %s - %s' % (
            account_number,
            report_platform_id, prefix,
            message)

    return actual_message
