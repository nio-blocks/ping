from unittest.mock import patch
from nio import Signal
from nio.testing.block_test_case import NIOBlockTestCase
from ..ping_block import Ping


class TestPing(NIOBlockTestCase):

    @patch('subprocess.call')
    @patch('time.monotonic')
    def test_ping_no_timeout(self, mock_monotonic, mock_call):
        """Every signal pings a host"""
        # two signals in this test, the second host will fail
        mock_call.side_effect = [0, 1]
        # set up some mocked times
        # first two values are a successful round trip,
        # second two values timed out
        mock_monotonic.side_effect = [0, 0.123321, 1.0, 4.14]
        blk = Ping()
        self.configure_block(blk, {
            'hostname': '{{ $host }}',
            'enrich': {'exclude_existing': False},
        })
        blk.start()
        blk.process_signals([
            Signal({'host': 'foo'}),
            Signal({'host': 'bar'}),
        ])
        blk.stop()
        self.assertEqual(mock_call.call_count, 2)
        self.assertEqual(
            mock_call.call_args_list[0][0],
            ('ping -c 1 foo',)
        )
        self.assertEqual(
            mock_call.call_args_list[1][0],
            ('ping -c 1 bar',)
        )
        self.assert_last_signal_list_notified([
            Signal({
                'ping_response': True,
                'ping_time_ms': 123.3,
                'host': 'foo',
            }),
            Signal({
                'ping_response': False,
                'ping_time_ms': None,
                'host': 'bar',
            }),
        ])

    @patch('subprocess.call')
    @patch('time.monotonic')
    def test_ping_with_timeout(self, mock_monotonic, mock_call):
        """ If they provide a timeout add the -W flag """
        mock_call.return_value = 0
        mock_monotonic.side_effect = [0, 0.123321]
        blk = Ping()
        self.configure_block(blk, {
            'hostname': '{{ $host }}',
            'timeout': 3.14,
            'enrich': {'exclude_existing': False},
        })
        blk.start()
        blk.process_signals([
            Signal({'host': 'foo'}),
        ])
        blk.stop()
        self.assertEqual(mock_call.call_count, 1)
        self.assertEqual(
            mock_call.call_args_list[0][0],
            ('ping -c 1 -W 3.14 foo',)
        )
        self.assert_last_signal_list_notified([
            Signal({
                'ping_response': True,
                'ping_time_ms': 123.3,
                'host': 'foo',
            })
        ])
