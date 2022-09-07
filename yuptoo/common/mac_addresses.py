"""This file includes helper methods related to mac_addresses."""
import copy

TRANSFORMED_DICT = dict({'removed': [], 'modified': [], 'missing_data': []})


def _remove_mac_addrs_for_omitted_nics(
    host: dict, mac_addresses_to_omit: list,
        transformed_obj=copy.deepcopy(TRANSFORMED_DICT)):
    """Remove mac_addresses for omitted nics."""

    mac_addresses = host.get('mac_addresses')
    len_of_mac_addrs_to_omit = len(mac_addresses_to_omit)
    if mac_addresses and len_of_mac_addrs_to_omit > 0:
        host['mac_addresses'] = list(
            set(mac_addresses) - set(mac_addresses_to_omit))
        if not host['mac_addresses']:
            del host['mac_addresses']
        transformed_obj['removed'].append(
            'omit mac_addresses for omitted nics')
    return [host, transformed_obj]
