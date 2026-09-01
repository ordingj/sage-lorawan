"""Translate canonical ChirpStack MQTT uplinks into Sage measurements."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import math
import re
from typing import Any


_RFC3339_NS_PATTERN = re.compile(
    r"^(?P<prefix>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})"
    r"(?:\.(?P<fraction>\d{1,9}))?(?P<zone>Z|[+-]\d{2}:\d{2})$"
)
_MEASUREMENT_NAME_PATTERN = re.compile(r"[^a-z0-9_]")
_DEVICE_INFO_FIELDS = (
    "tenantId",
    "tenantName",
    "applicationId",
    "applicationName",
    "deviceProfileId",
    "deviceProfileName",
    "deviceName",
    "devEui",
)
_UPLINK_METADATA_FIELDS = (
    "deduplicationId",
    "devAddr",
    "adr",
    "dr",
    "fCnt",
    "fPort",
    "confirmed",
)


class PayloadError(ValueError):
    """Report a permanent malformed or unsupported ChirpStack uplink."""


@dataclass(frozen=True)
class SageMeasurement:
    """One decoded Sage measurement with source time and LoRa identity."""

    name: str
    value: bool | int | float | str
    timestamp_ns: int
    metadata: Mapping[str, bool | int | float | str]


def measurements_from_payload(payload: bytes | str) -> tuple[SageMeasurement, ...]:
    """Return all scalar decoded fields from one ChirpStack MQTT envelope."""

    try:
        decoded_payload = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as error:
        raise PayloadError("ChirpStack uplink must be a UTF-8 JSON object") from error
    if not isinstance(decoded_payload, Mapping):
        raise PayloadError("ChirpStack uplink must be a JSON object")

    timestamp = decoded_payload.get("time")
    if not isinstance(timestamp, str):
        raise PayloadError("ChirpStack uplink time must be RFC 3339 text")
    timestamp_ns = _parse_rfc3339_ns(timestamp)

    device_info = decoded_payload.get("deviceInfo")
    if not isinstance(device_info, Mapping):
        raise PayloadError("ChirpStack uplink deviceInfo must be an object")
    for field in ("deviceName", "devEui"):
        if not isinstance(device_info.get(field), str) or not device_info[field].strip():
            raise PayloadError(f"ChirpStack uplink deviceInfo.{field} must be text")

    decoded = decoded_payload.get("object")
    if not isinstance(decoded, Mapping):
        raise PayloadError("ChirpStack uplink object must be a decoded JSON object")
    metadata = _measurement_metadata(decoded_payload, device_info)

    records: list[SageMeasurement] = []
    names: set[str] = set()
    for source_name, value in _flatten_scalars("", decoded):
        name = normalize_measurement_name(source_name)
        if name in names:
            raise PayloadError(f"decoded fields collide after Sage normalization: {name}")
        names.add(name)
        records.append(SageMeasurement(name, value, timestamp_ns, metadata))
    if not records:
        raise PayloadError("ChirpStack uplink object contains no scalar measurements")
    return tuple(records)


def normalize_measurement_name(value: str) -> str:
    """Apply the same lowercase Sage naming contract as LoRaWAN Listener."""

    normalized = _MEASUREMENT_NAME_PATTERN.sub("_", value.lower())
    if not normalized or not any(character.isalnum() for character in normalized):
        raise PayloadError(f"decoded field has no usable Sage name: {value!r}")
    return normalized


def _parse_rfc3339_ns(value: str) -> int:
    match = _RFC3339_NS_PATTERN.fullmatch(value)
    if match is None:
        raise PayloadError(f"invalid RFC 3339 timestamp: {value!r}")
    fraction = (match.group("fraction") or "").ljust(9, "0")
    zone = match.group("zone")
    zone_text = "+00:00" if zone == "Z" else zone
    try:
        parsed = datetime.fromisoformat(f"{match.group('prefix')}.{fraction[:6]}{zone_text}")
        utc = parsed.astimezone(timezone.utc)
        return int(utc.timestamp()) * 1_000_000_000 + int(fraction)
    except (OverflowError, ValueError) as error:
        raise PayloadError(f"invalid RFC 3339 timestamp: {value!r}") from error


def _measurement_metadata(
    payload: Mapping[str, Any],
    device_info: Mapping[str, Any],
) -> dict[str, bool | int | float | str]:
    metadata: dict[str, bool | int | float | str] = {"lns": "ihv_chirpstack"}
    for field in _DEVICE_INFO_FIELDS:
        value = device_info.get(field)
        if value is not None:
            metadata[field] = _metadata_scalar(value, f"deviceInfo.{field}")
    metadata["devEui"] = str(metadata["devEui"]).lower()
    for field in _UPLINK_METADATA_FIELDS:
        value = payload.get(field)
        if value is not None:
            metadata[field] = _metadata_scalar(value, field)

    tags = device_info.get("tags")
    if tags is not None and not isinstance(tags, Mapping):
        raise PayloadError("ChirpStack uplink deviceInfo.tags must be an object")
    for key, value in (tags or {}).items():
        if not isinstance(key, str):
            raise PayloadError("ChirpStack tag names must be text")
        metadata_key = f"{normalize_measurement_name(key)}_tag"
        if metadata_key in metadata:
            raise PayloadError(f"ChirpStack tag metadata collides at {metadata_key}")
        metadata[metadata_key] = _metadata_scalar(value, f"deviceInfo.tags.{key}")

    best_rssi = _best_receiver_value(payload.get("rxInfo"), "rssi")
    best_snr = _best_receiver_value(payload.get("rxInfo"), "snr")
    if best_rssi is not None:
        metadata["rssi"] = best_rssi
    if best_snr is not None:
        metadata["snr"] = best_snr
    return metadata


def _flatten_scalars(
    prefix: str,
    value: object,
) -> Iterable[tuple[str, bool | int | float | str]]:
    if value is None:
        return
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise PayloadError("decoded object keys must be text")
            nested_prefix = f"{prefix}_{key}" if prefix else key
            yield from _flatten_scalars(nested_prefix, nested)
        return
    if isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray):
        for index, nested in enumerate(value):
            nested_prefix = f"{prefix}_{index}" if prefix else str(index)
            yield from _flatten_scalars(nested_prefix, nested)
        return
    if isinstance(value, bool | str):
        yield prefix, value
        return
    if isinstance(value, int):
        yield prefix, value
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise PayloadError(f"decoded field {prefix} must be finite")
        yield prefix, value
        return
    raise PayloadError(f"decoded field {prefix} has unsupported type {type(value).__name__}")


def _metadata_scalar(value: object, field: str) -> bool | int | float | str:
    if isinstance(value, bool | int | str):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    raise PayloadError(f"ChirpStack metadata {field} must be a finite scalar")


def _best_receiver_value(value: object, key: str) -> int | float | None:
    if value is None:
        return None
    if not isinstance(value, Sequence) or isinstance(value, str | bytes | bytearray):
        raise PayloadError("ChirpStack uplink rxInfo must be a list")
    candidates: list[int | float] = []
    for receiver in value:
        if not isinstance(receiver, Mapping):
            raise PayloadError("ChirpStack uplink rxInfo entries must be objects")
        candidate = receiver.get(key)
        if candidate is None:
            continue
        if isinstance(candidate, bool) or not isinstance(candidate, int | float):
            raise PayloadError(f"ChirpStack rxInfo.{key} must be numeric")
        if isinstance(candidate, float) and not math.isfinite(candidate):
            raise PayloadError(f"ChirpStack rxInfo.{key} must be finite")
        candidates.append(candidate)
    return max(candidates, default=None)


__all__ = [
    "PayloadError",
    "SageMeasurement",
    "measurements_from_payload",
    "normalize_measurement_name",
]
