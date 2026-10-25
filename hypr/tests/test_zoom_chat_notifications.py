"""Run with python3 -B -m unittest discover -s hypr/tests."""
from collections import deque
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parents[1] / 'scripts'))
import zoom_chat_accessibility as accessibility


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parents[1] / 'scripts' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


popup = load('zoom_popup', 'zoom-chat-popup.py')
events = load('zoom_events', 'zoom-chat-notifications.py')


class EventDelivery(unittest.TestCase):
    def setUp(self):
        self.listener = events.Notifications.__new__(events.Notifications)
        self.listener.owners = {':1.25': 123}
        self.listener.pending = deque()
        self.listener.busy = False
        self.listener.reader = Mock()

    def arrival(self, text='From A&B to Everyone\n<hello>\nsecond line', sender=':1.25'):
        parameters = SimpleNamespace(unpack=lambda: ('accessible-name', 0, 0, text))
        self.listener.on_event(None, sender, '/label', None, None, parameters)

    def test_event_retains_exact_text_while_queries_are_busy(self):
        self.listener.busy = True
        self.arrival()
        self.listener.reader.query.assert_not_called()
        self.assertEqual(self.listener.pending[0]['contents']['message'], '<hello>\nsecond line')

    def test_unrelated_and_incomplete_events_do_not_notify(self):
        self.arrival(sender=':1.99')
        self.arrival(text='01:30')
        self.arrival(text='From A to Everyone\n')
        self.assertFalse(self.listener.pending)

    def test_verified_event_delivers_escaped_sender_and_full_message(self):
        self.arrival()
        with patch.object(self.listener, 'verify', return_value=True), patch.object(events.subprocess, 'run') as notify:
            self.listener.drain()
        self.assertEqual(notify.call_args.args[0][-1], '<b>A&amp;B</b>: &lt;hello&gt;\nsecond line')
        self.assertFalse(self.listener.pending)

    def test_failed_query_retries_without_losing_captured_message(self):
        self.arrival()
        with patch.object(self.listener, 'verify', side_effect=[False, True]), patch.object(events.subprocess, 'run') as notify:
            self.listener.drain()
            self.assertEqual(len(self.listener.pending), 1)
            notify.assert_not_called()
            self.listener.pending[0]['retry'] = 0
            self.listener.drain()
            notify.assert_called_once()

    def test_expired_unverified_event_never_emits_generic_alert(self):
        self.arrival()
        self.listener.pending[0]['received'] -= 20
        with patch.object(self.listener, 'verify', return_value=False), patch.object(events.subprocess, 'run') as notify:
            self.listener.drain()
            notify.assert_not_called()
        self.assertFalse(self.listener.pending)

    def test_two_identical_message_events_are_both_delivered(self):
        self.arrival()
        self.arrival()
        with patch.object(self.listener, 'verify', return_value=True), patch.object(events.subprocess, 'run') as notify:
            self.listener.drain()
            self.listener.drain()
            self.assertEqual(notify.call_count, 2)

    def test_closed_meeting_discards_queued_message(self):
        self.arrival()
        self.listener.owners.clear()
        with patch.object(self.listener, 'verify') as verify, patch.object(events.subprocess, 'run') as notify:
            self.listener.drain()
            verify.assert_not_called()
            notify.assert_not_called()

    def test_reused_native_window_cannot_bypass_meeting_identity(self):
        ref = (':1.25', '/label')
        self.listener.verified = {ref: {'xid': 1, 'meeting': '0xa', 'meeting_id': 'old'}}
        self.listener.frames = {}
        self.listener.x11 = Mock()
        self.listener.reader.query.return_value = {}
        with patch.object(self.listener, 'native_toast', return_value={'meeting': '0xa', 'meeting_id': 'new'}):
            self.assertFalse(self.listener.verify(ref, 123))
        self.assertNotIn(ref, self.listener.verified)


class Routing(unittest.TestCase):
    def test_routing_needs_no_accessibility_query_or_notification(self):
        with patch.object(popup, 'classify', return_value={'meeting': {'address': '0x2'}}), \
             patch.object(popup.subprocess, 'run') as run, \
             patch.object(popup.sys, 'argv', ['popup', '0x1', '99']):
            popup.main()
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0][:2], ['hyprctl', 'eval'])
        self.assertIn('hyprlifeZoomPopupClassified', run.call_args.args[0][2])


class DirectReader(unittest.TestCase):
    def test_multiline_message_is_preserved(self):
        self.assertEqual(accessibility.parse_text('From A & B to Everyone\r\nfirst\r\nsecond'),
                         {'sender': 'A & B', 'recipient': 'Everyone', 'message': 'first\nsecond'})

    def test_only_matching_process_family_is_read(self):
        reader = accessibility.Reader.__new__(accessibility.Reader)
        registry = ('org.a11y.atspi.Registry', '/org/a11y/atspi/accessible/root')
        zoom, other = ('zoom', '/root'), ('other', '/root')
        with patch.object(reader, 'children', return_value={registry: [zoom, other]}), \
             patch.object(reader, 'batch', return_value={zoom: (123,), other: (456,)}), \
             patch.object(accessibility, 'same_process_family', side_effect=lambda app, pid: app == pid):
            self.assertEqual(reader.applications(123), [zoom])


if __name__ == '__main__':
    unittest.main()
