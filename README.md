# zfs-discord-alerts

[![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/Rycochet/zfs-discord-alerts/publish.yml)](https://github.com/Rycochet/zfs-discord-alerts/actions/workflows/publish.yml) ![GitHub contributors](https://img.shields.io/github/contributors/Rycochet/zfs-discord-alerts) [![Docker Pulls](https://img.shields.io/docker/pulls/rycochet/zfs-discord-alerts) ![Docker Image Size](https://img.shields.io/docker/image-size/rycochet/zfs-discord-alerts)](https://hub.docker.com/r/rycochet/zfs-discord-alerts/)

Monitor your ZFS pools effortlessly and receive near real-time alerts in Discord.

## Features

- **Real-Time Reporting**: Runs every 5 minutes and tells discord instantly when something changes.
- **Discord Notifications**: Sends event alerts to a Discord channel using webhooks (no bot required).
- **Rich Embeds**: Optional detailed information.
- **Configurable**: Easily customize alerts using a ENV vars.
- **Dockerized**: Run the script as a background service using Docker Compose.

## Prerequisites

- Docker and Docker Compose installed on your system.
- A Discord account and a webhook URL from your server.

## Usage

1. **Create a `compose.yaml` file**

    An example [compose.yaml](compose.yaml) file is included, make sure you replace the `DISCORD_WEBHOOK_URL` value with one you [obtained from Discord](https://discordjs.guide/legacy/popular-topics/webhooks):

    ```yaml
    services:
        zfs-discord-alerts:
            container_name: zfs-discord-alerts
            image: ghcr.io/rycochet/zfs-discord-alerts:latest
            restart: unless-stopped
            devices:
                - "/dev/zfs:/dev/zfs"
            environment:
                DISCORD_WEBHOOK_URL: "https://discord.com/api/webhooks/..."
    ```

1. **Start the Service**

    Use Docker Compose to start the service in the background:

    ```bash
    docker-compose up -d
    ```

1. **Trigger ZFS Events**

    Unplug a drive and plug it back in...

    ...Seriously, don't do this - it just works!

1. **Check Discord**

    Notifications will appear in the designated Discord channel with details when something in the pools changes.

    There will be an initial message when starting, even if it only says that everything is `ONLINE` (healthy).

### Troubleshooting

- Ensure Docker and Docker Compose are running correctly.
- Verify that the Discord webhook URL is correct and active.
- Check for any errors in the container logs:

    ```bash
    docker logs zfs-discord-alerts
    ```

## Environment Variables

| Name | Definition | Default |
| --- | --- | --- |
| `CHECK_DELAY` | The number of seconds between checks. | `300` |
| `DISCORD_WEBHOOK_URL` | **Required** <br> The full [webhook URL](https://discordjs.guide/legacy/popular-topics/webhooks) from Discord. | |
| `EXTRA` | A string to send with every alert, perfect for sending @mentions for people. You need to [obtain the ID](https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID) and format as `<@USER_ID>` or `<@&ROLE_ID>`, but can put any text here. | |
| `LOG_LEVEL` | How much to log: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` | `INFO` |
| `POOLS` | A space separated list of pools to check, by default it will check everything. | |
| `SHOW_SPACE` | Whether to show the space used, this will send an update to Discord when it changes at about 0.1 units (Gb / Tb / Pb etc). (`True` / `False`) | `False` |
| `VERBOSE` | Provide more detail for the Discord messages. (`True` / `False`) | `False` |
