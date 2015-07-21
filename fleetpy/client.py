"""
Client Library for Fleetd

"""
import collections
import json
import logging
import os
from os import path

import requests
try:
    import requests_unixsocket
except ImportError:
    requests_unixsocket = None

from fleetpy import unit


LOGGER = logging.getLogger(__name__)

MACHINE = collections.namedtuple('Machine', ['id', 'ipaddr', 'metadata'])
MACHINE_STATE = collections.namedtuple('MachineState', ['id', 'ipaddr',
                                                        'metadata', 'unit',
                                                        'loaded', 'state',
                                                        'sub_state', 'hash'])
STATE = collections.namedtuple('State', ['machine', 'unit', 'loaded', 'state',
                                         'sub_state', 'hash'])


class _Adapter(object):

    GET_HEADERS = {'Accept': 'application/json',
                   'User-Agent': 'fleetpy/0.0'}
    PUT_HEADERS = {'Accept': 'application/json',
                   'Content-Type': 'application/json',
                   'User-Agent': 'fleetpy/0.0'}
    BASE_URI = 'fleet/v1'
    DEFAULT_ENDPOINT = 'unix:///var/run/fleet.sock'

    def __init__(self, endpoint):
        self._endpoint = endpoint or os.environ.get('FLEETCTL_ENDPOINT',
                                                    self.DEFAULT_ENDPOINT)
        if endpoint.startswith('unix://') and requests_unixsocket:
            self._session = requests_unixsocket.Session()
        else:
            self._session = requests.Session()

    def delete(self, request_path):
        return self._session.delete(self._build_url(request_path),
                                    headers=self.GET_HEADERS)

    def get(self, request_path, next_request_token=None):
        return self._session.get(self._build_url(request_path,
                                                 next_request_token),
                                 headers=self.GET_HEADERS)

    def put(self, request_path, body):
        return self._session.put(self._build_url(request_path),
                                 json.dumps(body),
                                 headers=self.PUT_HEADERS)

    def _build_url(self, request_path, next_page_token=None):
        url = path.join(self._endpoint, self.BASE_URI, request_path)
        if not next_page_token:
            return url
        return '{0}?nextPageToken={1}'.format(url, next_page_token)


class Client(object):
    """Create a Fleet API Client

    :param str endpoint: Base endpoint URL for accessing Fleet

    """
    def __init__(self, endpoint=None):
        self._adapter = _Adapter(endpoint)

    def machines(self):
        """Query Fleet returning a list of machines as namedtuples:

            Machine(id, ipaddr, metadata)

        :rtype: list

        """
        return self._list_machines()

    def state(self, full=False, unit_name=None):
        """

        :rtype: list

        """
        states = self._list_states()
        if unit_name:
            states = [s for s in states if s.unit == unit_name]
        if not full:
            return states
        machines, values = {}, []
        for machine in self._list_machines():
            machines[machine.id] = {'ipaddr': machine.ipaddr,
                                    'metadata': machine.metadata}
        for state in states:
            values.append(MACHINE_STATE(state.machine,
                                        machines[state.machine]['ipaddr'],
                                        machines[state.machine]['metadata'],
                                        state.unit, state.loaded,
                                        state.state, state.sub_state,
                                        state.hash))
        return values

    def unit(self, name, version=None, from_str=None, from_file=None):
        """

        :param str name:
        :param str version:
        :param str from_str:
        :param str from_file:
        :type: fleetpy.unit.Unit

        """
        value = unit.Unit(self._adapter, name, version)
        if from_str:
            value.read_string(value)
        elif from_file:
            value.read_file(from_file)
        return value

    def units(self):
        """

        :rtype: list

        """
        return self._list_units()

    def _list_machines(self, next_page_token=None):
        machines = list()
        response = self._adapter.get('machines', next_page_token)
        if response.status_code == 200:
            data = response.json()
            for row in data.get('machines'):
                machines.append(MACHINE(row['id'],
                                        row['primaryIP'],
                                        row['metadata']))
            if 'nextPageToken' in data:
                LOGGER.debug('Retrieving next page of results')
                machines += self._list_machines(data['next_page_token'])
        return machines

    def _list_states(self, next_page_token=None):
        states = []
        response = self._adapter.get('state', next_page_token)
        if response.status_code == 200:
            data = response.json()
            for row in data.get('states', []):
                states.append(STATE(row['machineID'],
                                    row['name'],
                                    row['systemdLoadState'] == 'loaded',
                                    row['systemdActiveState'],
                                    row['systemdSubState'],
                                    row['hash']))
            if 'nextPageToken' in data:
                LOGGER.debug('Retrieving next page of results')
                states += self._list_states(data['next_page_token'])
        return states

    def _list_units(self, next_page_token=None):
        units = list()
        response = self._adapter.get('units', next_page_token)
        if response.status_code == 200:
            data = response.json()
            for row in data.get('units'):
                value = unit.Unit(self._adapter,
                                  row['name'])
                value.set_desired_state(row['desiredState'])
                value.set_state(row['currentState'])
                for option in row['options']:
                    value.add_option(option['section'],
                                     option['name'],
                                     option['value'])
                units.append(value)
            if 'nextPageToken' in data:
                LOGGER.debug('Retrieving next page of results')
                units += self._list_units(data['next_page_token'])
        return units
