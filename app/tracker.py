"""Register external IHV-CENIC ChirpStack devices in the Sage node inventory."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
import queue
import re
import threading
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin, urlsplit
from urllib.request import Request, urlopen

import grpc
from chirpstack_api.api import application_pb2, application_pb2_grpc
from chirpstack_api.api import device_pb2, device_pb2_grpc
from chirpstack_api.api import device_profile_pb2, device_profile_pb2_grpc

from .payloads import PayloadError


_HARDWARE_MODEL_PATTERN = re.compile(r"\([^)]*\)")
_HTTP_TIMEOUT_SECONDS = 20
_RPC_TIMEOUT_SECONDS = 20


@dataclass(frozen=True)
class TrackerSettings:
    """Validated endpoints and credentials for the inventory-only Tracker."""

    mqtt_host: str
    chirpstack_api_url: str
    chirpstack_api_key: str
    chirpstack_tenant_id: str
    sage_node_token: str
    node_vsn: str
    mqtt_port: int = 1883
    mqtt_topic: str = "application/+/device/+/event/up"
    mqtt_client_id: str = "ihv-sage-h02a-tracker"
    mqtt_keepalive_seconds: int = 30
    queue_size: int = 1_000
    sage_api_url: str = "https://auth.sagecontinuum.org"

    def __post_init__(self) -> None:
        required = {
            "MQTT host": self.mqtt_host,
            "ChirpStack API URL": self.chirpstack_api_url,
            "ChirpStack API key": self.chirpstack_api_key,
            "ChirpStack tenant ID": self.chirpstack_tenant_id,
            "Sage node token": self.sage_node_token,
            "Sage node VSN": self.node_vsn,
            "MQTT topic": self.mqtt_topic,
            "MQTT client ID": self.mqtt_client_id,
            "Sage API URL": self.sage_api_url,
        }
        for label, value in required.items():
            if not value.strip():
                raise ValueError(f"{label} must not be blank")
        if not 1 <= self.mqtt_port <= 65_535:
            raise ValueError("MQTT port must be between 1 and 65535")
        if self.mqtt_keepalive_seconds <= 0:
            raise ValueError("MQTT keepalive must be positive")
        if self.queue_size <= 0:
            raise ValueError("MQTT queue size must be positive")

    @property
    def chirpstack_endpoint(self) -> str:
        """Return the host and port expected by the gRPC client."""

        parsed = urlsplit(self.chirpstack_api_url)
        endpoint = parsed.netloc or parsed.path
        if not endpoint or ":" not in endpoint:
            raise ValueError("ChirpStack API URL must include a host and port")
        return endpoint.rstrip("/")


@dataclass(frozen=True)
class UplinkIdentity:
    """Identity and source time extracted from a ChirpStack MQTT uplink."""

    dev_eui: str
    device_name: str
    device_profile_id: str
    last_seen_at: str


@dataclass(frozen=True)
class DeviceInventory:
    """Sage inventory fields resolved from one live ChirpStack device."""

    dev_eui: str
    name: str
    battery_level: float
    hardware: str
    hardware_model: str
    hardware_description: str
    last_seen_at: str | None
    margin: float
    expected_uplink_interval_seconds: int
    connection_type: str


class ChirpStackInventory(Protocol):
    """Describe the ChirpStack lookup boundary used by the Tracker worker."""

    def resolve(self, uplink: UplinkIdentity) -> DeviceInventory:
        """Resolve a live MQTT identity against ChirpStack's gRPC API."""

    def all_devices(self) -> tuple[DeviceInventory, ...]:
        """Return every enabled device visible in the configured tenant."""


class SageInventory(Protocol):
    """Describe the Sage registry boundary used by the Tracker worker."""

    def reconcile(self, inventory: DeviceInventory) -> None:
        """Create or update one device and its node connection."""


class JsonTransport(Protocol):
    """Describe the small authenticated JSON transport used by SageRegistry."""

    def request(
        self,
        method: str,
        path: str,
        payload: Mapping[str, object] | None = None,
    ) -> Mapping[str, object] | None:
        """Call one Sage registry route, returning ``None`` for a missing object."""


class ChirpStackApiClient:
    """Read device and profile records using the existing v4 API key."""

    def __init__(
        self,
        settings: TrackerSettings,
        *,
        channel_factory: Callable[[str], Any] = grpc.insecure_channel,
    ) -> None:
        self.settings = settings
        self.channel = channel_factory(settings.chirpstack_endpoint)
        self.applications = application_pb2_grpc.ApplicationServiceStub(self.channel)
        self.devices = device_pb2_grpc.DeviceServiceStub(self.channel)
        self.profiles = device_profile_pb2_grpc.DeviceProfileServiceStub(self.channel)
        self._profile_cache: dict[str, device_profile_pb2.DeviceProfile] = {}

    def _call(self, operation: Callable[..., Any], request: object) -> Any:
        return operation(
            request,
            metadata=(("authorization", f"Bearer {self.settings.chirpstack_api_key}"),),
            timeout=_RPC_TIMEOUT_SECONDS,
        )

    def resolve(self, uplink: UplinkIdentity) -> DeviceInventory:
        """Return Sage-facing inventory without reading LoRaWAN key material."""

        device_response = self._call(
            self.devices.Get,
            device_pb2.GetDeviceRequest(dev_eui=uplink.dev_eui),
        )
        device = device_response.device
        profile_id = device.device_profile_id or uplink.device_profile_id
        profile = self._get_profile(profile_id)
        return self._inventory_from(
            device_response,
            profile,
            fallback_name=uplink.device_name,
            last_seen_at=uplink.last_seen_at,
        )

    def all_devices(self) -> tuple[DeviceInventory, ...]:
        """Read all enabled tenant devices so startup does not wait for every cadence."""

        inventory: list[DeviceInventory] = []
        applications = self._list_all(
            self.applications.List,
            application_pb2.ListApplicationsRequest,
            tenant_id=self.settings.chirpstack_tenant_id,
        )
        for application in applications:
            devices = self._list_all(
                self.devices.List,
                device_pb2.ListDevicesRequest,
                application_id=application.id,
            )
            for item in devices:
                response = self._call(
                    self.devices.Get,
                    device_pb2.GetDeviceRequest(dev_eui=item.dev_eui),
                )
                if response.device.is_disabled:
                    continue
                profile = self._get_profile(response.device.device_profile_id)
                inventory.append(
                    self._inventory_from(
                        response,
                        profile,
                        fallback_name=item.name,
                        last_seen_at=_protobuf_timestamp(response.last_seen_at),
                    )
                )
        return tuple(inventory)

    def _get_profile(self, profile_id: str) -> device_profile_pb2.DeviceProfile:
        profile = self._profile_cache.get(profile_id)
        if profile is None:
            profile = self._call(
                self.profiles.Get,
                device_profile_pb2.GetDeviceProfileRequest(id=profile_id),
            ).device_profile
            self._profile_cache[profile_id] = profile
        return profile

    def _inventory_from(
        self,
        device_response: device_pb2.GetDeviceResponse,
        profile: device_profile_pb2.DeviceProfile,
        *,
        fallback_name: str,
        last_seen_at: str | None,
    ) -> DeviceInventory:
        device = device_response.device
        hardware_model = normalize_hardware_model(profile.name)
        return DeviceInventory(
            dev_eui=device.dev_eui.lower(),
            name=device.name or fallback_name,
            battery_level=float(device_response.device_status.battery_level),
            hardware=profile.name,
            hardware_model=hardware_model,
            hardware_description=profile.description,
            last_seen_at=last_seen_at,
            margin=float(device_response.device_status.margin),
            expected_uplink_interval_seconds=int(profile.uplink_interval),
            connection_type="OTAA" if profile.supports_otaa else "ABP",
        )

    def _list_all(
        self,
        operation: Callable[..., Any],
        request_type: Callable[..., object],
        **filters: str,
    ) -> list[Any]:
        results: list[Any] = []
        while True:
            response = self._call(
                operation,
                request_type(limit=100, offset=len(results), **filters),
            )
            page = list(response.result)
            results.extend(page)
            if not page or len(results) >= response.total_count:
                return results


class SageHttpTransport:
    """Call the Sage Auth inventory API with H02A's node credential."""

    def __init__(self, base_url: str, node_token: str) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.authorization = f"node_auth {node_token}"

    def request(
        self,
        method: str,
        path: str,
        payload: Mapping[str, object] | None = None,
    ) -> Mapping[str, object] | None:
        """Return decoded JSON, treating only HTTP 404 as a missing record."""

        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = Request(
            urljoin(self.base_url, path.lstrip("/")),
            data=body,
            method=method,
            headers={
                "Authorization": self.authorization,
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=_HTTP_TIMEOUT_SECONDS) as response:  # noqa: S310
                decoded = json.load(response)
        except HTTPError as error:
            if error.code == 404 and method == "GET":
                return None
            raise RuntimeError(
                f"Sage inventory request {method} {path} failed with HTTP {error.code}"
            ) from error
        except URLError as error:
            raise RuntimeError(f"Sage inventory request {method} {path} failed") from error
        if not isinstance(decoded, Mapping):
            raise RuntimeError(
                f"Sage inventory request {method} {path} returned non-object JSON"
            )
        return decoded


class SageRegistry:
    """Idempotently synchronize ChirpStack inventory into Sage Auth."""

    def __init__(self, transport: JsonTransport, node_vsn: str) -> None:
        self.transport = transport
        self.node_vsn = node_vsn

    def reconcile(self, inventory: DeviceInventory) -> None:
        """Ensure hardware, device, and node connection records exist and are current."""

        hardware_id = self._ensure_hardware(inventory)
        device_payload: dict[str, object] = {
            "name": inventory.name,
            "battery_level": inventory.battery_level,
        }
        device_path = f"lorawandevices/{quote(inventory.dev_eui, safe='')}/"
        if self.transport.request("GET", device_path) is None:
            self.transport.request(
                "POST",
                "lorawandevices/",
                {
                    **device_payload,
                    "deveui": inventory.dev_eui,
                    "hardware": hardware_id,
                },
            )
        else:
            self.transport.request("PATCH", device_path, device_payload)

        connection_payload: dict[str, object] = {
            "connection_name": inventory.name,
            "last_seen_at": inventory.last_seen_at,
            "margin": inventory.margin,
            "expected_uplink_interval_sec": inventory.expected_uplink_interval_seconds,
            "connection_type": inventory.connection_type,
            "is_active": True,
        }
        connection_path = (
            f"lorawanconnections/{quote(self.node_vsn, safe='')}/"
            f"{quote(inventory.dev_eui, safe='')}/"
        )
        if self.transport.request("GET", connection_path) is None:
            self.transport.request(
                "POST",
                "lorawanconnections/",
                {
                    **connection_payload,
                    "node": self.node_vsn,
                    "lorawan_device": inventory.dev_eui,
                },
            )
        else:
            self.transport.request("PATCH", connection_path, connection_payload)

    def _ensure_hardware(self, inventory: DeviceInventory) -> int:
        hardware_path = f"sensorhardwares/{quote(inventory.hardware_model, safe='')}/"
        existing = self.transport.request("GET", hardware_path)
        response = existing or self.transport.request(
            "POST",
            "sensorhardwares/",
            {
                "hardware": inventory.hardware,
                "hw_model": inventory.hardware_model,
                "description": inventory.hardware_description,
                "capabilities": [35],
            },
        )
        if response is None or not isinstance(response.get("id"), int):
            raise RuntimeError("Sage sensor-hardware response did not include an integer id")
        return response["id"]


@dataclass(frozen=True)
class PendingUplink:
    """MQTT delivery retained until Sage inventory reconciliation completes."""

    message_id: int
    qos: int
    payload: bytes


class MqttInventoryTracker:
    """Consume uplinks and reconcile their device inventory before acknowledging."""

    def __init__(
        self,
        mqtt_module: Any,
        chirpstack: ChirpStackInventory,
        sage: SageInventory,
        settings: TrackerSettings,
    ) -> None:
        self.mqtt_module = mqtt_module
        self.chirpstack = chirpstack
        self.sage = sage
        self.settings = settings
        self.pending: queue.Queue[PendingUplink] = queue.Queue(settings.queue_size)
        self.failure: Exception | None = None
        self._failure_lock = threading.Lock()
        self.worker = threading.Thread(
            target=self._work,
            name="ihv-cenic-chirpstack-tracker-worker",
            daemon=True,
        )
        self.client = self._build_client()

    def _build_client(self) -> Any:
        client = self.mqtt_module.Client(
            callback_api_version=self.mqtt_module.CallbackAPIVersion.VERSION2,
            client_id=self.settings.mqtt_client_id,
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
        """Restore the Tracker's QoS-1 subscription after reconnecting."""

        if getattr(reason_code, "is_failure", bool(reason_code)):
            self._record_failure(RuntimeError(f"MQTT connection failed: {reason_code}"))
            client.disconnect()
            return
        result, _message_id = client.subscribe(self.settings.mqtt_topic, qos=1)
        if result != self.mqtt_module.MQTT_ERR_SUCCESS:
            self._record_failure(RuntimeError(f"MQTT subscription failed: {result}"))
            client.disconnect()
            return
        logging.info("Tracker subscribed to %s at QoS 1", self.settings.mqtt_topic)

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
            logging.warning("Tracker MQTT disconnected unexpectedly: %s", reason_code)

    def on_message(self, client: Any, _userdata: object, message: Any) -> None:
        """Queue an MQTT uplink without acknowledging it yet."""

        try:
            self.pending.put_nowait(
                PendingUplink(message.mid, message.qos, bytes(message.payload))
            )
        except queue.Full:
            self._record_failure(RuntimeError("Tracker MQTT worker queue is full"))
            client.disconnect()

    def process_message(self, message: PendingUplink) -> DeviceInventory:
        """Reconcile one live device, then acknowledge its MQTT delivery."""

        uplink = uplink_identity_from_payload(message.payload)
        inventory = self.chirpstack.resolve(uplink)
        self.sage.reconcile(inventory)
        result = self.client.ack(message.message_id, message.qos)
        if result != self.mqtt_module.MQTT_ERR_SUCCESS:
            raise RuntimeError(f"Tracker MQTT acknowledgement failed: {result}")
        return inventory

    def run(self) -> None:
        """Run until shutdown or a delivery remains unacknowledged after failure."""

        self.reconcile_all()
        self.worker.start()
        self.client.connect(
            self.settings.mqtt_host,
            self.settings.mqtt_port,
            keepalive=self.settings.mqtt_keepalive_seconds,
        )
        self.client.loop_forever(retry_first_connection=True)
        if self.failure is not None:
            raise RuntimeError("Sage inventory tracking stopped before acknowledgement") from (
                self.failure
            )

    def reconcile_all(self) -> int:
        """Register every enabled tenant device before waiting for live uplinks."""

        inventory = self.chirpstack.all_devices()
        for device in inventory:
            self.sage.reconcile(device)
        logging.info("reconciled %s enabled Sage LoRaWAN devices at startup", len(inventory))
        return len(inventory)

    def _work(self) -> None:
        while True:
            message = self.pending.get()
            try:
                inventory = self.process_message(message)
                logging.info(
                    "reconciled Sage LoRaWAN device %s (%s)",
                    inventory.name,
                    inventory.dev_eui,
                )
            except PayloadError as error:
                logging.error("discarding invalid Tracker uplink: %s", error)
                result = self.client.ack(message.message_id, message.qos)
                if result != self.mqtt_module.MQTT_ERR_SUCCESS:
                    self._record_failure(
                        RuntimeError(
                            f"invalid Tracker payload acknowledgement failed: {result}"
                        )
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
                logging.error("Sage inventory tracking failure: %s", error)


def uplink_identity_from_payload(payload: bytes | str) -> UplinkIdentity:
    """Extract the identity required to query ChirpStack from one uplink."""

    try:
        decoded = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as error:
        raise PayloadError("Tracker uplink must be a UTF-8 JSON object") from error
    if not isinstance(decoded, Mapping):
        raise PayloadError("Tracker uplink must be a JSON object")
    info = decoded.get("deviceInfo")
    if not isinstance(info, Mapping):
        raise PayloadError("Tracker uplink deviceInfo must be an object")
    fields: dict[str, str] = {}
    for field in ("devEui", "deviceName", "deviceProfileId"):
        value = info.get(field)
        if not isinstance(value, str) or not value.strip():
            raise PayloadError(f"Tracker uplink deviceInfo.{field} must be text")
        fields[field] = value.strip()
    timestamp = decoded.get("time")
    if not isinstance(timestamp, str):
        raise PayloadError("Tracker uplink time must be RFC 3339 text")
    return UplinkIdentity(
        dev_eui=fields["devEui"].lower(),
        device_name=fields["deviceName"],
        device_profile_id=fields["deviceProfileId"],
        last_seen_at=normalize_rfc3339(timestamp),
    )


def normalize_rfc3339(value: str) -> str:
    """Return an RFC 3339 timestamp at UTC microsecond precision for Django."""

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise PayloadError(f"invalid Tracker RFC 3339 timestamp: {value!r}") from error
    if parsed.tzinfo is None:
        raise PayloadError(f"invalid Tracker RFC 3339 timestamp: {value!r}")
    return (
        parsed.astimezone(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def normalize_hardware_model(value: str) -> str:
    """Match the Sage Tracker's stable 30-character hardware-model lookup key."""

    without_parentheses = _HARDWARE_MODEL_PATTERN.sub("", value).strip()
    normalized = re.sub(r"_+", "_", without_parentheses.replace(" ", "_"))[:30]
    if not normalized:
        raise ValueError("ChirpStack device profile name has no usable hardware model")
    return normalized


def _protobuf_timestamp(value: Any) -> str | None:
    if not value.ListFields():
        return None
    return (
        value.ToDatetime(tzinfo=timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


__all__ = [
    "ChirpStackApiClient",
    "DeviceInventory",
    "MqttInventoryTracker",
    "PendingUplink",
    "SageHttpTransport",
    "SageRegistry",
    "TrackerSettings",
    "UplinkIdentity",
    "normalize_hardware_model",
    "normalize_rfc3339",
    "uplink_identity_from_payload",
]
