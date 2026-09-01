# Sage LoRaWAN Forwarder for IHV-CENIC

> **Status:** version `0.1.1` is built and public in the Sage Edge Code Repository (ECR).
> Canary job `5781` passed and was suspended; production job `5782` is active on H02A.

ECR image: `registry.sagecontinuum.org/ordingj/ihv-cenic-chirpstack-devices:0.1.1`.

This Sage edge app subscribes node H02A to the existing IHV-CENIC ChirpStack MQTT
application-uplink topic and republishes every decoded scalar through PyWaggle. It does not
change device codecs, ChirpStack integrations, or the existing ThingsBoard, InfluxDB, and
PostgreSQL delivery paths.

The stock Sage `lorawan-listener` is not a safe drop-in for this fleet. It expects decoded
payloads shaped as `object.measurements[]`; IHV-CENIC's established codecs emit canonical named
fields directly under `object`. Adding a second representation to every live codec would also
flow into the existing sinks. This forwarder instead flattens the established object only at
the Sage boundary.

## Scientific purpose

IHV-CENIC's vineyard LoRaWAN network observes environmental and equipment conditions through
distributed low-power sensors. Publishing those decoded observations through the Sage node
makes them available with node, plugin, device, radio, and acquisition-time provenance for
edge-to-cloud analysis. The adapter preserves the sensor's original ChirpStack timestamp and
identity rather than assigning forwarding time, which supports comparison with the existing
IHV-CENIC data paths and avoids silently changing the scientific record.

## Verified topology

Read-only checks from H02A on 2026-09-01 established:

- H02A is `sgt-thor-1423325056867-H02A` (`linux/arm64`) and reaches the IHV-CENIC Mac Studio at
  `192.168.1.200` through its site LAN.
- DNS on H02A resolves `ihv-mac-studio.localdomain` to that address, ICMP succeeds, and TCP
  port `1883` accepts connections.
- A bounded MQTT subscription received a current
  `application/<application-id>/device/<dev-eui>/event/up` envelope with the original
  nanosecond timestamp, device name, frame counter, and canonical decoded object.
- The Sage portal and Data API report current H02A system data, but the job inventory contained
  no existing H02A edge job at the time of inspection.

ECR version `0.1.1` was built for both `linux/amd64` and `linux/arm64` from reviewed source
commit `277f3af1039eac9fd271ee844674f165e79f1eb5`. On 2026-09-01, dry-run job `5781` pulled the
ARM64 image on H02A, stayed healthy with zero restarts, and decoded live soil, SDI-12, CO2, and
other IHV-CENIC uplinks. It was suspended after verification. Production job `5782` then
subscribed at QoS 1 and began publishing through the same image without errors.

Recheck the address and port from H02A before deployment; they are observed runtime facts, not
configuration discovery:

```bash
getent ahostsv4 ihv-mac-studio.localdomain
timeout 5 bash -c '</dev/tcp/192.168.1.200/1883'
```

## Data contract and delivery behavior

The app subscribes to `application/+/device/+/event/up` at QoS 1 using the stable persistent
client ID `ihv-sage-h02a`. It manually acknowledges an MQTT delivery only after every decoded
scalar has been accepted by PyWaggle. A transient Sage publication failure therefore leaves the
MQTT delivery unacknowledged and exits the app so the scheduler can restart it. The source
broker's existing persistent storage and QoS-1 queue then provide forward-only restart coverage
after this subscriber has connected for the first time.

Delivery is at least once. If Sage accepts part of an uplink before a later field fails, MQTT
redelivery can repeat those earlier fields. Consumers can identify replays using the measurement
name together with `deduplicationId`, `devEui`, and `fCnt` metadata.

Nested objects and arrays become underscore-separated names. Names are lowercased and
non-alphanumeric characters become underscores, matching Sage's LoRaWAN Listener convention.
For example:

| ChirpStack object path      | Sage measurement           |
| --------------------------- | -------------------------- |
| `BatV`                      | `batv`                     |
| `location.latitude`         | `location_latitude`        |
| `messages[0].measurementId` | `messages_0_measurementid` |

Every record preserves the ChirpStack nanosecond timestamp. Metadata includes `deviceName`,
lowercase `devEui`, tenant/application/profile identity, tags with a `_tag` suffix,
deduplication ID, frame counter, FPort, data rate, and the best receiver RSSI/SNR. Metadata
values are serialized as strings because that is the PyWaggle publication contract; decoded
measurement values retain their bool, number, or string types. Device variables and raw payload
bytes are never published.

Malformed JSON, missing identity/timestamp/object fields, non-finite values, unsupported value
types, and normalized-name collisions are rejected as permanent payload errors. They are logged
and acknowledged so one poison message cannot block the persistent session.

## Validate locally

Python 3.12+, Docker, and `make` are expected:

```bash
uv venv --python 3.12
uv pip install --python .venv/bin/python -r requirements-dev.txt
make all
```

`make all` checks formatting and lint, runs the unit/contract tests, builds the local container,
and executes its `--help` smoke test. It does not contact the IHV-CENIC MQTT broker, Sage ECR,
or H02A.

For a no-publication MQTT canary, run the reviewed image on an authorized Sage development path
with `--dry-run` and a separate client ID such as `ihv-sage-h02a-canary`. Do not run or install
packages directly on the node host.

## Review, publish, and schedule

The canonical development repository is
[`ihv-cenic1/sage-lorawan`](https://gitlab.nrp-nautilus.io/ihv-cenic1/sage-lorawan).
Sage's ECR source is the public
[`ordingj/sage-lorawan`](https://github.com/ordingj/sage-lorawan) mirror, as required by the
current publishing workflow. The `homepage` in `sage.yaml` points to that exact source. Keep
the mirror's `main` branch synchronized with reviewed GitLab commits before every ECR build.

`job.canary.yaml` is the bounded dry-run template; `job.yaml` is the production template.
Publication approval was granted on 2026-09-01. Initial production job `5780` connected to MQTT
but was suspended after PyWaggle rejected numeric and boolean metadata. Version `0.1.1`
serializes every metadata value and adds a regression boundary that rejects the same invalid
shape as PyWaggle. After canary job `5781` passed, production job `5782` was scheduled with the
stable client ID `ihv-sage-h02a`.

Production verification established:

- The H02A pod remained running with zero restarts while its logs reported the QoS-1
  subscription and successful measurement batches without publication errors.
- An initial 10-minute Sage Data API query returned 394 decoded records across 23 LoRa devices.
  A representative record preserved the ChirpStack timestamp and carried `deviceName`,
  lowercase `devEui`, `fCnt`, radio metadata, H02A identity, task name, and the exact `0.1.1`
  plugin image.
- The H02A Latest Records page displayed current `batv`, `data_sum`, `co2`, `humidity`,
  `pressure`, `temperature`, and other values with their LoRa device names.

Verify the production path through both the Sage Data API and the H02A Latest Records page:

```bash
curl -fsS -H 'Content-Type: application/json' \
  https://data.sagecontinuum.org/api/v1/query \
  -d '{"start":"-10m","filter":{"vsn":"H02A","task":"ihv-cenic-chirpstack-devices"}}'
```

The result must contain at least one decoded measurement with the source ChirpStack timestamp
and matching `deviceName`, `devEui`, and `fCnt`. A running job or broker connection alone is not
delivery proof.

## References

- [IHV-CENIC project overview](https://gitlab.nrp-nautilus.io/ihv-cenic1/ihv/-/blob/main/README.md)
- [IHV-CENIC ChirpStack architecture and Sage H02A deployment plan](https://gitlab.nrp-nautilus.io/ihv-cenic1/ihv/-/blob/main/CHIRPSTACK.md#sage-h02a-forwarder-prepared)
- [IHV-CENIC Sage forwarder design and validation notes](https://gitlab.nrp-nautilus.io/ihv-cenic1/ihv/-/blob/main/sage/ihv_chirpstack_forwarder/README.md)
- [Sage LoRaWAN reference](https://sagecontinuum.org/docs/reference-guides/lorawan)
- [Sage edge app publishing guide](https://sagecontinuum.org/docs/tutorials/edge-apps/publishing-to-ecr)
- [Sage edge app testing guide](https://sagecontinuum.org/docs/tutorials/edge-apps/testing-an-edge-app)
