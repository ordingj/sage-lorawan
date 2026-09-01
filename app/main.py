"""Run the IHV-CENIC ChirpStack-to-Sage MQTT forwarder."""

from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
from typing import Sequence

import paho.mqtt.client as mqtt
from waggle.plugin import Plugin

from .runtime import ForwarderSettings, MqttForwarder
from .tracker import (
    ChirpStackApiClient,
    MqttInventoryTracker,
    SageHttpTransport,
    SageRegistry,
    TrackerSettings,
)


def build_parser() -> argparse.ArgumentParser:
    """Return the Sage job command-line contract."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("forward", "tracker"), default="forward")
    parser.add_argument("--mqtt-host", required=True)
    parser.add_argument("--mqtt-port", type=int, default=1883)
    parser.add_argument(
        "--mqtt-topic",
        default="application/+/device/+/event/up",
    )
    parser.add_argument("--mqtt-client-id", default="ihv-sage-h02a")
    parser.add_argument("--mqtt-keepalive", type=int, default=30)
    parser.add_argument("--queue-size", type=int, default=1_000)
    parser.add_argument(
        "--chirpstack-api-url",
        default=os.getenv("CHIRPSTACK_API_URL", ""),
    )
    parser.add_argument(
        "--chirpstack-api-key-file",
        type=Path,
        default=os.getenv("CHIRPSTACK_API_KEY_FILE", ""),
    )
    parser.add_argument(
        "--chirpstack-tenant-id",
        default=os.getenv("CHIRPSTACK_TENANT_ID", ""),
    )
    parser.add_argument(
        "--sage-api-url",
        default=os.getenv("SAGE_API_URL", "https://auth.sagecontinuum.org"),
    )
    parser.add_argument(
        "--sage-node-token-file",
        type=Path,
        default=os.getenv("SAGE_NODE_TOKEN_FILE", ""),
    )
    parser.add_argument("--node-vsn", default=os.getenv("WAGGLE_NODE_VSN", ""))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--debug", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run measurement forwarding or inventory-only Tracker reconciliation."""

    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    if args.mode == "tracker":
        if args.dry_run:
            raise ValueError("--dry-run is available only in forward mode")
        chirpstack_key = _read_secret(args.chirpstack_api_key_file, "ChirpStack API key")
        node_token = _read_secret(args.sage_node_token_file, "Sage node token")
        settings = TrackerSettings(
            mqtt_host=args.mqtt_host,
            mqtt_port=args.mqtt_port,
            mqtt_topic=args.mqtt_topic,
            mqtt_client_id=args.mqtt_client_id,
            mqtt_keepalive_seconds=args.mqtt_keepalive,
            queue_size=args.queue_size,
            chirpstack_api_url=args.chirpstack_api_url,
            chirpstack_api_key=chirpstack_key,
            chirpstack_tenant_id=args.chirpstack_tenant_id,
            sage_api_url=args.sage_api_url,
            sage_node_token=node_token,
            node_vsn=args.node_vsn,
        )
        chirpstack = ChirpStackApiClient(settings)
        sage = SageRegistry(
            SageHttpTransport(settings.sage_api_url, settings.sage_node_token),
            settings.node_vsn,
        )
        MqttInventoryTracker(mqtt, chirpstack, sage, settings).run()
    else:
        settings = ForwarderSettings(
            host=args.mqtt_host,
            port=args.mqtt_port,
            topic=args.mqtt_topic,
            client_id=args.mqtt_client_id,
            keepalive_seconds=args.mqtt_keepalive,
            queue_size=args.queue_size,
            dry_run=args.dry_run,
        )
        with Plugin() as plugin:
            MqttForwarder(mqtt, plugin, settings).run()
    return 0


def _read_secret(path: Path, label: str) -> str:
    if not path.is_file():
        raise ValueError(f"{label} file does not exist: {path}")
    value = path.read_text(encoding="utf-8").strip()
    if not value:
        raise ValueError(f"{label} file must not be empty")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
