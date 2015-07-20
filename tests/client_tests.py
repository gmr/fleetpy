try:
    import unittest2 as unittest
except ImportError:
    import unittest

import httmock

from fleetpy import client


class TestCase(unittest.TestCase):

    ENDPOINT = 'http://localhost:49153'

    def setUp(self):
        self.obj = client.Client(self.ENDPOINT)


class BuildURLTests(TestCase):

    def test_url_with_path(self):
        self.assertEqual(self.obj._adapter._build_url('machines'),
                         'http://localhost:49153/fleet/v1/machines')


class ListMachinesTests(TestCase):

    RESPONSE = (b'{"machines":[{"id":"0661525c22db49a4a4cba40c5a713b7f","metad'
                b'ata":{"region":"us-east-1","service":"discovery"},"primaryIP'
                b'":"10.100.9.154"},{"id":"73407c4b2d464b9b91c409b15fed359f","'
                b'metadata":{"region":"us-east-1","service":"discovery"},"prim'
                b'aryIP":"10.100.141.117"},{"id":"fde1534d336848c786edcc122e78'
                b'c592","metadata":{"service":"discovery"},"primaryIP":"10.100'
                b'.90.164"}]}')

    def test_200_response(self):

        @httmock.all_requests
        def response_content(_url, _request):
            return {'status_code': 200, 'content': self.RESPONSE}

        expectation = [client.MACHINE(id='0661525c22db49a4a4cba40c5a713b7f',
                                      ipaddr='10.100.9.154',
                                      metadata={'region': 'us-east-1',
                                                'service': 'discovery'}),
                       client.MACHINE(id='73407c4b2d464b9b91c409b15fed359f',
                                      ipaddr='10.100.141.117',
                                      metadata={'region': 'us-east-1',
                                                'service': 'discovery'}),
                       client.MACHINE(id='fde1534d336848c786edcc122e78c592',
                                      ipaddr='10.100.90.164',
                                      metadata={'service': 'discovery'})]

        with httmock.HTTMock(response_content):
            machines = self.obj.machines()
            self.assertListEqual(machines, expectation)

