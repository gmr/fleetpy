"""

"""
import collections
import logging
from os import path

LOGGER = logging.getLogger(__name__)

OPTION = collections.namedtuple('Option', ['section', 'name', 'value'])
VALID_STATES = ['inactive', 'loaded', 'launched']


class Unit(object):

    def __init__(self, adapter, name, version=None):
        self._adapter = adapter
        if name.endswith('.service'):
            name = name[0:-8]
        if '@' in name:
            name, value = name.split('@')
        self._name = name
        self._options = []
        self._version = version
        self._desired_state = 'inactive'
        self._state = None

    def __dict__(self):
        return {'name': self.name,
                'desiredState': self._desired_state,
                'options': self.options()}

    def add_option(self, section, name, value):
        self._options.append(OPTION(section, name, value))

    def as_dict(self):
        return self.__dict__()

    @property
    def desired_state(self):
        return self._desired_state

    def destroy(self):
        result = self._adapter.delete('units/{0}'.format(self.name))
        return result.status_code == 204

    @property
    def name(self):
        if not self._version:
            return '{0}.service'.format(self._name)
        return '{0}@{1}.service'.format(self._name, self._version)

    def read_file(self, filename):
        if not path.exists(filename):
            raise ValueError('File not found: {0}'.format(filename))
        with open(filename, 'r') as handle:
            self._parse(handle.read())

    def read_string(self, value):
        self._parse(value)

    def options(self):
        return [dict(vars(option)) for option in self._options]

    def refresh(self):
        result = self._adapter.get('units/{0}'.format(self.name))
        if result.status_code == 200:
            value = result.json()
            self._state = value.get('currentState', self._state)
            self._desired_state = value.get('desiredState', self._desired_state)
            if value.get('options'):
                value['options'] = []
            for option in value['options']:
                value.add_option(option['section'],
                                 option['name'],
                                 option['value'])
            return True
        return False

    def set_desired_state(self, state):
        if state not in VALID_STATES:
            raise ValueError('Invalid state: {0}'.format(state))
        self._desired_state = state

    def set_name(self, name):
        self._name = name

    def set_state(self, state):
        if state not in VALID_STATES:
            raise ValueError('Invalid state: {0}'.format(state))
        self._state = state

    def set_version(self, version):
        self._version = version

    @property
    def state(self):
        return self._state

    def start(self):
        self._desired_state = 'launched'
        result = self._adapter.put('units/{0}'.format(self.name),
                                   {'desiredState': self._desired_state})
        return result.status_code == 204

    def stop(self):
        self._desired_state = 'inactive'
        result = self._adapter.put('units/{0}'.format(self.name),
                                   {'desiredState': self._desired_state})
        return result.status_code == 204

    def submit(self):
        self._desired_state = 'loaded'
        result = self._adapter.put('units/{0}'.format(self.name),
                                   self.as_dict())
        LOGGER.debug('Result: (%s) %s', result.status_code, result.content)
        return result.status_code == 201

    def unload(self):
        self._desired_state = 'inactive'

    def _parse(self, value_in):
        self._options = []
        key, section, value = None, None, ''
        for line in value_in.split('\n'):
            if not line.strip():
                self._options.append(OPTION(section, key, '\n'.join(value)))
                key, value = None, None
                continue
            if line.startswith('[') and line.endswith(']'):
                section = line[1:-1]
                continue
            if line.startswith(' ') or '=' not in line:
                value.append(line.strip())
                continue
            parts = line.strip().split('=', 1)
            if parts:
                # Add the previous value
                if key and value:
                    self._options.append(OPTION(section, key, '\n'.join(value)))

                # Handle the next iteration
                key = parts.pop(0)
                value = parts
        if key and value:
            self._options.append(OPTION(section, key, '\n'.join(value)))
