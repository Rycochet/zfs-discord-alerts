import http.server
import json
import logging
import os
import re
import requests
import signal
import subprocess
import sys
import threading
import time

from dotenv import load_dotenv
from threading import Event

load_dotenv()

isTTY = sys.stdout.isatty()

logging.basicConfig(
    level = os.getenv('LOG_LEVEL', 'INFO').upper(),
    format = '[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Discord configuration
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')
if not DISCORD_WEBHOOK_URL:
    raise ValueError("DISCORD_WEBHOOK_URL environment variable is required")

try:
    DISCORD_MAX_RETRIES = int(os.environ.get('DISCORD_MAX_RETRIES', '5'))
except ValueError:
    raise ValueError("DISCORD_MAX_RETRIES environment variable must be a valid integer")

try:
    DISCORD_RETRY_DELAY = int(os.environ.get('DISCORD_RETRY_DELAY', '5'))
except ValueError:
    raise ValueError("DISCORD_RETRY_DELAY environment variable must be a valid integer")

# How long should we wait between checks - 5 minutes default
try:
    CHECK_DELAY = int(os.environ.get('CHECK_DELAY', '5'))
except ValueError:
    raise ValueError("CHECK_DELAY environment variable must be a valid integer")

# Extra text to add to notifications
EXTRA = os.environ.get('EXTRA', '')

# Pools monitoring configuration - see error link for the rules, anything breaking it is removed and if they have different lengths it raises an error
# Coincidentally anything that breaks these rules can also break security as we pass this on a command line!
pools_env = os.environ.get('POOLS', '').strip()
pools_tmp = re.sub(
    r"(?:[^a-zA-Z0-9_.:,\s-]|\b(?:c[0-9]\S*|log|mirror|raidz[1-3]?|spare|[0-9_.:-].*)\b)",
    "",
    pools_env
)
if len(pools_env) != len(pools_tmp):
    raise ValueError("POOLS environment variable contains invalid pool names: https://docs.oracle.com/cd/E26505_01/html/E37384/gbcpt.html")
POOLS = pools_tmp

# Show disk usage, this will result in updates roughtly every TB
SHOW_SPACE = os.getenv("SHOW_SPACE", 'False').lower() in ('true', '1', 'yes')

# Verbose monitoring configuration
VERBOSE = os.getenv("VERBOSE", 'False').lower() in ('true', '1', 'yes')

# Whether to run the webserver
WEBSERVER = os.getenv("WEBSERVER", 'False').lower() in ('true', '1', 'yes')

# Hostname to bind to, default is "everything"
HOST = os.environ.get('HOST', '0.0.0.0')

# Port to bind to, default is 8080
try:
    PORT = int(os.environ.get('PORT', '8080'))
except ValueError:
    raise ValueError("PORT environment variable must be a valid integer")

def get_embed(prefix, data):
    """
    Builds a Discord embed payload summarising pool and vdev health.

    Parameters:
    	prefix (str): Optional string prepended to the embed title when provided.
    	data (dict): Status dictionary containing at minimum `total`, `online`,
        `degraded` and `vdevs`. Supported optional keys:
    		- `alloc_space`, `total_space` (str): human-readable space usage for
              top-level data or per-vdev entries.
    		- `vdevs` (dict): mapping of vdev name -> dict with `total`,
              `online`, `degraded` and optionally `alloc_space`, `total_space`.
    		- `degraded_drives` (list[str]): list of degraded drive identifiers
              to include as a field.
    		- `offline_drives` (list[str]): list of offline drive identifiers to
              include as a field.

    Returns:
    	dict: A Discord embed payload with keys:
    		- `title`: embed title including optional prefix and overall status.
    		- `description`: summary of online/total counts and optional space
              usage, with EXTRA appended when configured.
    		- `color`: integer hex colour representing status.
    		- `fields`: list of field objects describing each vdev, degraded /
              offline sections (if any) and a timestamp.
    """
    title = '\🛑 OFFLINE' if data['total'] and data['online'] + data['degraded'] == 0 else '\✅ ONLINE' if data['online'] == data['total'] else '\⚠️ DEGRADED'
    color = 0xFF0000 if data['total'] and data['online'] + data['degraded'] == 0 else 0x00FF00 if data['online'] == data['total'] else 0xFFA500
    description = f"{data['online']} / {data['total']} online" + ("" if data['online'] + data['degraded'] == data['total'] else f" ({data['online'] - data['degraded']} unavailable)")
    fields = []

    if 'alloc_space' in data and 'total_space' in data:
        description += f", {data['alloc_space']} / {data['total_space']} used"

    for vdev_name, vdev in data['vdevs'].items():
        vdev_icon = '\🛑' if vdev['total'] and vdev['online'] + vdev['degraded'] == 0 else '\✅' if vdev['online'] == vdev['total'] else '\⚠️'
        fields.append({
            "name": f"{vdev_icon} {vdev_name}",
            "value": f"{vdev['online']} / {vdev['total']} online" + ("" if vdev['online'] + vdev['degraded'] == vdev['total'] else f" ({vdev['online'] - vdev['degraded']} unavailable)"),
            "inline": True,
        })
        if 'alloc_space' in vdev and 'total_space' in vdev:
            fields[len(fields) - 1]['value'] += f", {vdev['alloc_space']} / {vdev['total_space']} used"

    if 'degraded_drives' in data and data['degraded_drives']:
        fields.append({
            "name": "\⚠️ Degraded",
            "value": f"```{"\n".join(data['degraded_drives'])}```",
            "inline": False,
        })

    if 'offline_drives' in data and data['offline_drives']:
        fields.append({
            "name": "\🛑 Offline",
            "value": f"```{"\n".join(data['offline_drives'])}```",
            "inline": False,
        })

    fields.append({
        "name": "Timestamp",
        "value": f"<t:{int(time.time())}:F>",
        "inline": False,
    })

    return {
        "title": (prefix + ': ' if prefix else '') + title,
        "description": description + ('\n' + EXTRA if EXTRA else ''),
        "color": color,
        "fields": fields,
    }

# Replace this every time we finish check_status - so always send first message when starting
old_data = {"vdevs": {}}

def check_status(data):
    global old_data

    if old_data != data:
        embeds = []

        logger.info('Status: ' + ('OFFLINE' if data['total'] and data['online'] + data['degraded'] == 0 else 'ONLINE' if data['online'] == data['total'] else 'DEGRADED'))

        if not VERBOSE:
            embeds.append(get_embed('', data))
        else:
            for vdev_name, vdev in data['vdevs'].items():
                if not vdev_name in old_data['vdevs'] or old_data['vdevs'][vdev_name] != vdev:
                    embeds.append(get_embed(vdev_name, vdev))

        old_data = data.copy()

        payload = {
            "embeds": embeds,
            "allowed_mentions": {
                "parse": ["users", "roles", "everyone"],
            },
        }
        headers = {"Content-Type": "application/json"}

        for attempt in range(DISCORD_MAX_RETRIES):
            try:
                response = requests.post(
                    DISCORD_WEBHOOK_URL,
                    data=json.dumps(payload),
                    headers=headers,
                    timeout=10
                )
                if response.status_code == 204:
                    break
                logger.warning(f"Discord API returned status code: {response.status_code}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Attempt {attempt + 1}/{DISCORD_MAX_RETRIES} failed: {e}")
                if attempt < DISCORD_MAX_RETRIES - 1:
                    time.sleep(DISCORD_RETRY_DELAY)
                continue

def check():
    """
    Poll ZFS pool status, build a structured summary of pools/vdevs/drives, an
      forward it to check_status.

    Runs a ZFS status query for the configured POOLS and constructs a nested
    data structure with top-level counters and per-pool entries under `vdevs`.
    Each pool entry contains `total`, `online`, `degraded` counters, a `vdevs`
    mapping of vdev summaries with the same counters, and lists
    `degraded_drives` and `offline_drives` for any non‑online devices. When
    SHOW_SPACE is enabled and space data is present, pool entries also include
    `alloc_space` and `total_space`. The completed structure is passed to
    check_status. Any subprocess.CalledProcessError raised while querying ZFS is
    logged.
    """
    def create_count(data):
        data['total'] = 0
        data['online'] = 0
        data['degraded'] = 0

    def count_by_state(data, obj):
        data['total'] += 1
        if obj['state'] == 'ONLINE' or obj['state'] == 'AVAIL':
            data['online'] += 1
        elif obj['state'] == 'DEGRADED' or obj['state'] == 'INUSE':
            data['degraded'] += 1

    try:
        status = json.loads(subprocess.check_output(f"zpool status -j {POOLS}", shell=True, text=True))
        data = {}

        logger.debug(json.dumps(status))

        create_count(data)

        data['vdevs'] = {}
        for pool_name, pool in status['pools'].items():
            count_by_state(data, pool)

            pool_data = data['vdevs'][pool_name] = {
                "degraded_drives": [],
                "offline_drives": [],
                "vdevs": {},
            }

            if SHOW_SPACE and 'alloc_space' in pool['vdevs'][pool_name]:
                pool_data['alloc_space'] = pool['vdevs'][pool_name]['alloc_space']
                pool_data['total_space'] = pool['vdevs'][pool_name]['total_space']

            create_count(pool_data)

            for vdev_name, vdev in pool['vdevs'][pool_name]['vdevs'].items():
                vdev_data = pool_data['vdevs'][vdev_name] = {}
                create_count(vdev_data)

                for drive_name, drive in vdev['vdevs'].items():
                    count_by_state(pool_data, drive)
                    count_by_state(vdev_data, drive)

                    if drive['state'] == 'ONLINE':
                        continue
                    if drive['vdev_type'] == 'spare':
                        for sub_name, sub_drive in drive['vdevs'].items():
                            if sub_drive['vdev_type'] == 'replacing':
                                for rpl_name, rpl_drive in sub_drive['vdevs'].items():
                                    if rpl_drive['state'] == 'DEGRADED':
                                        pool_data['degraded_drives'].append(rpl_name + " (replacing)")
                                    elif rpl_drive['state'] != 'ONLINE':
                                        pool_data['offline_drives'].append(rpl_name + " (replacing)")
                            elif sub_drive['class'] != 'spare':
                                if sub_drive['state'] == 'DEGRADED':
                                    pool_data['degraded_drives'].append(sub_name)
                                elif sub_drive['state'] != 'ONLINE':
                                    pool_data['offline_drives'].append(sub_name)
                    elif drive['state'] == 'DEGRADED':
                        pool_data['degraded_drives'].append(drive_name)
                    elif drive['state'] != 'ONLINE':
                        pool_data['offline_drives'].append(drive_name)

            if 'logs' in pool:
                vdev_data = pool_data['vdevs']['logs'] = {}
                create_count(vdev_data)
                for _, drive in pool['logs'].items():
                    if drive['vdev_type'] != 'disk':
                        for sub_name, sub_drive in drive['vdevs'].items():
                            count_by_state(vdev_data, sub_drive)
                    else:
                        count_by_state(vdev_data, drive)

            if 'l2cache' in pool:
                vdev_data = pool_data['vdevs']['cache'] = {}
                create_count(vdev_data)
                for _, drive in pool['l2cache'].items():
                    count_by_state(vdev_data, drive)

            if 'spares' in pool:
                vdev_data = pool_data['vdevs']['spares'] = {}
                create_count(vdev_data)
                for _, drive in pool['spares'].items():
                    count_by_state(vdev_data, drive)

        check_status(data)

    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing command: {e}")

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        """
        Handle incoming HTTP GET requests for the monitoring web server.

        Responds with 204 for the special "_ping" path. For other paths, treats
        the URL path segments as keys into the global `old_data` structure and:
        - responds 200 with the JSON-serialized value when the key path is found
          (Content-Type: application/json),
        - responds 404 when any path segment is not present.

        On unexpected errors logs the exception and attempts to respond 500.
        """
        try:
            path = str(self.path)[1:].split('?', 1)[0]

            if path == '_ping':
                self.send_response(204)
                self.end_headers()
                return

            data = old_data
            for key in path.split('/'):
                if not key:
                    continue
                if key not in data:
                    self.send_response(404)
                    self.end_headers()
                    return
                data = data[key]

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode(encoding='utf8'))

        except Exception:
            logger.exception('Web error')
            try:
                self.send_response(500)
                self.end_headers()
            except Exception:
                pass

    def log_request(self, *args):
        """
        Log an HTTP request only when the global logger is set to DEBUG.

        If the global logger's level includes DEBUG, forwards the original
        arguments to BaseHTTPRequestHandler.log_request to produce the usual
        request-line logging; otherwise suppresses the log entry.

        Parameters:
            *args: Positional arguments accepted by BaseHTTPRequestHandler.log_request
        """
        if logger.isEnabledFor(logging.DEBUG):
            super().log_request(*args)

shutdown_event = Event()

def main():
    """
    Start the application: optionally launch the HTTP server and run the
    periodic status loop until shutdown.

    If web server mode is enabled, initialise and start a background
    ThreadingHTTPServer bound to HOST:PORT. Enter a loop that repeatedly calls
    check() and waits for CHECK_DELAY between iterations until shutdown_event is
    set. On any unhandled exception the error is logged and the process exits
    with status code 1.
    """
    try:
        if WEBSERVER:
            logger.info('Starting web server')
            server = http.server.ThreadingHTTPServer((HOST, PORT), Handler)
            thread = threading.Thread(target = server.serve_forever)
            thread.daemon = True
            thread.start()

        while not shutdown_event.is_set():
            check()
            shutdown_event.wait(CHECK_DELAY)

    except Exception:
        logger.exception('Application error')
        sys.exit(1)

def quit(signo, _frame):
    """
    Handle termination signals by logging the interrupt and initiating a
    graceful shutdown.

    Parameters:
        signo (int): Signal number that triggered the handler.
        _frame (frame): Current stack frame at time of signal (unused).
    """
    logger.info("Interrupted by %d, shutting down" % signo)
    shutdown_event.set()

if __name__ == '__main__':
    signal.signal(signal.SIGTERM, quit)
    signal.signal(signal.SIGINT, quit)
    signal.signal(signal.SIGHUP, quit)

    main()
