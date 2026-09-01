"""Run the IHV ChirpStack-to-Sage MQTT forwarder."""

from __future__ import annotations

import argparse
import logging
from typing import Sequence

import paho.mqtt.client as mqtt
from waggle.plugin import Plugin

from .runtime import ForwarderSettings, MqttForwarder


def build_parser() -> argparse.ArgumentParser:
    """Return the Sage job command-line contract."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mqtt-host", required=True)
    parser.add_argument("--mqtt-port", type=int, default=1883)
    parser.add_argument(
        "--mqtt-topic",
        default="application/+/device/+/event/up",
    )
    parser.add_argument("--mqtt-client-id", default="ihv-sage-h02a")
    parser.add_argument("--mqtt-keepalive", type=int, default=30)
    parser.add_argument("--queue-size", type=int, default=1_000)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--debug", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Validate settings and bridge MQTT messages through PyWaggle."""

    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
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


if __name__ == "__main__":
    raise SystemExit(main())
