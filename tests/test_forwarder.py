"""Protect the IHV-CENIC ChirpStack-to-Sage payload and MQTT contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from PIL import Image

from app.payloads import PayloadError, measurements_from_payload
from app.runtime import ForwarderSettings, MqttForwarder, PendingMessage


REPO_ROOT = Path(__file__).resolve().parents[1]


def _payload() -> dict[str, Any]:
    return {
        "deduplicationId": "30270303-19fc-49fc-99a0-0d0d09374a1c",
        "time": "2026-08-20T06:01:02.123456789Z",
        "deviceInfo": {
            "tenantId": "7161e400-2e8f-4b5f-9b04-9481f09ddcbb",
            "tenantName": "IHV",
            "applicationId": "a511c18f-3f42-448d-894e-ebd34ded80de",
            "applicationName": "SDI-12-LS",
            "deviceProfileId": "c5618790-7705-475f-a5ea-5e87816e90ee",
            "deviceProfileName": "SDI-12",
            "deviceName": "SDI-12-LS-US915-1",
            "devEui": "A8404111F05C5EF9",
            "tags": {"Block Name": "Block 1"},
        },
        "devAddr": "01a2b3c4",
        "adr": True,
        "dr": 3,
        "fCnt": 9921,
        "fPort": 2,
        "confirmed": False,
        "object": {
            "BatV": 3.42,
            "flags": [True, "ok"],
            "location": {"latitude": 38.5, "longitude": -122.9},
            "missing": None,
        },
        "rxInfo": [{"rssi": -91, "snr": 8.5}, {"rssi": -96, "snr": 9.0}],
    }


def test_payload_flattens_existing_object_and_preserves_source_identity() -> None:
    records = measurements_from_payload(json.dumps(_payload()).encode())
    records_by_name = {record.name: record for record in records}

    assert {name: record.value for name, record in records_by_name.items()} == {
        "batv": 3.42,
        "flags_0": True,
        "flags_1": "ok",
        "location_latitude": 38.5,
        "location_longitude": -122.9,
    }
    assert {record.timestamp_ns for record in records} == {1_787_205_662_123_456_789}
    metadata = records_by_name["batv"].metadata
    assert metadata["deviceName"] == "SDI-12-LS-US915-1"
    assert metadata["devEui"] == "a8404111f05c5ef9"
    assert metadata["device_label"] == "Soil Matric Sensor - P"
    assert metadata["block"] == "P"
    assert metadata["slope"] == "upslope"
    assert metadata["latitude"] == "38.461576122"
    assert metadata["longitude"] == "-122.898461072"
    assert metadata["fCnt"] == "9921"
    assert metadata["block_name_tag"] == "Block 1"
    assert metadata["rssi"] == "-91"
    assert metadata["snr"] == "9.0"
    assert metadata["adr"] == "true"
    assert metadata["confirmed"] == "false"
    assert metadata["units"] == "V"
    assert all(isinstance(value, str) for value in metadata.values())
    assert "units" not in records_by_name["flags_0"].metadata
    assert "units" not in records_by_name["location_latitude"].metadata
    assert "data" not in metadata


def test_payload_leaves_field_metadata_absent_for_unmapped_device() -> None:
    payload = _payload()
    payload["deviceInfo"]["devEui"] = "0000000000000001"

    metadata = measurements_from_payload(json.dumps(payload))[0].metadata

    assert not {"device_label", "block", "slope", "latitude", "longitude"} & metadata.keys()


def test_payload_adds_units_to_known_physical_measurements_only() -> None:
    payload = _payload()
    payload["deviceInfo"]["deviceProfileName"] = "EM500-CO2"
    payload["object"] = {
        "battery": 91,
        "co2": 476,
        "humidity": 58.5,
        "pressure": 1012.4,
        "temperature": 24.7,
        "temp_DS18B20": 23.9,
        "temp_SOIL4": 22.6,
        "conduct_SOIL4": 148,
        "water_SOIL4": 31.2,
        "uv_a_irradiance_w_m2": 4.25,
        "node_type": 1,
    }

    units = {
        record.name: record.metadata.get("units")
        for record in measurements_from_payload(json.dumps(payload))
    }

    assert units == {
        "battery": "%",
        "co2": "ppm",
        "humidity": "%RH",
        "pressure": "hPa",
        "temperature": "°C",
        "temp_ds18b20": "°C",
        "temp_soil4": "°C",
        "conduct_soil4": "µS/cm",
        "water_soil4": "%",
        "uv_a_irradiance_w_m2": "W/m²",
        "node_type": None,
    }


def test_payload_uses_device_specific_pressure_units_for_current_and_history() -> None:
    payload = _payload()
    payload["deviceInfo"]["applicationName"] = "EM500-PP-4842"
    payload["deviceInfo"]["deviceProfileName"] = "EM500-PP"
    payload["deviceInfo"]["deviceName"] = "EM500-PP-4842"
    payload["object"] = {
        "pressure": 216,
        "history": [{"timestamp": 1_666_938_125, "pressure": 210}],
    }

    units = {
        record.name: record.metadata.get("units")
        for record in measurements_from_payload(json.dumps(payload))
    }

    assert units == {
        "pressure": "kPa",
        "history_0_timestamp": None,
        "history_0_pressure": "kPa",
    }


def test_payload_resolves_sensecap_units_from_sibling_measurement_ids() -> None:
    payload = _payload()
    payload["deviceInfo"]["deviceProfileName"] = "SenseCAP S2103"
    payload["object"] = {
        "messages": [
            {"measurementId": 4097, "measurementValue": 22.5},
            {"measurementId": 4098, "measurementValue": 61.2},
            {"measurementId": 4100, "measurementValue": 488},
            {"battery": 94},
            {"measurementId": 9999, "measurementValue": 3},
        ]
    }

    units = {
        record.name: record.metadata.get("units")
        for record in measurements_from_payload(json.dumps(payload))
    }

    assert units["messages_0_measurementvalue"] == "°C"
    assert units["messages_1_measurementvalue"] == "%RH"
    assert units["messages_2_measurementvalue"] == "ppm"
    assert units["messages_3_battery"] == "%"
    assert units["messages_4_measurementvalue"] is None
    assert units["messages_0_measurementid"] is None


def test_payload_preserves_nanoseconds_across_timezone_offsets() -> None:
    payload = _payload()
    payload["time"] = "2026-08-19T23:01:02.123456789-07:00"

    assert measurements_from_payload(json.dumps(payload))[0].timestamp_ns == (
        1_787_205_662_123_456_789
    )


def test_payload_rejects_impossible_rfc3339_date_as_permanent_error() -> None:
    payload = _payload()
    payload["time"] = "2026-13-20T06:01:02Z"

    with pytest.raises(PayloadError, match="invalid RFC 3339 timestamp"):
        measurements_from_payload(json.dumps(payload))


@pytest.mark.parametrize(
    ("object_payload", "message"),
    (
        ({"A-B": 1, "a_b": 2}, "collide after Sage normalization"),
        ({"bad": float("nan")}, "must be finite"),
        ({}, "contains no scalar measurements"),
    ),
)
def test_payload_rejects_ambiguous_or_invalid_decoded_objects(
    object_payload: object,
    message: str,
) -> None:
    payload = _payload()
    payload["object"] = object_payload

    with pytest.raises(PayloadError, match=message):
        measurements_from_payload(json.dumps(payload))


class _ReasonCode:
    is_failure = False

    def __bool__(self) -> bool:
        return self.is_failure


class _FakeClient:
    def __init__(self, **kwargs: Any) -> None:
        self.kwargs = kwargs
        self.manual_ack = False
        self.reconnect_delays: tuple[int, int] | None = None
        self.acknowledgements: list[tuple[int, int]] = []
        self.subscriptions: list[tuple[str, int]] = []
        self.disconnected = False

    def manual_ack_set(self, enabled: bool) -> None:
        self.manual_ack = enabled

    def reconnect_delay_set(self, *, min_delay: int, max_delay: int) -> None:
        self.reconnect_delays = (min_delay, max_delay)

    def subscribe(self, topic: str, *, qos: int) -> tuple[int, int]:
        self.subscriptions.append((topic, qos))
        return 0, 1

    def ack(self, message_id: int, qos: int) -> int:
        self.acknowledgements.append((message_id, qos))
        return 0

    def disconnect(self) -> None:
        self.disconnected = True


class _FakeMqtt:
    class CallbackAPIVersion:
        VERSION2 = "v2"

    MQTTv311 = "v311"
    MQTT_ERR_SUCCESS = 0

    def __init__(self) -> None:
        self.client: _FakeClient | None = None

    def Client(self, **kwargs: Any) -> _FakeClient:  # noqa: N802 - mirrors Paho API
        self.client = _FakeClient(**kwargs)
        return self.client


class _Publisher:
    def __init__(self, *, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[str, object, int, dict[str, str]]] = []

    def publish(
        self,
        name: str,
        value: object,
        *,
        timestamp: int,
        meta: dict[str, str],
    ) -> None:
        if self.fail:
            raise ConnectionError("Sage unavailable")
        if not all(
            isinstance(key, str) and isinstance(value, str) for key, value in meta.items()
        ):
            raise TypeError("Meta must be a dictionary of strings to strings.")
        self.calls.append((name, value, timestamp, meta))


def test_runtime_uses_persistent_qos1_session_and_acks_after_publish() -> None:
    mqtt = _FakeMqtt()
    publisher = _Publisher()
    forwarder = MqttForwarder(
        mqtt,
        publisher,
        ForwarderSettings(host="192.168.1.200"),
    )
    assert mqtt.client is not None

    assert mqtt.client.kwargs == {
        "callback_api_version": "v2",
        "client_id": "ihv-sage-h02a",
        "clean_session": False,
        "protocol": "v311",
    }
    assert mqtt.client.manual_ack is True
    forwarder.on_connect(mqtt.client, None, None, _ReasonCode(), None)
    assert mqtt.client.subscriptions == [("application/+/device/+/event/up", 1)]

    count = forwarder.process_message(PendingMessage(17, 1, json.dumps(_payload()).encode()))

    assert count == 5
    assert [call[0] for call in publisher.calls] == [
        "batv",
        "flags_0",
        "flags_1",
        "location_latitude",
        "location_longitude",
    ]
    assert mqtt.client.acknowledgements == [(17, 1)]


def test_runtime_does_not_ack_when_sage_publication_fails() -> None:
    mqtt = _FakeMqtt()
    forwarder = MqttForwarder(
        mqtt,
        _Publisher(fail=True),
        ForwarderSettings(host="192.168.1.200"),
    )
    assert mqtt.client is not None

    with pytest.raises(ConnectionError, match="Sage unavailable"):
        forwarder.process_message(PendingMessage(18, 1, json.dumps(_payload()).encode()))

    assert mqtt.client.acknowledgements == []


def test_runtime_stops_after_a_rejected_mqtt_connection() -> None:
    mqtt = _FakeMqtt()
    forwarder = MqttForwarder(
        mqtt,
        _Publisher(),
        ForwarderSettings(host="192.168.1.200"),
    )
    assert mqtt.client is not None
    reason_code = _ReasonCode()
    reason_code.is_failure = True

    forwarder.on_connect(mqtt.client, None, None, reason_code, None)

    assert isinstance(forwarder.failure, RuntimeError)
    assert mqtt.client.disconnected is True


def test_bundle_pins_contract_and_targets_only_h02a() -> None:
    requirements = (REPO_ROOT / "requirements.txt").read_text()
    dockerfile = (REPO_ROOT / "Dockerfile").read_text()
    dockerignore = (REPO_ROOT / ".dockerignore").read_text()
    manifest = yaml.safe_load((REPO_ROOT / "sage.yaml").read_text())
    job = yaml.safe_load((REPO_ROOT / "job.yaml").read_text())
    canary_job = yaml.safe_load((REPO_ROOT / "job.canary.yaml").read_text())

    assert "paho-mqtt==2.1.0" in requirements
    assert "pika==1.4.4" in requirements
    assert "pywaggle==0.56.3" in requirements
    assert "pywagglemsg==0.4.0" in requirements
    assert "chirpstack-api==4.19.0" in requirements
    assert 'ENTRYPOINT ["python3", "-m", "app.main"]' in dockerfile
    assert "__pycache__/" in dockerignore
    assert manifest["name"] == "ihv-cenic-chirpstack-devices"
    assert manifest["version"] == "0.2.1"
    assert manifest["source"]["architectures"] == ["linux/amd64", "linux/arm64"]
    assert job["nodes"] == {"H02A": True}
    plugin = job["plugins"][0]
    assert plugin["name"] == "ihv-cenic-chirpstack-devices"
    assert "ihv-cenic-chirpstack-devices:0.2.0" in plugin["pluginSpec"]["image"]
    assert "192.168.1.200" in plugin["pluginSpec"]["args"]
    assert "ihv-sage-h02a" in plugin["pluginSpec"]["args"]
    canary_args = canary_job["plugins"][0]["pluginSpec"]["args"]
    assert (
        "ihv-cenic-chirpstack-devices:0.2.0" in canary_job["plugins"][0]["pluginSpec"]["image"]
    )
    assert canary_job["nodes"] == {"H02A": True}
    assert "ihv-sage-h02a-canary" in canary_args
    assert "--dry-run" in canary_args
    assert "--dry-run" not in plugin["pluginSpec"]["args"]


def test_ecr_description_matches_readme_and_assets_are_present() -> None:
    assert (REPO_ROOT / "ecr-meta/ecr-science-description.md").read_bytes() == (
        REPO_ROOT / "README.md"
    ).read_bytes()
    assert (REPO_ROOT / "ecr-meta/ecr-icon.jpg").is_file()
    assert (REPO_ROOT / "ecr-meta/ecr-science-image.jpg").is_file()
    with Image.open(REPO_ROOT / "ecr-meta/ecr-icon.jpg") as icon:
        assert icon.format == "JPEG"
        assert icon.mode == "RGB"
        assert icon.size == (512, 512)
    with Image.open(REPO_ROOT / "ecr-meta/ecr-science-image.jpg") as science_image:
        assert science_image.format == "JPEG"
        assert science_image.mode == "RGB"
        assert science_image.size == (1920, 1080)
