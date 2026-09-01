"""Protect external ChirpStack to Sage inventory registration contracts."""

from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
from typing import Any
from urllib.error import HTTPError

from chirpstack_api.api import application_pb2, application_pb2_grpc
from chirpstack_api.api import device_pb2, device_pb2_grpc
from chirpstack_api.api import device_profile_pb2, device_profile_pb2_grpc
import pytest
import yaml

from app.tracker import (
    ChirpStackApiClient,
    DeviceInventory,
    MqttInventoryTracker,
    PendingUplink,
    SageHttpTransport,
    SageRegistry,
    TrackerSettings,
    normalize_hardware_model,
    uplink_identity_from_payload,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _payload() -> bytes:
    return json.dumps(
        {
            "time": "2026-08-20T06:01:02.123456789Z",
            "deviceInfo": {
                "deviceName": "SDI-12-LS-US915-1",
                "devEui": "A8404111F05C5EF9",
                "deviceProfileId": "c5618790-7705-475f-a5ea-5e87816e90ee",
            },
        }
    ).encode()


def _inventory() -> DeviceInventory:
    return DeviceInventory(
        dev_eui="a8404111f05c5ef9",
        name="SDI-12-LS-US915-1",
        battery_level=87.5,
        hardware="SDI-12 (US915)",
        hardware_model="SDI-12",
        hardware_description="IHV-CENIC SDI-12 profile",
        last_seen_at="2026-08-20T06:01:02.123456Z",
        margin=12.0,
        expected_uplink_interval_seconds=600,
        connection_type="OTAA",
    )


def test_uplink_identity_is_canonical_and_django_timestamp_is_bounded() -> None:
    identity = uplink_identity_from_payload(_payload())

    assert identity.dev_eui == "a8404111f05c5ef9"
    assert identity.device_name == "SDI-12-LS-US915-1"
    assert identity.device_profile_id == "c5618790-7705-475f-a5ea-5e87816e90ee"
    assert identity.last_seen_at == "2026-08-20T06:01:02.123456Z"
    assert normalize_hardware_model("SDI-12 (US915)") == "SDI-12"


class _GrpcOperation:
    def __init__(self, response: object) -> None:
        self.response = response
        self.calls: list[tuple[object, object, float]] = []

    def __call__(self, request: object, *, metadata: object, timeout: float) -> object:
        self.calls.append((request, metadata, timeout))
        return self.response


class _DeviceStub:
    def __init__(
        self,
        response: device_pb2.GetDeviceResponse,
        list_response: device_pb2.ListDevicesResponse,
    ) -> None:
        self.Get = _GrpcOperation(response)
        self.List = _GrpcOperation(list_response)


class _ApplicationStub:
    def __init__(self, response: application_pb2.ListApplicationsResponse) -> None:
        self.List = _GrpcOperation(response)


class _ProfileStub:
    def __init__(self, response: device_profile_pb2.GetDeviceProfileResponse) -> None:
        self.Get = _GrpcOperation(response)


def test_chirpstack_client_uses_v4_api_key_and_reads_no_device_keys(monkeypatch: Any) -> None:
    device_response = device_pb2.GetDeviceResponse()
    device_response.device.dev_eui = "a8404111f05c5ef9"
    device_response.device.name = "SDI-12-LS-US915-1"
    device_response.device.device_profile_id = "profile-id"
    device_response.device_status.battery_level = 87.5
    device_response.device_status.margin = 12
    device_response.last_seen_at.FromJsonString("2026-08-20T06:01:02.123456Z")
    applications_response = application_pb2.ListApplicationsResponse(total_count=1)
    applications_response.result.add(id="application-id", name="SDI-12-LS")
    devices_response = device_pb2.ListDevicesResponse(total_count=1)
    devices_response.result.add(
        dev_eui="a8404111f05c5ef9",
        name="SDI-12-LS-US915-1",
    )
    profile_response = device_profile_pb2.GetDeviceProfileResponse()
    profile_response.device_profile.id = "profile-id"
    profile_response.device_profile.name = "SDI-12 (US915)"
    profile_response.device_profile.description = "IHV-CENIC SDI-12 profile"
    profile_response.device_profile.uplink_interval = 600
    profile_response.device_profile.supports_otaa = True
    application_stub = _ApplicationStub(applications_response)
    device_stub = _DeviceStub(device_response, devices_response)
    profile_stub = _ProfileStub(profile_response)
    monkeypatch.setattr(
        application_pb2_grpc,
        "ApplicationServiceStub",
        lambda _channel: application_stub,
    )
    monkeypatch.setattr(device_pb2_grpc, "DeviceServiceStub", lambda _channel: device_stub)
    monkeypatch.setattr(
        device_profile_pb2_grpc,
        "DeviceProfileServiceStub",
        lambda _channel: profile_stub,
    )
    endpoints: list[str] = []
    settings = TrackerSettings(
        mqtt_host="192.168.1.200",
        chirpstack_api_url="http://192.168.1.200:8080",
        chirpstack_api_key="secret-api-key",
        chirpstack_tenant_id="tenant-id",
        sage_node_token="secret-node-token",
        node_vsn="H02A",
    )
    client = ChirpStackApiClient(
        settings,
        channel_factory=lambda endpoint: endpoints.append(endpoint) or object(),
    )

    inventory = client.resolve(uplink_identity_from_payload(_payload()))
    startup_inventory = client.all_devices()

    assert endpoints == ["192.168.1.200:8080"]
    assert inventory == _inventory()
    assert startup_inventory == (_inventory(),)
    for operation in (device_stub.Get, profile_stub.Get):
        assert operation.calls[0][1] == (("authorization", "Bearer secret-api-key"),)


class _RegistryTransport:
    def __init__(self, *, existing: bool = False) -> None:
        self.existing = existing
        self.calls: list[tuple[str, str, object]] = []

    def request(self, method: str, path: str, payload: object = None) -> object:
        self.calls.append((method, path, payload))
        if method == "GET" and path.startswith("sensorhardwares/"):
            return {"id": 35} if self.existing else None
        if method == "POST" and path == "sensorhardwares/":
            return {"id": 35}
        if method == "GET":
            return {"present": True} if self.existing else None
        return {"saved": True}


def test_registry_creates_inventory_without_copying_lorawan_keys() -> None:
    transport = _RegistryTransport()

    SageRegistry(transport, "H02A").reconcile(_inventory())

    assert [(method, path) for method, path, _payload in transport.calls] == [
        ("GET", "sensorhardwares/SDI-12/"),
        ("POST", "sensorhardwares/"),
        ("GET", "lorawandevices/a8404111f05c5ef9/"),
        ("POST", "lorawandevices/"),
        ("GET", "lorawanconnections/H02A/a8404111f05c5ef9/"),
        ("POST", "lorawanconnections/"),
    ]
    assert all("lorawankeys" not in path for _method, path, _payload in transport.calls)
    hardware_payload = transport.calls[1][2]
    assert hardware_payload == {
        "hardware": "SDI-12 (US915)",
        "hw_model": "SDI-12",
        "description": "IHV-CENIC SDI-12 profile",
        "capabilities": [35],
    }
    connection_payload = transport.calls[-1][2]
    assert connection_payload == {
        "connection_name": "SDI-12-LS-US915-1",
        "last_seen_at": "2026-08-20T06:01:02.123456Z",
        "margin": 12.0,
        "expected_uplink_interval_sec": 600,
        "connection_type": "OTAA",
        "is_active": True,
        "node": "H02A",
        "lorawan_device": "a8404111f05c5ef9",
    }


def test_registry_patches_existing_device_and_connection() -> None:
    transport = _RegistryTransport(existing=True)

    SageRegistry(transport, "H02A").reconcile(_inventory())

    assert [(method, path) for method, path, _payload in transport.calls] == [
        ("GET", "sensorhardwares/SDI-12/"),
        ("GET", "lorawandevices/a8404111f05c5ef9/"),
        ("PATCH", "lorawandevices/a8404111f05c5ef9/"),
        ("GET", "lorawanconnections/H02A/a8404111f05c5ef9/"),
        ("PATCH", "lorawanconnections/H02A/a8404111f05c5ef9/"),
    ]


def test_http_transport_authenticates_and_only_get_uses_404_as_missing(
    monkeypatch: Any,
) -> None:
    requests: list[object] = []

    def successful(request: object, *, timeout: int) -> BytesIO:
        requests.append(request)
        assert timeout == 20
        return BytesIO(b'{"id": 35}')

    monkeypatch.setattr("app.tracker.urlopen", successful)
    transport = SageHttpTransport("https://auth.sagecontinuum.org", "node-token")

    assert transport.request("GET", "sensorhardwares/SDI-12/") == {"id": 35}
    request = requests[0]
    assert request.full_url == "https://auth.sagecontinuum.org/sensorhardwares/SDI-12/"
    assert request.get_header("Authorization") == "node_auth node-token"

    def missing(request: object, *, timeout: int) -> BytesIO:
        raise HTTPError(request.full_url, 404, "not found", {}, None)

    monkeypatch.setattr("app.tracker.urlopen", missing)
    assert transport.request("GET", "lorawandevices/missing/") is None
    with pytest.raises(RuntimeError, match="POST lorawandevices/ failed with HTTP 404"):
        transport.request("POST", "lorawandevices/", {"deveui": "missing"})


class _FakeClient:
    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs
        self.acknowledgements: list[tuple[int, int]] = []

    def manual_ack_set(self, _enabled: bool) -> None:
        pass

    def reconnect_delay_set(self, *, min_delay: int, max_delay: int) -> None:
        pass

    def ack(self, message_id: int, qos: int) -> int:
        self.acknowledgements.append((message_id, qos))
        return 0


class _FakeMqtt:
    class CallbackAPIVersion:
        VERSION2 = "v2"

    MQTTv311 = "v311"
    MQTT_ERR_SUCCESS = 0

    def __init__(self) -> None:
        self.client: _FakeClient | None = None

    def Client(self, **kwargs: object) -> _FakeClient:  # noqa: N802 - mirrors Paho API
        self.client = _FakeClient(**kwargs)
        return self.client


class _ChirpStack:
    def resolve(self, _uplink: object) -> DeviceInventory:
        return _inventory()

    def all_devices(self) -> tuple[DeviceInventory, ...]:
        return (_inventory(),)


class _Sage:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.records: list[DeviceInventory] = []

    def reconcile(self, inventory: DeviceInventory) -> None:
        if self.fail:
            raise ConnectionError("Sage inventory unavailable")
        self.records.append(inventory)


def _settings() -> TrackerSettings:
    return TrackerSettings(
        mqtt_host="192.168.1.200",
        chirpstack_api_url="http://192.168.1.200:8080",
        chirpstack_api_key="secret-api-key",
        chirpstack_tenant_id="tenant-id",
        sage_node_token="secret-node-token",
        node_vsn="H02A",
    )


def test_runtime_acknowledges_only_after_sage_inventory_accepts_device() -> None:
    mqtt = _FakeMqtt()
    sage = _Sage()
    tracker = MqttInventoryTracker(mqtt, _ChirpStack(), sage, _settings())
    assert mqtt.client is not None

    inventory = tracker.process_message(PendingUplink(42, 1, _payload()))

    assert inventory == _inventory()
    assert sage.records == [_inventory()]
    assert mqtt.client.acknowledgements == [(42, 1)]


def test_runtime_reconciles_complete_inventory_before_live_uplinks() -> None:
    mqtt = _FakeMqtt()
    sage = _Sage()
    tracker = MqttInventoryTracker(mqtt, _ChirpStack(), sage, _settings())

    assert tracker.reconcile_all() == 1
    assert sage.records == [_inventory()]


def test_runtime_leaves_delivery_unacknowledged_when_registry_fails() -> None:
    mqtt = _FakeMqtt()
    tracker = MqttInventoryTracker(mqtt, _ChirpStack(), _Sage(fail=True), _settings())
    assert mqtt.client is not None

    with pytest.raises(ConnectionError, match="Sage inventory unavailable"):
        tracker.process_message(PendingUplink(43, 1, _payload()))

    assert mqtt.client.acknowledgements == []


def test_tracker_deployment_is_h02a_scoped_and_secret_backed() -> None:
    deployment = yaml.safe_load((REPO_ROOT / "deploy/tracker-deployment.yaml").read_text())
    pod = deployment["spec"]["template"]["spec"]
    container = pod["containers"][0]

    assert deployment["metadata"]["name"] == "ihv-cenic-chirpstack-tracker"
    assert deployment["spec"]["strategy"] == {"type": "Recreate"}
    assert pod["nodeSelector"] == {"zone": "core"}
    assert "ihv-cenic-chirpstack-devices:0.2.0" in container["image"]
    assert "--mode" in container["args"]
    assert "tracker" in container["args"]
    assert "192.168.1.200" in container["args"]
    assert "http://137.164.38.253:8080" in container["args"]
    assert "68523723-483d-484e-a36b-8ae3ddc3fcd3" in container["args"]
    assert "Bearer " not in " ".join(container["args"])
    assert "node_auth " not in " ".join(container["args"])
    secrets = {volume["secret"]["secretName"] for volume in pod["volumes"]}
    assert secrets == {"django-token", "ihv-cenic-chirpstack-api"}
    assert container["securityContext"]["readOnlyRootFilesystem"] is True
    assert container["securityContext"]["runAsNonRoot"] is True
