# Sage LoRaWAN Forwarder for IHV

> **Status:** review candidate only. This app has not been registered with, built by, or made
> public in the Sage Edge Code Repository (ECR), and it has not been scheduled on H02A.

Planned ECR app name: `ihv-cenic-chirpstack-devices`.

This Sage edge app subscribes node H02A to the existing IHV ChirpStack MQTT
application-uplink topic and republishes every decoded scalar through PyWaggle. It does not
change device codecs, ChirpStack integrations, or the existing ThingsBoard, InfluxDB, and
PostgreSQL delivery paths.

The stock Sage `lorawan-listener` is not a safe drop-in for this fleet. It expects decoded
payloads shaped as `object.measurements[]`; IHV's established codecs emit canonical named
fields directly under `object`. Adding a second representation to every live codec would also
flow into the existing sinks. This forwarder instead flattens the established object only at
the Sage boundary.

## Scientific purpose

IHV's vineyard LoRaWAN network observes environmental and equipment conditions through
distributed low-power sensors. Publishing those decoded observations through the Sage node
makes them available with node, plugin, device, radio, and acquisition-time provenance for
edge-to-cloud analysis. The adapter preserves the sensor's original ChirpStack timestamp and
identity rather than assigning forwarding time, which supports comparison with the existing
IHV data paths and avoids silently changing the scientific record.

## Verified topology

Read-only checks from H02A on 2026-09-01 established:

- H02A is `sgt-thor-1423325056867-H02A` (`linux/arm64`) and reaches the IHV Mac Studio at
  `192.168.1.200` through its site LAN.
- DNS on H02A resolves `ihv-mac-studio.localdomain` to that address, ICMP succeeds, and TCP
  port `1883` accepts connections.
- A bounded MQTT subscription received a current
  `application/<application-id>/device/<dev-eui>/event/up` envelope with the original
  nanosecond timestamp, device name, frame counter, and canonical decoded object.
- The Sage portal and Data API report current H02A system data, but the job inventory contained
  no existing H02A edge job at the time of inspection.

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
deduplication ID, frame counter, FPort, data rate, and the best receiver RSSI/SNR. Device
variables and raw payload bytes are never published.

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
and executes its `--help` smoke test. It does not contact the IHV MQTT broker, Sage ECR, or H02A.

For a no-publication MQTT canary, run the reviewed image on an authorized Sage development path
with `--dry-run` and a separate client ID such as `ihv-sage-h02a-canary`. Do not run or install
packages directly on the node host.

## Review, publish, and schedule

The canonical development repository is
[`ihv-cenic1/sage-lorawan`](https://gitlab.nrp-nautilus.io/ihv-cenic1/sage-lorawan).
Sage's current ECR instructions require a public GitHub repository URL when creating an app.
Before registration, either confirm that ECR now accepts this GitLab URL or create a reviewed
public GitHub mirror and update `homepage` in `sage.yaml` to that exact source URL.

`job.canary.yaml` is the bounded dry-run template; `job.yaml` is the production template.
After explicit owner approval:

1. Register and build version `0.1.0` in ECR. ECR versions cannot be reused.
2. Confirm the ECR owner/name and update the image in `job.yaml` if it differs.
3. Make the app public only when it is ready to schedule.
4. Run a bounded canary with `--dry-run --mqtt-client-id ihv-sage-h02a-canary`.
5. Suspend the canary before starting the production job with `ihv-sage-h02a`; only one running
   subscriber may use a given client ID.

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

- [Sage LoRaWAN reference](https://sagecontinuum.org/docs/reference-guides/lorawan)
- [Sage edge app publishing guide](https://sagecontinuum.org/docs/tutorials/edge-apps/publishing-to-ecr)
- [Sage edge app testing guide](https://sagecontinuum.org/docs/tutorials/edge-apps/testing-an-edge-app)
