"""Own the persistent MQTT session and post-publish acknowledgements."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import queue
import threading
from typing import Any, Protocol

from .payloads import PayloadError, measurements_from_payload


class SagePublisher(Protocol):
    """Describe the PyWaggle publication boundary used by the worker."""

    def publish(
        self,
        name: str,
        value: bool | int | float | str,
        *,
        timestamp: int,
        meta: dict[str, str],
    ) -> Any:
        """Publish one timestamped measurement to the Sage node."""


@dataclass(frozen=True)
class ForwarderSettings:
    """Validated MQTT source and persistent subscriber settings."""

    host: str
    port: int = 1883
    topic: str = "application/+/device/+/event/up"
    client_id: str = "ihv-sage-h02a"
    keepalive_seconds: int = 30
    queue_size: int = 1_000
    dry_run: bool = False

    def __post_init__(self) -> None:
        if not self.host.strip():
            raise ValueError("MQTT host must not be blank")
        if not 1 <= self.port <= 65_535:
            raise ValueError("MQTT port must be between 1 and 65535")
        if not self.topic.strip():
            raise ValueError("MQTT topic must not be blank")
        if not self.client_id.strip():
            raise ValueError("MQTT client ID must not be blank")
        if self.keepalive_seconds <= 0:
            raise ValueError("MQTT keepalive must be positive")
        if self.queue_size <= 0:
            raise ValueError("MQTT queue size must be positive")


@dataclass(frozen=True)
class PendingMessage:
    """MQTT delivery retained until Sage accepts every decoded scalar."""

    message_id: int
    qos: int
    payload: bytes


class MqttForwarder:
    """Bridge QoS-1 ChirpStack messages into Sage without early PUBACKs."""

    def __init__(
        self,
        mqtt_module: Any,
        publisher: SagePublisher,
        settings: ForwarderSettings,
    ) -> None:
        self.mqtt_module = mqtt_module
        self.publisher = publisher
        self.settings = settings
        self.pending: queue.Queue[PendingMessage] = queue.Queue(settings.queue_size)
        self.failure: Exception | None = None
        self._failure_lock = threading.Lock()
        self.worker = threading.Thread(
            target=self._work,
            name="ihv-cenic-chirpstack-devices-worker",
            daemon=True,
        )
        self.client = self._build_client()

    def _build_client(self) -> Any:
        client = self.mqtt_module.Client(
            callback_api_version=self.mqtt_module.CallbackAPIVersion.VERSION2,
            client_id=self.settings.client_id,
            clean_session=False,
            protocol=self.mqtt_module.MQTTv311,
        )
        client.manual_ack_set(True)
        client.reconnect_delay_set(min_delay=1, max_delay=30)
        client.on_connect = self.on_connect
        client.on_disconnect = self.on_disconnect
        client.on_message = self.on_message
        return client

    def on_connect(
        self,
        client: Any,
        _userdata: object,
        _flags: object,
        reason_code: Any,
        _properties: object,
    ) -> None:
        """Restore the QoS-1 subscription after every broker connection."""

        if getattr(reason_code, "is_failure", bool(reason_code)):
            self._record_failure(RuntimeError(f"MQTT connection failed: {reason_code}"))
            client.disconnect()
            return
        result, _message_id = client.subscribe(self.settings.topic, qos=1)
        if result != self.mqtt_module.MQTT_ERR_SUCCESS:
            self._record_failure(RuntimeError(f"MQTT subscription failed: {result}"))
            client.disconnect()
            return
        logging.info("subscribed to %s at QoS 1", self.settings.topic)

    @staticmethod
    def on_disconnect(
        _client: Any,
        _userdata: object,
        _disconnect_flags: object,
        reason_code: Any,
        _properties: object,
    ) -> None:
        """Report unexpected disconnects while Paho handles reconnection."""

        if getattr(reason_code, "is_failure", bool(reason_code)):
            logging.warning("MQTT disconnected unexpectedly: %s", reason_code)

    def on_message(self, client: Any, _userdata: object, message: Any) -> None:
        """Queue an MQTT delivery without acknowledging it to the source broker."""

        try:
            self.pending.put_nowait(
                PendingMessage(message.mid, message.qos, bytes(message.payload))
            )
        except queue.Full:
            self._record_failure(RuntimeError("MQTT worker queue is full"))
            client.disconnect()

    def process_message(self, message: PendingMessage) -> int:
        """Publish every decoded scalar, then acknowledge the MQTT delivery."""

        measurements = measurements_from_payload(message.payload)
        for measurement in measurements:
            if self.settings.dry_run:
                logging.info(
                    "dry run: %s %s %s",
                    measurement.metadata["deviceName"],
                    measurement.name,
                    measurement.value,
                )
                continue
            self.publisher.publish(
                measurement.name,
                measurement.value,
                timestamp=measurement.timestamp_ns,
                meta=dict(measurement.metadata),
            )
        result = self.client.ack(message.message_id, message.qos)
        if result != self.mqtt_module.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"MQTT acknowledgement failed: {result}")
        return len(measurements)

    def run(self) -> None:
        """Run the subscriber until shutdown or an unacknowledged delivery failure."""

        self.worker.start()
        self.client.connect(
            self.settings.host,
            self.settings.port,
            keepalive=self.settings.keepalive_seconds,
        )
        self.client.loop_forever(retry_first_connection=True)
        if self.failure is not None:
            raise RuntimeError(
                "Sage MQTT forwarding stopped before acknowledgement"
            ) from self.failure

    def _work(self) -> None:
        while True:
            message = self.pending.get()
            try:
                count = self.process_message(message)
                logging.info("forwarded %s Sage measurements", count)
            except PayloadError as error:
                logging.error("discarding invalid ChirpStack uplink: %s", error)
                result = self.client.ack(message.message_id, message.qos)
                if result != self.mqtt_module.MQTT_ERR_SUCCESS:
                    self._record_failure(
                        RuntimeError(f"invalid MQTT payload acknowledgement failed: {result}")
                    )
                    self.client.disconnect()
                    return
            except Exception as error:
                self._record_failure(error)
                self.client.disconnect()
                return
            finally:
                self.pending.task_done()

    def _record_failure(self, error: Exception) -> None:
        with self._failure_lock:
            if self.failure is None:
                self.failure = error
                logging.error("Sage MQTT forwarding failure: %s", error)


__all__ = [
    "ForwarderSettings",
    "MqttForwarder",
    "PendingMessage",
    "SagePublisher",
]
