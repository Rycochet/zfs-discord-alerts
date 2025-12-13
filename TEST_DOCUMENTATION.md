# Test Documentation for ZFS Discord Alerts

## Overview

This document describes the comprehensive test suite for the ZFS Discord Alerts application. The test suite covers all functionality introduced in the recent changes, including environment variable validation, web server functionality, improved command execution, and Discord notification logic.

## Test Structure

The test suite is organized into 11 test classes with 113 individual test methods:

### 1. TestEnvironmentVariableValidation (36 tests)
Tests all environment variable parsing, validation, and error handling:

- **Discord Configuration Tests**
  - `test_missing_discord_webhook_url_raises_error` - Validates required webhook URL
  - `test_valid_discord_webhook_url_loads` - Tests successful webhook URL loading
  - `test_discord_max_retries_*` - Tests retry count validation (default, custom, invalid, negative, zero, boundary values)
  - `test_discord_retry_delay_*` - Tests retry delay validation (default, custom, invalid, negative)

- **Check Delay Tests**
  - `test_check_delay_*` - Tests CHECK_DELAY validation (default, custom, invalid, negative)

- **Pool Configuration Tests**
  - `test_pools_empty_string_is_valid` - Tests monitoring all pools
  - `test_pools_valid_pool_names` - Tests valid pool name parsing
  - `test_pools_with_invalid_characters_raises_error` - Tests security validation
  - `test_pools_reserved_words_are_filtered` - Tests ZFS reserved word filtering

- **Boolean Configuration Tests**
  - `test_show_space_*` - Tests SHOW_SPACE boolean parsing (true/false values)
  - `test_verbose_*` - Tests VERBOSE boolean parsing
  - `test_webserver_*` - Tests WEBSERVER boolean parsing

- **Web Server Configuration Tests**
  - `test_host_*` - Tests HOST configuration (default and custom values)
  - `test_port_*` - Tests PORT validation (default, custom, invalid, out of range, boundaries)

- **Extra Configuration Tests**
  - `test_extra_*` - Tests EXTRA text configuration

### 2. TestGetEmbedFunction (13 tests)
Tests Discord embed generation with various data structures:

- **Status Tests**
  - `test_get_embed_all_online_no_prefix` - Tests fully healthy status
  - `test_get_embed_all_offline_with_prefix` - Tests completely offline status
  - `test_get_embed_degraded_state` - Tests degraded status

- **Data Structure Tests**
  - `test_get_embed_with_vdevs` - Tests vdev information inclusion
  - `test_get_embed_with_space_info` - Tests space usage display
  - `test_get_embed_with_degraded_drives` - Tests degraded drive listing
  - `test_get_embed_with_offline_drives` - Tests offline drive listing
  - `test_get_embed_empty_degraded_list_not_shown` - Tests empty list handling

- **Advanced Tests**
  - `test_get_embed_vdev_with_space_info` - Tests per-vdev space information
  - `test_get_embed_with_extra_text` - Tests EXTRA text inclusion
  - `test_get_embed_timestamp_field_present` - Tests timestamp field
  - `test_get_embed_mixed_vdev_states` - Tests complex mixed states
  - `test_get_embed_no_vdevs_key` - Tests graceful handling of missing keys

### 3. TestCheckStatusFunction (7 tests)
Tests Discord notification sending logic:

- **Notification Logic Tests**
  - `test_check_status_sends_notification_on_new_data` - Tests notification on change
  - `test_check_status_no_notification_on_same_data` - Tests suppression of duplicate notifications
  - `test_check_status_retries_on_failure` - Tests retry mechanism
  - `test_check_status_logs_non_204_status` - Tests error status logging

- **Mode Tests**
  - `test_check_status_verbose_mode_multiple_embeds` - Tests verbose mode (separate embeds per pool)
  - `test_check_status_non_verbose_mode_single_embed` - Tests normal mode (single combined embed)
  - `test_check_status_updates_old_data` - Tests state tracking

### 4. TestCheckFunction (10 tests)
Tests ZFS pool status checking and data processing:

- **Command Execution Tests**
  - `test_check_calls_zpool_status` - Tests zpool command invocation
  - `test_check_passes_pool_names_as_arguments` - Tests secure argument passing (no shell=True)
  - `test_check_builds_correct_data_structure` - Tests data structure construction

- **Drive Status Tests**
  - `test_check_handles_degraded_drives` - Tests degraded drive detection
  - `test_check_handles_offline_drives` - Tests offline drive detection
  - `test_check_logs_subprocess_error` - Tests error handling

- **Feature Tests**
  - `test_check_with_show_space_includes_space_data` - Tests space reporting
  - `test_check_handles_spare_drives` - Tests spare drive handling
  - `test_check_handles_log_devices` - Tests log device handling
  - `test_check_handles_cache_devices` - Tests L2ARC cache handling

### 5. TestHTTPHandler (8 tests)
Tests the new web server HTTP handler:

- **Endpoint Tests**
  - `test_handler_ping_endpoint` - Tests /_ping health check endpoint
  - `test_handler_root_path_returns_data` - Tests root path data retrieval
  - `test_handler_nested_path_returns_nested_data` - Tests nested path navigation
  - `test_handler_invalid_path_returns_404` - Tests 404 error handling

- **Request Parsing Tests**
  - `test_handler_query_string_is_stripped` - Tests query string handling
  - `test_handler_empty_path_segments_ignored` - Tests empty segment handling
  - `test_handler_exception_returns_500` - Tests exception handling
  - `test_handler_log_request_only_in_debug` - Tests conditional logging

### 6. TestSignalHandling (2 tests)
Tests signal handling and graceful shutdown:

- `test_quit_function_sets_shutdown_event` - Tests shutdown event setting
- `test_quit_function_logs_signal_number` - Tests signal logging

### 7. TestMainFunction (5 tests)
Tests the main application loop and lifecycle:

- **Loop Tests**
  - `test_main_calls_check_in_loop` - Tests periodic check execution
  - `test_main_starts_webserver_when_enabled` - Tests web server initialization
  - `test_main_does_not_start_webserver_when_disabled` - Tests web server opt-out

- **Error Handling Tests**
  - `test_main_logs_and_exits_on_exception` - Tests exception handling
  - `test_main_shuts_down_webserver_on_exit` - Tests graceful shutdown

### 8. TestIntegrationScenarios (2 tests)
Tests end-to-end scenarios:

- `test_full_check_and_notify_flow` - Tests complete workflow from ZFS check to Discord notification
- `test_no_notification_when_status_unchanged` - Tests notification suppression

### 9. TestEdgeCasesAndBoundaries (20 tests)
Tests edge cases, boundary conditions, and unusual scenarios:

- **Input Validation Edge Cases**
  - `test_pools_with_whitespace_variations` - Tests various whitespace patterns
  - `test_pools_with_valid_special_characters` - Tests special character handling
  - `test_get_embed_zero_total_devices` - Tests zero device handling
  - `test_get_embed_all_degraded_no_online` - Tests all-degraded state

- **Complex Scenarios**
  - `test_get_embed_partial_degraded_partial_offline` - Tests mixed offline/degraded
  - `test_get_embed_single_degraded_drive_in_list` - Tests single item lists
  - `test_get_embed_many_drives_in_lists` - Tests large drive lists
  - `test_get_embed_unicode_in_pool_names` - Tests unicode handling
  - `test_get_embed_very_large_space_values` - Tests large space values

- **Boundary Conditions**
  - `test_check_status_max_retries_zero` - Tests zero retry configuration
  - `test_check_status_retry_delay_zero` - Tests zero delay configuration
  - `test_check_empty_pools_list` - Tests empty pool list
  - `test_check_complex_spare_replacement_scenario` - Tests complex spare scenarios
  - `test_check_mirror_in_log_devices` - Tests mirrored log devices

- **HTTP Handler Edge Cases**
  - `test_handler_path_with_non_dict_intermediate` - Tests invalid path traversal
  - `test_handler_path_returning_list` - Tests list return values
  - `test_handler_path_returning_integer` - Tests integer return values
  - `test_handler_path_returning_boolean` - Tests boolean return values

### 10. TestComposeYamlValidation (5 tests)
Tests Docker Compose configuration:

- `test_compose_yaml_exists` - Tests file existence
- `test_compose_yaml_valid_syntax` - Tests YAML syntax validity
- `test_compose_yaml_has_services` - Tests service definitions
- `test_compose_yaml_zfs_discord_alerts_service` - Tests specific service
- `test_compose_yaml_environment_variables` - Tests environment variable configuration
- `test_compose_yaml_has_healthcheck_comment` - Tests healthcheck configuration

### 11. TestReadmeDocumentation (5 tests)
Tests README documentation completeness:

- `test_readme_exists` - Tests file existence
- `test_readme_documents_webserver_feature` - Tests WEBSERVER documentation
- `test_readme_documents_host_and_port` - Tests HOST/PORT documentation
- `test_readme_documents_ping_endpoint` - Tests /_ping documentation
- `test_readme_documents_api_json_structure` - Tests API structure documentation
- `test_readme_includes_security_warning` - Tests security warning presence

## Running the Tests

### Quick Start

```bash
# Make the test runner executable
chmod +x run_tests.sh

# Run all tests
./run_tests.sh
```

### Manual Execution

```bash
# Run all tests with verbose output
python3 -m unittest test_main.py -v

# Run a specific test class
python3 -m unittest test_main.TestEnvironmentVariableValidation -v

# Run a specific test method
python3 -m unittest test_main.TestEnvironmentVariableValidation.test_missing_discord_webhook_url_raises_error -v
```

### Test Discovery

```bash
# Run with test discovery
python3 -m unittest discover -s . -p "test_*.py" -v
```

## Test Coverage

The test suite provides comprehensive coverage of:

1. **Environment Variable Validation** (NEW)
   - All new validation logic for integer environment variables
   - Boundary testing for PORT range (1-65535)
   - Negative value rejection for all numeric configs
   - Boolean parsing for WEBSERVER, SHOW_SPACE, VERBOSE

2. **Web Server Functionality** (NEW)
   - HTTP GET request handling
   - Health check endpoint (/_ping)
   - JSON API with path-based data retrieval
   - Error handling (404, 500)
   - Conditional request logging

3. **Command Execution Security** (IMPROVED)
   - Secure argument passing without shell=True
   - Pool name filtering and validation
   - ZFS reserved word filtering

4. **Discord Integration**
   - Embed generation for all pool states
   - Notification logic with retry mechanism
   - Verbose vs normal mode behavior
   - State change detection

5. **ZFS Data Processing**
   - Complex pool/vdev structures
   - Degraded and offline drive detection
   - Spare drive replacement scenarios
   - Log, cache, and spare device handling

6. **Application Lifecycle**
   - Signal handling (SIGTERM, SIGINT, SIGHUP)
   - Graceful shutdown
   - Web server start/stop
   - Exception handling

7. **Configuration Files**
   - compose.yaml validation
   - README.md documentation verification

## Dependencies

The test suite uses Python's built-in `unittest` framework and requires no additional testing dependencies for the core tests.

Optional dependencies:
- `pyyaml` - For YAML validation tests (will skip if not available)
- `requests` - Already a project dependency
- `python-dotenv` - Already a project dependency

## Test Design Principles

1. **Isolation**: Each test is independent and can run in any order
2. **Mocking**: External dependencies (subprocess, requests, file I/O) are mocked
3. **Coverage**: Tests cover happy paths, edge cases, and failure conditions
4. **Clarity**: Test names clearly describe what is being tested
5. **Assertions**: Multiple assertions per test to verify all aspects of behavior

## Continuous Integration

These tests are designed to run in CI/CD pipelines. They:
- Require no external services (ZFS, Discord)
- Use mocking for all external dependencies
- Can run in isolated environments
- Provide clear pass/fail results

## Known Limitations

1. Some tests may be skipped if optional dependencies (e.g., pyyaml) are not installed
2. Tests assume Python 3.6+ due to f-string usage in main.py
3. Tests mock subprocess calls and don't validate actual ZFS command functionality
4. Web server tests don't validate network-level behavior

## Contributing

When adding new functionality to main.py:

1. Add corresponding tests to test_main.py
2. Ensure tests cover happy paths, edge cases, and failure modes
3. Use descriptive test names following the pattern: `test_<function>_<scenario>`
4. Mock external dependencies appropriately
5. Run the full test suite before submitting changes

## Test Maintenance

- Keep tests up-to-date with code changes
- Refactor tests when code structure changes
- Add regression tests for any bugs discovered
- Maintain test documentation alongside code documentation