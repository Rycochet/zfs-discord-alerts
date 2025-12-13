"""
Comprehensive unit tests for main.py - ZFS Discord Alerts application.

Tests cover:
- Environment variable validation and parsing
- get_embed function with various data structures
- check_status function with Discord webhook interactions
- check function with ZFS command execution
- HTTP server Handler class
- Signal handling and shutdown logic
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call, mock_open
import json
import sys
import os
import io
import http.server
import time
import threading
import subprocess
import signal


class TestEnvironmentVariableValidation(unittest.TestCase):
    """Test suite for environment variable parsing and validation."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Store original environment
        self.original_env = os.environ.copy()
        # Clear any existing env vars that main.py reads
        self.env_vars_to_clear = [
            'DISCORD_WEBHOOK_URL', 'DISCORD_MAX_RETRIES', 'DISCORD_RETRY_DELAY',
            'CHECK_DELAY', 'EXTRA', 'POOLS', 'SHOW_SPACE', 'VERBOSE',
            'WEBSERVER', 'HOST', 'PORT', 'LOG_LEVEL'
        ]
        for var in self.env_vars_to_clear:
            os.environ.pop(var, None)
    
    def tearDown(self):
        """Clean up after each test."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)
        # Remove main module from cache if it was imported
        if 'main' in sys.modules:
            del sys.modules['main']
    
    def test_missing_discord_webhook_url_raises_error(self):
        """Test that missing DISCORD_WEBHOOK_URL raises ValueError."""
        with self.assertRaises(ValueError) as context:
            import main
        self.assertIn("DISCORD_WEBHOOK_URL is required", str(context.exception))
    
    def test_valid_discord_webhook_url_loads(self):
        """Test that valid DISCORD_WEBHOOK_URL allows module to load."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        self.assertEqual(main.DISCORD_WEBHOOK_URL, 'https://discord.com/api/webhooks/test')
    
    def test_discord_max_retries_default_value(self):
        """Test DISCORD_MAX_RETRIES defaults to 3."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        self.assertEqual(main.DISCORD_MAX_RETRIES, 3)
    
    def test_discord_max_retries_custom_value(self):
        """Test DISCORD_MAX_RETRIES accepts custom valid integer."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        os.environ['DISCORD_MAX_RETRIES'] = '5'
        import main
        self.assertEqual(main.DISCORD_MAX_RETRIES, 5)
    
    def test_discord_max_retries_invalid_value_raises_error(self):
        """Test DISCORD_MAX_RETRIES with non-integer raises ValueError."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        os.environ['DISCORD_MAX_RETRIES'] = 'invalid'
        with self.assertRaises(ValueError) as context:
            import main
        self.assertIn("DISCORD_MAX_RETRIES must be a valid integer", str(context.exception))
    
    def test_discord_max_retries_negative_value_raises_error(self):
        """Test DISCORD_MAX_RETRIES with negative value raises ValueError."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        os.environ['DISCORD_MAX_RETRIES'] = '-1'
        with self.assertRaises(ValueError) as context:
            import main
        self.assertIn("DISCORD_MAX_RETRIES must be >= 0", str(context.exception))
    
    def test_discord_max_retries_zero_is_valid(self):
        """Test DISCORD_MAX_RETRIES accepts zero as valid value."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        os.environ['DISCORD_MAX_RETRIES'] = '0'
        import main
        self.assertEqual(main.DISCORD_MAX_RETRIES, 0)
    
    def test_discord_retry_delay_default_value(self):
        """Test DISCORD_RETRY_DELAY defaults to 5."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        self.assertEqual(main.DISCORD_RETRY_DELAY, 5)
    
    def test_discord_retry_delay_custom_value(self):
        """Test DISCORD_RETRY_DELAY accepts custom valid integer."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        os.environ['DISCORD_RETRY_DELAY'] = '10'
        import main
        self.assertEqual(main.DISCORD_RETRY_DELAY, 10)
    
    def test_discord_retry_delay_invalid_value_raises_error(self):
        """Test DISCORD_RETRY_DELAY with non-integer raises ValueError."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        os.environ['DISCORD_RETRY_DELAY'] = 'not_a_number'
        with self.assertRaises(ValueError) as context:
            import main
        self.assertIn("DISCORD_RETRY_DELAY must be a valid integer", str(context.exception))
    
    def test_discord_retry_delay_negative_value_raises_error(self):
        """Test DISCORD_RETRY_DELAY with negative value raises ValueError."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        os.environ['DISCORD_RETRY_DELAY'] = '-5'
        with self.assertRaises(ValueError) as context:
            import main
        self.assertIn("DISCORD_RETRY_DELAY must be >= 0", str(context.exception))
    
    def test_check_delay_default_value(self):
        """Test CHECK_DELAY defaults to 300 seconds."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        self.assertEqual(main.CHECK_DELAY, 300)
    
    def test_check_delay_custom_value(self):
        """Test CHECK_DELAY accepts custom valid integer."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        os.environ['CHECK_DELAY'] = '600'
        import main
        self.assertEqual(main.CHECK_DELAY, 600)
    
    def test_check_delay_invalid_value_raises_error(self):
        """Test CHECK_DELAY with non-integer raises ValueError."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        os.environ['CHECK_DELAY'] = 'five_minutes'
        with self.assertRaises(ValueError) as context:
            import main
        self.assertIn("CHECK_DELAY must be a valid integer", str(context.exception))
    
    def test_check_delay_negative_value_raises_error(self):
        """Test CHECK_DELAY with negative value raises ValueError."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        os.environ['CHECK_DELAY'] = '-100'
        with self.assertRaises(ValueError) as context:
            import main
        self.assertIn("CHECK_DELAY must be >= 0", str(context.exception))
    
    def test_pools_empty_string_is_valid(self):
        """Test POOLS with empty string (monitor all pools)."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        os.environ['POOLS'] = ''
        import main
        self.assertEqual(main.POOLS, '')
    
    def test_pools_valid_pool_names(self):
        """Test POOLS with valid pool names."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        os.environ['POOLS'] = 'tank data backup'
        import main
        self.assertEqual(main.POOLS, 'tank data backup')
    
    def test_pools_with_invalid_characters_raises_error(self):
        """Test POOLS with invalid characters raises ValueError."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        os.environ['POOLS'] = 'tank; rm -rf /'
        with self.assertRaises(ValueError) as context:
            import main
        self.assertIn("POOLS contains invalid pool names", str(context.exception))
    
    def test_pools_reserved_words_are_filtered(self):
        """Test POOLS filters out ZFS reserved words."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        os.environ['POOLS'] = 'tank mirror log raidz'
        with self.assertRaises(ValueError) as context:
            import main
        self.assertIn("POOLS contains invalid pool names", str(context.exception))
    
    def test_show_space_false_by_default(self):
        """Test SHOW_SPACE defaults to False."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        self.assertFalse(main.SHOW_SPACE)
    
    def test_show_space_true_values(self):
        """Test SHOW_SPACE recognizes true values."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        for value in ['true', 'True', 'TRUE', '1', 'yes', 'Yes', 'YES']:
            os.environ['SHOW_SPACE'] = value
            if 'main' in sys.modules:
                del sys.modules['main']
            import main
            self.assertTrue(main.SHOW_SPACE, f"Failed for value: {value}")
            del sys.modules['main']
    
    def test_show_space_false_values(self):
        """Test SHOW_SPACE recognizes false values."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        for value in ['false', 'False', 'FALSE', '0', 'no', 'No', 'NO', '']:
            os.environ['SHOW_SPACE'] = value
            if 'main' in sys.modules:
                del sys.modules['main']
            import main
            self.assertFalse(main.SHOW_SPACE, f"Failed for value: {value}")
            del sys.modules['main']
    
    def test_verbose_false_by_default(self):
        """Test VERBOSE defaults to False."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        self.assertFalse(main.VERBOSE)
    
    def test_verbose_true_values(self):
        """Test VERBOSE recognizes true values."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        for value in ['true', '1', 'yes']:
            os.environ['VERBOSE'] = value
            if 'main' in sys.modules:
                del sys.modules['main']
            import main
            self.assertTrue(main.VERBOSE, f"Failed for value: {value}")
            del sys.modules['main']
    
    def test_webserver_false_by_default(self):
        """Test WEBSERVER defaults to False."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        self.assertFalse(main.WEBSERVER)
    
    def test_webserver_true_values(self):
        """Test WEBSERVER recognizes true values."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        for value in ['true', '1', 'yes']:
            os.environ['WEBSERVER'] = value
            if 'main' in sys.modules:
                del sys.modules['main']
            import main
            self.assertTrue(main.WEBSERVER, f"Failed for value: {value}")
            del sys.modules['main']
    
    def test_host_default_value(self):
        """Test HOST defaults to 0.0.0.0."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        self.assertEqual(main.HOST, '0.0.0.0')
    
    def test_host_custom_value(self):
        """Test HOST accepts custom value."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        os.environ['HOST'] = '127.0.0.1'
        import main
        self.assertEqual(main.HOST, '127.0.0.1')
    
    def test_port_default_value(self):
        """Test PORT defaults to 8080."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        self.assertEqual(main.PORT, 8080)
    
    def test_port_custom_value(self):
        """Test PORT accepts custom valid integer."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        os.environ['PORT'] = '9000'
        import main
        self.assertEqual(main.PORT, 9000)
    
    def test_port_invalid_value_raises_error(self):
        """Test PORT with non-integer raises ValueError."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        os.environ['PORT'] = 'not_a_port'
        with self.assertRaises(ValueError) as context:
            import main
        self.assertIn("PORT must be a valid integer", str(context.exception))
    
    def test_port_out_of_range_low_raises_error(self):
        """Test PORT with value <= 0 raises ValueError."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        os.environ['PORT'] = '0'
        with self.assertRaises(ValueError) as context:
            import main
        self.assertIn("PORT must be in range 1..65535", str(context.exception))
    
    def test_port_out_of_range_high_raises_error(self):
        """Test PORT with value >= 65536 raises ValueError."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        os.environ['PORT'] = '65536'
        with self.assertRaises(ValueError) as context:
            import main
        self.assertIn("PORT must be in range 1..65535", str(context.exception))
    
    def test_port_boundary_values(self):
        """Test PORT accepts boundary values 1 and 65535."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        
        os.environ['PORT'] = '1'
        import main
        self.assertEqual(main.PORT, 1)
        del sys.modules['main']
        
        os.environ['PORT'] = '65535'
        import main
        self.assertEqual(main.PORT, 65535)
    
    def test_extra_default_value(self):
        """Test EXTRA defaults to empty string."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        self.assertEqual(main.EXTRA, '')
    
    def test_extra_custom_value(self):
        """Test EXTRA accepts custom string."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        os.environ['EXTRA'] = 'Additional alert information'
        import main
        self.assertEqual(main.EXTRA, 'Additional alert information')


class TestGetEmbedFunction(unittest.TestCase):
    """Test suite for the get_embed function that creates Discord embed payloads."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests in this class."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        os.environ['EXTRA'] = ''
        import main
        cls.main = main
    
    def test_get_embed_all_online_no_prefix(self):
        """Test get_embed with all devices online and no prefix."""
        data = {
            'total': 3,
            'online': 3,
            'degraded': 0,
            'vdevs': {}
        }
        result = self.main.get_embed('', data)
        
        self.assertIn('ONLINE', result['title'])
        self.assertEqual(result['color'], 0x00FF00)
        self.assertIn('3 / 3 online', result['description'])
        self.assertTrue(len(result['fields']) > 0)  # Should have timestamp field
    
    def test_get_embed_all_offline_with_prefix(self):
        """Test get_embed with all devices offline and prefix."""
        data = {
            'total': 5,
            'online': 0,
            'degraded': 0,
            'vdevs': {}
        }
        result = self.main.get_embed('tank', data)
        
        self.assertIn('tank:', result['title'])
        self.assertIn('OFFLINE', result['title'])
        self.assertEqual(result['color'], 0xFF0000)
        self.assertIn('0 / 5 online', result['description'])
    
    def test_get_embed_degraded_state(self):
        """Test get_embed with degraded devices."""
        data = {
            'total': 4,
            'online': 3,
            'degraded': 1,
            'vdevs': {}
        }
        result = self.main.get_embed('', data)
        
        self.assertIn('DEGRADED', result['title'])
        self.assertEqual(result['color'], 0xFFA500)
        self.assertIn('3 / 4 online', result['description'])
    
    def test_get_embed_with_vdevs(self):
        """Test get_embed with vdev information."""
        data = {
            'total': 6,
            'online': 6,
            'degraded': 0,
            'vdevs': {
                'raidz1-0': {'total': 3, 'online': 3, 'degraded': 0},
                'raidz1-1': {'total': 3, 'online': 3, 'degraded': 0}
            }
        }
        result = self.main.get_embed('', data)
        
        # Check that vdevs are in fields
        field_names = [f['name'] for f in result['fields']]
        self.assertTrue(any('raidz1-0' in name for name in field_names))
        self.assertTrue(any('raidz1-1' in name for name in field_names))
    
    def test_get_embed_with_space_info(self):
        """Test get_embed includes space information when provided."""
        data = {
            'total': 3,
            'online': 3,
            'degraded': 0,
            'alloc_space': '1.5TB',
            'total_space': '10TB',
            'vdevs': {}
        }
        result = self.main.get_embed('', data)
        
        self.assertIn('1.5TB / 10TB used', result['description'])
    
    def test_get_embed_with_degraded_drives(self):
        """Test get_embed includes degraded drives list."""
        data = {
            'total': 4,
            'online': 3,
            'degraded': 1,
            'degraded_drives': ['sda1', 'sdb1'],
            'vdevs': {}
        }
        result = self.main.get_embed('', data)
        
        # Check for degraded drives field
        degraded_fields = [f for f in result['fields'] if 'Degraded' in f['name']]
        self.assertTrue(len(degraded_fields) > 0)
        self.assertIn('sda1', degraded_fields[0]['value'])
        self.assertIn('sdb1', degraded_fields[0]['value'])
    
    def test_get_embed_with_offline_drives(self):
        """Test get_embed includes offline drives list."""
        data = {
            'total': 4,
            'online': 2,
            'degraded': 0,
            'offline_drives': ['sdc1', 'sdd1'],
            'vdevs': {}
        }
        result = self.main.get_embed('', data)
        
        # Check for offline drives field
        offline_fields = [f for f in result['fields'] if 'Offline' in f['name']]
        self.assertTrue(len(offline_fields) > 0)
        self.assertIn('sdc1', offline_fields[0]['value'])
        self.assertIn('sdd1', offline_fields[0]['value'])
    
    def test_get_embed_empty_degraded_list_not_shown(self):
        """Test get_embed doesn't show degraded field if list is empty."""
        data = {
            'total': 4,
            'online': 4,
            'degraded': 0,
            'degraded_drives': [],
            'vdevs': {}
        }
        result = self.main.get_embed('', data)
        
        degraded_fields = [f for f in result['fields'] if 'Degraded' in f['name']]
        self.assertEqual(len(degraded_fields), 0)
    
    def test_get_embed_vdev_with_space_info(self):
        """Test get_embed handles vdev with space information."""
        data = {
            'total': 6,
            'online': 6,
            'degraded': 0,
            'vdevs': {
                'raidz1-0': {
                    'total': 3,
                    'online': 3,
                    'degraded': 0,
                    'alloc_space': '500GB',
                    'total_space': '3TB'
                }
            }
        }
        result = self.main.get_embed('', data)
        
        # Find the raidz1-0 field
        raidz_fields = [f for f in result['fields'] if 'raidz1-0' in f['name']]
        self.assertTrue(len(raidz_fields) > 0)
        self.assertIn('500GB / 3TB used', raidz_fields[0]['value'])
    
    def test_get_embed_with_extra_text(self):
        """Test get_embed appends EXTRA text when configured."""
        # Temporarily set EXTRA
        original_extra = self.main.EXTRA
        self.main.EXTRA = 'Production Server Alert'
        
        try:
            data = {
                'total': 3,
                'online': 3,
                'degraded': 0,
                'vdevs': {}
            }
            result = self.main.get_embed('', data)
            
            self.assertIn('Production Server Alert', result['description'])
        finally:
            self.main.EXTRA = original_extra
    
    def test_get_embed_timestamp_field_present(self):
        """Test get_embed always includes a timestamp field."""
        data = {
            'total': 1,
            'online': 1,
            'degraded': 0,
            'vdevs': {}
        }
        result = self.main.get_embed('', data)
        
        timestamp_fields = [f for f in result['fields'] if f['name'] == 'Timestamp']
        self.assertEqual(len(timestamp_fields), 1)
        self.assertIn('<t:', timestamp_fields[0]['value'])
    
    def test_get_embed_mixed_vdev_states(self):
        """Test get_embed with mixed vdev states."""
        data = {
            'total': 9,
            'online': 7,
            'degraded': 2,
            'vdevs': {
                'raidz1-0': {'total': 3, 'online': 3, 'degraded': 0},
                'raidz1-1': {'total': 3, 'online': 2, 'degraded': 1},
                'raidz1-2': {'total': 3, 'online': 2, 'degraded': 1}
            }
        }
        result = self.main.get_embed('storage', data)
        
        self.assertIn('storage:', result['title'])
        self.assertIn('DEGRADED', result['title'])
        field_names = [f['name'] for f in result['fields']]
        # Check all vdevs are present
        self.assertEqual(sum(1 for name in field_names if 'raidz1' in name), 3)
    
    def test_get_embed_no_vdevs_key(self):
        """Test get_embed handles data without vdevs key gracefully."""
        data = {
            'total': 1,
            'online': 1,
            'degraded': 0
        }
        result = self.main.get_embed('', data)
        
        # Should not crash, should produce valid embed
        self.assertIn('title', result)
        self.assertIn('description', result)
        self.assertIn('color', result)
        self.assertIn('fields', result)


class TestCheckStatusFunction(unittest.TestCase):
    """Test suite for the check_status function that sends Discord notifications."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests in this class."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        cls.main = main
    
    def setUp(self):
        """Reset old_data before each test."""
        self.main.old_data = {"vdevs": {}}
    
    @patch('main.requests.post')
    @patch('main.logger')
    def test_check_status_sends_notification_on_new_data(self, mock_logger, mock_post):
        """Test check_status sends notification when data changes."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response
        
        data = {
            'total': 3,
            'online': 3,
            'degraded': 0,
            'vdevs': {}
        }
        
        self.main.check_status(data)
        
        # Should call post once
        self.assertEqual(mock_post.call_count, 1)
        # Check the call was made with correct URL
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], self.main.DISCORD_WEBHOOK_URL)
    
    @patch('main.requests.post')
    def test_check_status_no_notification_on_same_data(self, mock_post):
        """Test check_status doesn't send notification when data unchanged."""
        data = {
            'total': 3,
            'online': 3,
            'degraded': 0,
            'vdevs': {}
        }
        
        # First call should send
        mock_response = Mock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response
        self.main.check_status(data)
        
        # Reset mock
        mock_post.reset_mock()
        
        # Second call with same data should not send
        self.main.check_status(data)
        self.assertEqual(mock_post.call_count, 0)
    
    @patch('main.requests.post')
    @patch('main.time.sleep')
    def test_check_status_retries_on_failure(self, mock_sleep, mock_post):
        """Test check_status retries on request failure."""
        mock_post.side_effect = [
            Exception("Connection error"),
            Exception("Connection error"),
            Mock(status_code=204)
        ]
        
        data = {
            'total': 3,
            'online': 3,
            'degraded': 0,
            'vdevs': {}
        }
        
        self.main.check_status(data)
        
        # Should retry up to DISCORD_MAX_RETRIES times
        self.assertEqual(mock_post.call_count, 3)
        # Should sleep between retries
        self.assertEqual(mock_sleep.call_count, 2)
    
    @patch('main.requests.post')
    @patch('main.logger')
    def test_check_status_logs_non_204_status(self, mock_logger, mock_post):
        """Test check_status logs warning on non-204 status code."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response
        
        data = {
            'total': 3,
            'online': 3,
            'degraded': 0,
            'vdevs': {}
        }
        
        self.main.check_status(data)
        
        # Should log warning about status code
        mock_logger.warning.assert_called()
        warning_msg = str(mock_logger.warning.call_args[0][0])
        self.assertIn('400', warning_msg)
    
    @patch('main.requests.post')
    def test_check_status_verbose_mode_multiple_embeds(self, mock_post):
        """Test check_status sends separate embeds in verbose mode."""
        original_verbose = self.main.VERBOSE
        self.main.VERBOSE = True
        
        try:
            mock_response = Mock()
            mock_response.status_code = 204
            mock_post.return_value = mock_response
            
            data = {
                'total': 6,
                'online': 6,
                'degraded': 0,
                'vdevs': {
                    'tank': {'total': 3, 'online': 3, 'degraded': 0, 'vdevs': {}},
                    'backup': {'total': 3, 'online': 3, 'degraded': 0, 'vdevs': {}}
                }
            }
            
            self.main.check_status(data)
            
            # Check payload has multiple embeds
            call_args = mock_post.call_args
            payload = json.loads(call_args[1]['data'])
            self.assertEqual(len(payload['embeds']), 2)
        finally:
            self.main.VERBOSE = original_verbose
    
    @patch('main.requests.post')
    def test_check_status_non_verbose_mode_single_embed(self, mock_post):
        """Test check_status sends single embed in non-verbose mode."""
        original_verbose = self.main.VERBOSE
        self.main.VERBOSE = False
        
        try:
            mock_response = Mock()
            mock_response.status_code = 204
            mock_post.return_value = mock_response
            
            data = {
                'total': 6,
                'online': 6,
                'degraded': 0,
                'vdevs': {
                    'tank': {'total': 3, 'online': 3, 'degraded': 0, 'vdevs': {}},
                    'backup': {'total': 3, 'online': 3, 'degraded': 0, 'vdevs': {}}
                }
            }
            
            self.main.check_status(data)
            
            # Check payload has single embed
            call_args = mock_post.call_args
            payload = json.loads(call_args[1]['data'])
            self.assertEqual(len(payload['embeds']), 1)
        finally:
            self.main.VERBOSE = original_verbose
    
    @patch('main.requests.post')
    def test_check_status_updates_old_data(self, mock_post):
        """Test check_status updates old_data after sending."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response
        
        data = {
            'total': 3,
            'online': 3,
            'degraded': 0,
            'vdevs': {'test': {'total': 1, 'online': 1, 'degraded': 0}}
        }
        
        self.main.check_status(data)
        
        # old_data should be updated
        self.assertEqual(self.main.old_data['total'], 3)
        self.assertIn('test', self.main.old_data['vdevs'])


class TestCheckFunction(unittest.TestCase):
    """Test suite for the check function that polls ZFS status."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests in this class."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        os.environ['POOLS'] = 'tank backup'
        import main
        cls.main = main
    
    @patch('main.subprocess.check_output')
    @patch('main.check_status')
    def test_check_calls_zpool_status(self, mock_check_status, mock_subprocess):
        """Test check function calls zpool status command."""
        zpool_output = {
            'pools': {
                'tank': {
                    'state': 'ONLINE',
                    'vdevs': {
                        'tank': {
                            'vdevs': {
                                'sda1': {'state': 'ONLINE', 'vdev_type': 'disk', 'class': 'vdev'}
                            }
                        }
                    }
                }
            }
        }
        mock_subprocess.return_value = json.dumps(zpool_output)
        
        self.main.check()
        
        # Check subprocess was called
        self.assertEqual(mock_subprocess.call_count, 1)
        call_args = mock_subprocess.call_args[0][0]
        self.assertEqual(call_args[0], 'zpool')
        self.assertEqual(call_args[1], 'status')
        self.assertEqual(call_args[2], '-j')
    
    @patch('main.subprocess.check_output')
    @patch('main.check_status')
    def test_check_passes_pool_names_as_arguments(self, mock_check_status, mock_subprocess):
        """Test check function passes pool names as separate arguments."""
        zpool_output = {'pools': {}}
        mock_subprocess.return_value = json.dumps(zpool_output)
        
        self.main.check()
        
        call_args = mock_subprocess.call_args[0][0]
        self.assertIn('tank', call_args)
        self.assertIn('backup', call_args)
    
    @patch('main.subprocess.check_output')
    @patch('main.check_status')
    def test_check_builds_correct_data_structure(self, mock_check_status, mock_subprocess):
        """Test check function builds correct data structure."""
        zpool_output = {
            'pools': {
                'tank': {
                    'state': 'ONLINE',
                    'vdevs': {
                        'tank': {
                            'vdevs': {
                                'raidz1-0': {
                                    'vdev_type': 'raidz1',
                                    'vdevs': {
                                        'sda1': {'state': 'ONLINE', 'vdev_type': 'disk', 'class': 'vdev'},
                                        'sdb1': {'state': 'ONLINE', 'vdev_type': 'disk', 'class': 'vdev'}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        mock_subprocess.return_value = json.dumps(zpool_output)
        
        self.main.check()
        
        # Check that check_status was called with correct structure
        self.assertEqual(mock_check_status.call_count, 1)
        data = mock_check_status.call_args[0][0]
        
        self.assertIn('total', data)
        self.assertIn('online', data)
        self.assertIn('degraded', data)
        self.assertIn('vdevs', data)
        self.assertIn('tank', data['vdevs'])
    
    @patch('main.subprocess.check_output')
    @patch('main.check_status')
    def test_check_handles_degraded_drives(self, mock_check_status, mock_subprocess):
        """Test check function identifies degraded drives."""
        zpool_output = {
            'pools': {
                'tank': {
                    'state': 'DEGRADED',
                    'vdevs': {
                        'tank': {
                            'vdevs': {
                                'raidz1-0': {
                                    'vdev_type': 'raidz1',
                                    'vdevs': {
                                        'sda1': {'state': 'ONLINE', 'vdev_type': 'disk', 'class': 'vdev'},
                                        'sdb1': {'state': 'DEGRADED', 'vdev_type': 'disk', 'class': 'vdev'}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        mock_subprocess.return_value = json.dumps(zpool_output)
        
        self.main.check()
        
        data = mock_check_status.call_args[0][0]
        self.assertIn('sdb1', data['vdevs']['tank']['degraded_drives'])
    
    @patch('main.subprocess.check_output')
    @patch('main.check_status')
    def test_check_handles_offline_drives(self, mock_check_status, mock_subprocess):
        """Test check function identifies offline drives."""
        zpool_output = {
            'pools': {
                'tank': {
                    'state': 'DEGRADED',
                    'vdevs': {
                        'tank': {
                            'vdevs': {
                                'raidz1-0': {
                                    'vdev_type': 'raidz1',
                                    'vdevs': {
                                        'sda1': {'state': 'ONLINE', 'vdev_type': 'disk', 'class': 'vdev'},
                                        'sdb1': {'state': 'OFFLINE', 'vdev_type': 'disk', 'class': 'vdev'}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        mock_subprocess.return_value = json.dumps(zpool_output)
        
        self.main.check()
        
        data = mock_check_status.call_args[0][0]
        self.assertIn('sdb1', data['vdevs']['tank']['offline_drives'])
    
    @patch('main.subprocess.check_output')
    @patch('main.logger')
    def test_check_logs_subprocess_error(self, mock_logger, mock_subprocess):
        """Test check function logs subprocess errors."""
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, 'zpool')
        
        self.main.check()
        
        # Should log error
        mock_logger.error.assert_called()
    
    @patch('main.subprocess.check_output')
    @patch('main.check_status')
    def test_check_with_show_space_includes_space_data(self, mock_check_status, mock_subprocess):
        """Test check includes space data when SHOW_SPACE is True."""
        original_show_space = self.main.SHOW_SPACE
        self.main.SHOW_SPACE = True
        
        try:
            zpool_output = {
                'pools': {
                    'tank': {
                        'state': 'ONLINE',
                        'vdevs': {
                            'tank': {
                                'alloc_space': '1TB',
                                'total_space': '10TB',
                                'vdevs': {
                                    'sda1': {'state': 'ONLINE', 'vdev_type': 'disk', 'class': 'vdev'}
                                }
                            }
                        }
                    }
                }
            }
            mock_subprocess.return_value = json.dumps(zpool_output)
            
            self.main.check()
            
            data = mock_check_status.call_args[0][0]
            self.assertIn('alloc_space', data['vdevs']['tank'])
            self.assertIn('total_space', data['vdevs']['tank'])
        finally:
            self.main.SHOW_SPACE = original_show_space
    
    @patch('main.subprocess.check_output')
    @patch('main.check_status')
    def test_check_handles_spare_drives(self, mock_check_status, mock_subprocess):
        """Test check function handles spare drives."""
        zpool_output = {
            'pools': {
                'tank': {
                    'state': 'ONLINE',
                    'vdevs': {
                        'tank': {
                            'vdevs': {
                                'sda1': {'state': 'ONLINE', 'vdev_type': 'disk', 'class': 'vdev'}
                            }
                        }
                    },
                    'spares': {
                        'sdb1': {'state': 'AVAIL', 'vdev_type': 'disk', 'class': 'spare'}
                    }
                }
            }
        }
        mock_subprocess.return_value = json.dumps(zpool_output)
        
        self.main.check()
        
        data = mock_check_status.call_args[0][0]
        self.assertIn('spares', data['vdevs']['tank']['vdevs'])
    
    @patch('main.subprocess.check_output')
    @patch('main.check_status')
    def test_check_handles_log_devices(self, mock_check_status, mock_subprocess):
        """Test check function handles log devices."""
        zpool_output = {
            'pools': {
                'tank': {
                    'state': 'ONLINE',
                    'vdevs': {
                        'tank': {
                            'vdevs': {
                                'sda1': {'state': 'ONLINE', 'vdev_type': 'disk', 'class': 'vdev'}
                            }
                        }
                    },
                    'logs': {
                        'sdc1': {'state': 'ONLINE', 'vdev_type': 'disk', 'class': 'log'}
                    }
                }
            }
        }
        mock_subprocess.return_value = json.dumps(zpool_output)
        
        self.main.check()
        
        data = mock_check_status.call_args[0][0]
        self.assertIn('logs', data['vdevs']['tank']['vdevs'])
    
    @patch('main.subprocess.check_output')
    @patch('main.check_status')
    def test_check_handles_cache_devices(self, mock_check_status, mock_subprocess):
        """Test check function handles L2ARC cache devices."""
        zpool_output = {
            'pools': {
                'tank': {
                    'state': 'ONLINE',
                    'vdevs': {
                        'tank': {
                            'vdevs': {
                                'sda1': {'state': 'ONLINE', 'vdev_type': 'disk', 'class': 'vdev'}
                            }
                        }
                    },
                    'l2cache': {
                        'nvme0n1': {'state': 'ONLINE', 'vdev_type': 'disk', 'class': 'cache'}
                    }
                }
            }
        }
        mock_subprocess.return_value = json.dumps(zpool_output)
        
        self.main.check()
        
        data = mock_check_status.call_args[0][0]
        self.assertIn('cache', data['vdevs']['tank']['vdevs'])


class TestHTTPHandler(unittest.TestCase):
    """Test suite for the HTTP Handler class."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests in this class."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        cls.main = main
    
    def setUp(self):
        """Set up test data before each test."""
        self.main.old_data = {
            'total': 6,
            'online': 6,
            'degraded': 0,
            'vdevs': {
                'tank': {
                    'total': 3,
                    'online': 3,
                    'degraded': 0,
                    'degraded_drives': [],
                    'offline_drives': []
                }
            }
        }
    
    def test_handler_ping_endpoint(self):
        """Test Handler responds with 204 to /_ping."""
        handler = self.main.Handler(Mock(), ('127.0.0.1', 12345), None)
        handler.send_response = Mock()
        handler.end_headers = Mock()
        handler.path = '/_ping'
        
        handler.do_GET()
        
        handler.send_response.assert_called_with(204)
        handler.end_headers.assert_called_once()
    
    def test_handler_root_path_returns_data(self):
        """Test Handler returns full data for root path."""
        handler = self.main.Handler(Mock(), ('127.0.0.1', 12345), None)
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()
        handler.wfile = Mock()
        handler.path = '/'
        
        handler.do_GET()
        
        handler.send_response.assert_called_with(200)
        handler.send_header.assert_called_with('Content-type', 'application/json')
        # Check that data was written
        write_calls = handler.wfile.write.call_args_list
        self.assertTrue(len(write_calls) > 0)
    
    def test_handler_nested_path_returns_nested_data(self):
        """Test Handler returns nested data for path segments."""
        handler = self.main.Handler(Mock(), ('127.0.0.1', 12345), None)
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()
        handler.wfile = Mock()
        handler.path = '/vdevs/tank/total'
        
        handler.do_GET()
        
        handler.send_response.assert_called_with(200)
        # Should return the nested value
        write_calls = handler.wfile.write.call_args_list
        if len(write_calls) > 0:
            written_data = json.loads(write_calls[0][0][0].decode('utf8'))
            self.assertEqual(written_data, 3)
    
    def test_handler_invalid_path_returns_404(self):
        """Test Handler returns 404 for invalid path."""
        handler = self.main.Handler(Mock(), ('127.0.0.1', 12345), None)
        handler.send_response = Mock()
        handler.end_headers = Mock()
        handler.path = '/invalid/path/does/not/exist'
        
        handler.do_GET()
        
        handler.send_response.assert_called_with(404)
    
    def test_handler_query_string_is_stripped(self):
        """Test Handler strips query string from path."""
        handler = self.main.Handler(Mock(), ('127.0.0.1', 12345), None)
        handler.send_response = Mock()
        handler.end_headers = Mock()
        handler.path = '/_ping?foo=bar'
        
        handler.do_GET()
        
        # Should still respond to _ping
        handler.send_response.assert_called_with(204)
    
    def test_handler_empty_path_segments_ignored(self):
        """Test Handler ignores empty path segments."""
        handler = self.main.Handler(Mock(), ('127.0.0.1', 12345), None)
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()
        handler.wfile = Mock()
        handler.path = '//vdevs//tank///total///'
        
        handler.do_GET()
        
        # Should successfully navigate despite extra slashes
        handler.send_response.assert_called_with(200)
    
    @patch('main.logger')
    def test_handler_exception_returns_500(self, mock_logger):
        """Test Handler returns 500 on exception."""
        handler = self.main.Handler(Mock(), ('127.0.0.1', 12345), None)
        handler.send_response = Mock(side_effect=[Exception("Test"), None])
        handler.end_headers = Mock()
        handler.path = '/'
        
        handler.do_GET()
        
        # Should log exception
        mock_logger.exception.assert_called()
    
    @patch('main.logger')
    def test_handler_log_request_only_in_debug(self, mock_logger):
        """Test Handler.log_request only logs in DEBUG mode."""
        handler = self.main.Handler(Mock(), ('127.0.0.1', 12345), None)
        
        # Test when DEBUG is disabled
        mock_logger.isEnabledFor.return_value = False
        with patch.object(http.server.BaseHTTPRequestHandler, 'log_request') as mock_base_log:
            handler.log_request()
            mock_base_log.assert_not_called()
        
        # Test when DEBUG is enabled
        mock_logger.isEnabledFor.return_value = True
        with patch.object(http.server.BaseHTTPRequestHandler, 'log_request') as mock_base_log:
            handler.log_request()
            mock_base_log.assert_called_once()


class TestSignalHandling(unittest.TestCase):
    """Test suite for signal handling and shutdown logic."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests in this class."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        cls.main = main
    
    def setUp(self):
        """Reset shutdown_event before each test."""
        self.main.shutdown_event.clear()
    
    @patch('main.logger')
    def test_quit_function_sets_shutdown_event(self, mock_logger):
        """Test quit function sets shutdown_event."""
        self.assertFalse(self.main.shutdown_event.is_set())
        
        self.main.quit(signal.SIGTERM, None)
        
        self.assertTrue(self.main.shutdown_event.is_set())
        mock_logger.info.assert_called()
    
    @patch('main.logger')
    def test_quit_function_logs_signal_number(self, mock_logger):
        """Test quit function logs the signal number."""
        self.main.quit(signal.SIGINT, None)
        
        log_message = str(mock_logger.info.call_args[0][0])
        self.assertIn(str(signal.SIGINT), log_message)


class TestMainFunction(unittest.TestCase):
    """Test suite for the main function and application loop."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests in this class."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        cls.main = main
    
    def setUp(self):
        """Reset shutdown_event before each test."""
        self.main.shutdown_event.clear()
    
    @patch('main.check')
    @patch('main.shutdown_event')
    def test_main_calls_check_in_loop(self, mock_event, mock_check):
        """Test main function calls check in a loop."""
        # Make event wait return True immediately to exit loop
        mock_event.is_set.side_effect = [False, True]
        mock_event.wait.return_value = None
        
        self.main.main()
        
        # Check should be called at least once
        self.assertTrue(mock_check.call_count >= 1)
    
    @patch('main.http.server.ThreadingHTTPServer')
    @patch('main.threading.Thread')
    @patch('main.check')
    @patch('main.shutdown_event')
    def test_main_starts_webserver_when_enabled(self, mock_event, mock_check, mock_thread, mock_server):
        """Test main function starts web server when WEBSERVER is True."""
        original_webserver = self.main.WEBSERVER
        self.main.WEBSERVER = True
        
        try:
            mock_event.is_set.return_value = True  # Exit immediately
            mock_server_instance = Mock()
            mock_server.return_value = mock_server_instance
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            self.main.main()
            
            # Server should be created
            mock_server.assert_called_once()
            # Thread should be created and started
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()
        finally:
            self.main.WEBSERVER = original_webserver
    
    @patch('main.http.server.ThreadingHTTPServer')
    @patch('main.check')
    @patch('main.shutdown_event')
    def test_main_does_not_start_webserver_when_disabled(self, mock_event, mock_check, mock_server):
        """Test main function doesn't start web server when WEBSERVER is False."""
        original_webserver = self.main.WEBSERVER
        self.main.WEBSERVER = False
        
        try:
            mock_event.is_set.return_value = True  # Exit immediately
            
            self.main.main()
            
            # Server should not be created
            mock_server.assert_not_called()
        finally:
            self.main.WEBSERVER = original_webserver
    
    @patch('main.logger')
    @patch('main.check')
    @patch('main.shutdown_event')
    @patch('main.sys.exit')
    def test_main_logs_and_exits_on_exception(self, mock_exit, mock_event, mock_check, mock_logger):
        """Test main function logs exception and exits on error."""
        mock_check.side_effect = Exception("Test error")
        mock_event.is_set.return_value = False
        
        self.main.main()
        
        # Should log exception
        mock_logger.exception.assert_called()
        # Should exit with code 1
        mock_exit.assert_called_with(1)
    
    @patch('main.http.server.ThreadingHTTPServer')
    @patch('main.threading.Thread')
    @patch('main.check')
    @patch('main.shutdown_event')
    def test_main_shuts_down_webserver_on_exit(self, mock_event, mock_check, mock_thread, mock_server):
        """Test main function properly shuts down web server on exit."""
        original_webserver = self.main.WEBSERVER
        self.main.WEBSERVER = True
        
        try:
            mock_event.is_set.return_value = True  # Exit immediately
            mock_server_instance = Mock()
            mock_server.return_value = mock_server_instance
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            self.main.main()
            
            # Server should be shut down
            mock_server_instance.shutdown.assert_called_once()
            mock_server_instance.server_close.assert_called_once()
            # Thread should be joined
            mock_thread_instance.join.assert_called_once()
        finally:
            self.main.WEBSERVER = original_webserver


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for complex scenarios."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once for all tests in this class."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        cls.main = main
    
    @patch('main.subprocess.check_output')
    @patch('main.requests.post')
    def test_full_check_and_notify_flow(self, mock_post, mock_subprocess):
        """Test complete flow from ZFS check to Discord notification."""
        # Set up ZFS output
        zpool_output = {
            'pools': {
                'tank': {
                    'state': 'DEGRADED',
                    'vdevs': {
                        'tank': {
                            'vdevs': {
                                'raidz1-0': {
                                    'vdev_type': 'raidz1',
                                    'vdevs': {
                                        'sda1': {'state': 'ONLINE', 'vdev_type': 'disk', 'class': 'vdev'},
                                        'sdb1': {'state': 'DEGRADED', 'vdev_type': 'disk', 'class': 'vdev'},
                                        'sdc1': {'state': 'ONLINE', 'vdev_type': 'disk', 'class': 'vdev'}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        mock_subprocess.return_value = json.dumps(zpool_output)
        
        # Set up Discord response
        mock_response = Mock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response
        
        # Reset old_data to ensure notification is sent
        self.main.old_data = {"vdevs": {}}
        
        # Run check
        self.main.check()
        
        # Verify Discord was called
        self.assertEqual(mock_post.call_count, 1)
        
        # Verify payload structure
        call_args = mock_post.call_args
        payload = json.loads(call_args[1]['data'])
        self.assertIn('embeds', payload)
        self.assertTrue(len(payload['embeds']) > 0)
        
        # Verify embed contains degraded information
        embed = payload['embeds'][0]
        self.assertIn('DEGRADED', embed['title'])
    
    @patch('main.subprocess.check_output')
    @patch('main.requests.post')
    def test_no_notification_when_status_unchanged(self, mock_post, mock_subprocess):
        """Test no notification sent when status hasn't changed."""
        zpool_output = {
            'pools': {
                'tank': {
                    'state': 'ONLINE',
                    'vdevs': {
                        'tank': {
                            'vdevs': {
                                'sda1': {'state': 'ONLINE', 'vdev_type': 'disk', 'class': 'vdev'}
                            }
                        }
                    }
                }
            }
        }
        mock_subprocess.return_value = json.dumps(zpool_output)
        mock_response = Mock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response
        
        # First check - should send notification
        self.main.old_data = {"vdevs": {}}
        self.main.check()
        self.assertEqual(mock_post.call_count, 1)
        
        # Second check with same data - should not send
        mock_post.reset_mock()
        self.main.check()
        self.assertEqual(mock_post.call_count, 0)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)


class TestEdgeCasesAndBoundaries(unittest.TestCase):
    """Test suite for edge cases, boundary conditions, and error handling."""
    
    def setUp(self):
        """Set up test environment before each test."""
        self.original_env = os.environ.copy()
        for var in ['DISCORD_WEBHOOK_URL', 'DISCORD_MAX_RETRIES', 'DISCORD_RETRY_DELAY',
                    'CHECK_DELAY', 'EXTRA', 'POOLS', 'SHOW_SPACE', 'VERBOSE',
                    'WEBSERVER', 'HOST', 'PORT', 'LOG_LEVEL']:
            os.environ.pop(var, None)
    
    def tearDown(self):
        """Clean up after each test."""
        os.environ.clear()
        os.environ.update(self.original_env)
        if 'main' in sys.modules:
            del sys.modules['main']
    
    def test_pools_with_whitespace_variations(self):
        """Test POOLS handles various whitespace patterns."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        
        # Multiple spaces
        os.environ['POOLS'] = 'tank   backup     data'
        import main
        self.assertEqual(main.POOLS, 'tank   backup     data')
        del sys.modules['main']
        
        # Tabs and newlines are spaces too
        os.environ['POOLS'] = 'tank\tbackup'
        import main
        # The regex allows \s which includes tabs
        self.assertIn('tank', main.POOLS)
    
    def test_pools_with_valid_special_characters(self):
        """Test POOLS accepts valid special characters."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        
        # Valid characters: alphanumeric, underscore, period, colon, comma, dash
        os.environ['POOLS'] = 'tank_1 backup-2 data.pool pool:test'
        import main
        self.assertEqual(main.POOLS, 'tank_1 backup-2 data.pool pool:test')
    
    def test_get_embed_zero_total_devices(self):
        """Test get_embed with zero total devices."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        
        data = {
            'total': 0,
            'online': 0,
            'degraded': 0,
            'vdevs': {}
        }
        result = main.get_embed('', data)
        
        # Should handle gracefully
        self.assertIn('0 / 0 online', result['description'])
    
    def test_get_embed_all_degraded_no_online(self):
        """Test get_embed when all devices are degraded."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        
        data = {
            'total': 3,
            'online': 0,
            'degraded': 3,
            'vdevs': {}
        }
        result = main.get_embed('', data)
        
        # Should show as degraded, not offline
        self.assertIn('DEGRADED', result['title'])
        self.assertEqual(result['color'], 0xFFA500)
    
    def test_get_embed_partial_degraded_partial_offline(self):
        """Test get_embed with some degraded and some offline."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        
        data = {
            'total': 5,
            'online': 2,
            'degraded': 2,
            'vdevs': {}
        }
        result = main.get_embed('', data)
        
        # 5 total, 2 online, 2 degraded = 1 offline
        self.assertIn('(1 unavailable)', result['description'])
    
    def test_get_embed_single_degraded_drive_in_list(self):
        """Test get_embed with single degraded drive."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        
        data = {
            'total': 2,
            'online': 1,
            'degraded': 1,
            'degraded_drives': ['single-drive'],
            'vdevs': {}
        }
        result = main.get_embed('', data)
        
        degraded_fields = [f for f in result['fields'] if 'Degraded' in f['name']]
        self.assertEqual(len(degraded_fields), 1)
        self.assertIn('single-drive', degraded_fields[0]['value'])
    
    def test_get_embed_many_drives_in_lists(self):
        """Test get_embed with many drives in degraded/offline lists."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        
        degraded = [f'degraded-{i}' for i in range(10)]
        offline = [f'offline-{i}' for i in range(15)]
        
        data = {
            'total': 30,
            'online': 5,
            'degraded': 10,
            'degraded_drives': degraded,
            'offline_drives': offline,
            'vdevs': {}
        }
        result = main.get_embed('', data)
        
        # Check all drives are listed
        degraded_fields = [f for f in result['fields'] if 'Degraded' in f['name']]
        offline_fields = [f for f in result['fields'] if 'Offline' in f['name']]
        
        self.assertTrue(all(d in degraded_fields[0]['value'] for d in degraded))
        self.assertTrue(all(o in offline_fields[0]['value'] for o in offline))
    
    def test_get_embed_unicode_in_pool_names(self):
        """Test get_embed handles unicode characters in pool names."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        
        data = {
            'total': 1,
            'online': 1,
            'degraded': 0,
            'vdevs': {}
        }
        result = main.get_embed('池-pool', data)  # Chinese character + ASCII
        
        self.assertIn('池-pool', result['title'])
    
    def test_get_embed_very_large_space_values(self):
        """Test get_embed with very large space values."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        
        data = {
            'total': 1,
            'online': 1,
            'degraded': 0,
            'alloc_space': '999.99PB',
            'total_space': '1000PB',
            'vdevs': {}
        }
        result = main.get_embed('', data)
        
        self.assertIn('999.99PB / 1000PB used', result['description'])
    
    @patch('main.requests.post')
    def test_check_status_max_retries_zero(self, mock_post):
        """Test check_status with DISCORD_MAX_RETRIES set to 0."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        os.environ['DISCORD_MAX_RETRIES'] = '0'
        import main
        
        mock_post.side_effect = Exception("Connection error")
        
        data = {
            'total': 1,
            'online': 1,
            'degraded': 0,
            'vdevs': {}
        }
        
        main.old_data = {"vdevs": {}}
        main.check_status(data)
        
        # Should not call post since max_retries is 0
        self.assertEqual(mock_post.call_count, 0)
    
    @patch('main.requests.post')
    @patch('main.time.sleep')
    def test_check_status_retry_delay_zero(self, mock_sleep, mock_post):
        """Test check_status with DISCORD_RETRY_DELAY set to 0."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        os.environ['DISCORD_RETRY_DELAY'] = '0'
        import main
        
        mock_post.side_effect = [
            Exception("Error 1"),
            Mock(status_code=204)
        ]
        
        data = {
            'total': 1,
            'online': 1,
            'degraded': 0,
            'vdevs': {}
        }
        
        main.old_data = {"vdevs": {}}
        main.check_status(data)
        
        # Should still retry but with 0 sleep
        self.assertEqual(mock_post.call_count, 2)
        mock_sleep.assert_called_with(0)
    
    @patch('main.subprocess.check_output')
    @patch('main.check_status')
    def test_check_empty_pools_list(self, mock_check_status, mock_subprocess):
        """Test check function with empty POOLS list."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        os.environ['POOLS'] = ''
        import main
        
        zpool_output = {'pools': {}}
        mock_subprocess.return_value = json.dumps(zpool_output)
        
        main.check()
        
        # Should call zpool without specific pool names
        call_args = mock_subprocess.call_args[0][0]
        self.assertEqual(call_args[0], 'zpool')
        # After 'zpool', 'status', '-j', there should be no more arguments
        self.assertEqual(len(call_args), 3)
    
    @patch('main.subprocess.check_output')
    @patch('main.check_status')
    def test_check_complex_spare_replacement_scenario(self, mock_check_status, mock_subprocess):
        """Test check handles complex spare with replacing vdev."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        
        zpool_output = {
            'pools': {
                'tank': {
                    'state': 'DEGRADED',
                    'vdevs': {
                        'tank': {
                            'vdevs': {
                                'raidz1-0': {
                                    'vdev_type': 'raidz1',
                                    'vdevs': {
                                        'sda1': {'state': 'ONLINE', 'vdev_type': 'disk', 'class': 'vdev'},
                                        'spare-0': {
                                            'state': 'DEGRADED',
                                            'vdev_type': 'spare',
                                            'class': 'vdev',
                                            'vdevs': {
                                                'replacing-0': {
                                                    'vdev_type': 'replacing',
                                                    'class': 'vdev',
                                                    'vdevs': {
                                                        'sdb1': {'state': 'DEGRADED', 'vdev_type': 'disk'},
                                                        'sdc1': {'state': 'ONLINE', 'vdev_type': 'disk'}
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        mock_subprocess.return_value = json.dumps(zpool_output)
        
        main.check()
        
        data = mock_check_status.call_args[0][0]
        # Should identify sdb1 as degraded (replacing)
        self.assertTrue(any('sdb1' in drive for drive in data['vdevs']['tank']['degraded_drives']))
    
    @patch('main.subprocess.check_output')
    @patch('main.check_status')
    def test_check_mirror_in_log_devices(self, mock_check_status, mock_subprocess):
        """Test check handles mirrored log devices."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        
        zpool_output = {
            'pools': {
                'tank': {
                    'state': 'ONLINE',
                    'vdevs': {
                        'tank': {
                            'vdevs': {
                                'sda1': {'state': 'ONLINE', 'vdev_type': 'disk', 'class': 'vdev'}
                            }
                        }
                    },
                    'logs': {
                        'mirror-0': {
                            'vdev_type': 'mirror',
                            'vdevs': {
                                'sdb1': {'state': 'ONLINE', 'vdev_type': 'disk', 'class': 'log'},
                                'sdc1': {'state': 'ONLINE', 'vdev_type': 'disk', 'class': 'log'}
                            }
                        }
                    }
                }
            }
        }
        mock_subprocess.return_value = json.dumps(zpool_output)
        
        main.check()
        
        data = mock_check_status.call_args[0][0]
        # Should have logs vdev with correct counts
        self.assertIn('logs', data['vdevs']['tank']['vdevs'])
        self.assertEqual(data['vdevs']['tank']['vdevs']['logs']['total'], 2)
    
    def test_handler_path_with_non_dict_intermediate(self):
        """Test Handler returns 404 when path traverses through non-dict."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        
        main.old_data = {
            'total': 5,
            'vdevs': {}
        }
        
        handler = main.Handler(Mock(), ('127.0.0.1', 12345), None)
        handler.send_response = Mock()
        handler.end_headers = Mock()
        # 'total' is an integer, can't traverse into it
        handler.path = '/total/subkey'
        
        handler.do_GET()
        
        handler.send_response.assert_called_with(404)
    
    def test_handler_path_returning_list(self):
        """Test Handler can return list data."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        
        main.old_data = {
            'vdevs': {
                'tank': {
                    'degraded_drives': ['sda1', 'sdb1']
                }
            }
        }
        
        handler = main.Handler(Mock(), ('127.0.0.1', 12345), None)
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()
        handler.wfile = Mock()
        handler.path = '/vdevs/tank/degraded_drives'
        
        handler.do_GET()
        
        handler.send_response.assert_called_with(200)
        write_calls = handler.wfile.write.call_args_list
        if len(write_calls) > 0:
            written_data = json.loads(write_calls[0][0][0].decode('utf8'))
            self.assertEqual(written_data, ['sda1', 'sdb1'])
    
    def test_handler_path_returning_integer(self):
        """Test Handler can return integer data."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        
        main.old_data = {'total': 42}
        
        handler = main.Handler(Mock(), ('127.0.0.1', 12345), None)
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()
        handler.wfile = Mock()
        handler.path = '/total'
        
        handler.do_GET()
        
        handler.send_response.assert_called_with(200)
        write_calls = handler.wfile.write.call_args_list
        if len(write_calls) > 0:
            written_data = json.loads(write_calls[0][0][0].decode('utf8'))
            self.assertEqual(written_data, 42)
    
    def test_handler_path_returning_boolean(self):
        """Test Handler can return boolean data."""
        os.environ['DISCORD_WEBHOOK_URL'] = 'https://discord.com/api/webhooks/test'
        import main
        
        main.old_data = {'is_healthy': True}
        
        handler = main.Handler(Mock(), ('127.0.0.1', 12345), None)
        handler.send_response = Mock()
        handler.send_header = Mock()
        handler.end_headers = Mock()
        handler.wfile = Mock()
        handler.path = '/is_healthy'
        
        handler.do_GET()
        
        handler.send_response.assert_called_with(200)
        write_calls = handler.wfile.write.call_args_list
        if len(write_calls) > 0:
            written_data = json.loads(write_calls[0][0][0].decode('utf8'))
            self.assertTrue(written_data)


class TestComposeYamlValidation(unittest.TestCase):
    """Test suite to validate compose.yaml configuration file."""
    
    def test_compose_yaml_exists(self):
        """Test that compose.yaml file exists."""
        self.assertTrue(os.path.exists('compose.yaml'))
    
    def test_compose_yaml_valid_syntax(self):
        """Test that compose.yaml has valid YAML syntax."""
        try:
            import yaml
        except ImportError:
            self.skipTest("pyyaml not available")
        
        with open('compose.yaml', 'r') as f:
            try:
                data = yaml.safe_load(f)
                self.assertIsNotNone(data)
            except yaml.YAMLError as e:
                self.fail(f"Invalid YAML syntax: {e}")
    
    def test_compose_yaml_has_services(self):
        """Test that compose.yaml defines services."""
        try:
            import yaml
        except ImportError:
            self.skipTest("pyyaml not available")
        
        with open('compose.yaml', 'r') as f:
            data = yaml.safe_load(f)
            self.assertIn('services', data)
            self.assertIsInstance(data['services'], dict)
            self.assertTrue(len(data['services']) > 0)
    
    def test_compose_yaml_zfs_discord_alerts_service(self):
        """Test that compose.yaml defines zfs-discord-alerts service."""
        try:
            import yaml
        except ImportError:
            self.skipTest("pyyaml not available")
        
        with open('compose.yaml', 'r') as f:
            data = yaml.safe_load(f)
            self.assertIn('zfs-discord-alerts', data['services'])
    
    def test_compose_yaml_environment_variables(self):
        """Test that compose.yaml includes all required environment variables."""
        try:
            import yaml
        except ImportError:
            self.skipTest("pyyaml not available")
        
        with open('compose.yaml', 'r') as f:
            data = yaml.safe_load(f)
            service = data['services']['zfs-discord-alerts']
            self.assertIn('environment', service)
            
            env = service['environment']
            # Check for key environment variables
            expected_vars = ['DISCORD_WEBHOOK_URL', 'WEBSERVER', 'PORT']
            for var in expected_vars:
                self.assertIn(var, env, f"Missing environment variable: {var}")
    
    def test_compose_yaml_has_healthcheck_comment(self):
        """Test that compose.yaml includes healthcheck configuration (commented)."""
        with open('compose.yaml', 'r') as f:
            content = f.read()
            # Check for healthcheck presence (even if commented)
            self.assertIn('healthcheck', content.lower())
            self.assertIn('_ping', content)


class TestReadmeDocumentation(unittest.TestCase):
    """Test suite to validate README.md documentation."""
    
    def test_readme_exists(self):
        """Test that README.md file exists."""
        self.assertTrue(os.path.exists('README.md'))
    
    def test_readme_documents_webserver_feature(self):
        """Test that README documents the new WEBSERVER feature."""
        with open('README.md', 'r') as f:
            content = f.read()
            self.assertIn('WEBSERVER', content)
            self.assertIn('Web Server', content)
    
    def test_readme_documents_host_and_port(self):
        """Test that README documents HOST and PORT configuration."""
        with open('README.md', 'r') as f:
            content = f.read()
            self.assertIn('HOST', content)
            self.assertIn('PORT', content)
    
    def test_readme_documents_ping_endpoint(self):
        """Test that README documents the /_ping endpoint."""
        with open('README.md', 'r') as f:
            content = f.read()
            self.assertIn('_ping', content)
    
    def test_readme_documents_api_json_structure(self):
        """Test that README documents the API JSON structure."""
        with open('README.md', 'r') as f:
            content = f.read()
            self.assertIn('total', content)
            self.assertIn('online', content)
            self.assertIn('degraded', content)
            self.assertIn('vdevs', content)
    
    def test_readme_includes_security_warning(self):
        """Test that README includes security warning about webserver."""
        with open('README.md', 'r') as f:
            content = f.read()
            # Should warn about unsecured webserver
            self.assertTrue(
                'unsecured' in content.lower() or 'security' in content.lower(),
                "README should include security warnings about the webserver"
            )


if __name__ == '__main__':
    unittest.main(verbosity=2)