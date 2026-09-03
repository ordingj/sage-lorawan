# Sage LoRaWAN Forwarder for IHV-CENIC

> **Status:** version `0.1.1` is built and public in the Sage Edge Code Repository (ECR).
> Canary job `5781` passed and was suspended; production job `5782` is active on H02A.
> Version `0.2.0` adds physical-measurement unit metadata and the external-ChirpStack Tracker
> mode described below; it is prepared for owner review and has not been published or deployed.

ECR image: `registry.sagecontinuum.org/ordingj/ihv-cenic-chirpstack-devices:0.1.1`.

This Sage edge app subscribes node H02A to the existing IHV-CENIC ChirpStack MQTT
application-uplink topic. Its default mode republishes every decoded scalar through PyWaggle;
its optional Tracker mode registers the same live devices in Sage's LoRaWAN inventory. Neither
mode changes device codecs, ChirpStack integrations, or the existing ThingsBoard, InfluxDB, and
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
- A read-only canary through H02A received a live MQTT uplink and resolved its device and profile
  through the configured ChirpStack v4 gRPC endpoint at `137.164.38.253:8080` using the existing
  API key; no activation or key API was called.
- A complete authenticated inventory read on 2026-09-01 found 27 configured and enabled
  IHV-CENIC devices across the tenant's applications. Tracker uses this same inventory sweep at
  startup so dashboard registration does not wait for each device's next uplink.
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

Known physical measurements also carry the plural `meta.units` field consumed by the Sage
portal. The forwarder currently assigns:

| Measurement family                                      | `meta.units` |
| ------------------------------------------------------- | ------------ |
| Battery level / `batv`                                  | `%` / `V`    |
| CO2 / relative humidity / temperature                   | `ppm` / `%RH` / `°C` |
| EM500-CO2 barometric pressure / EM500-PP pipe pressure  | `hPa` / `kPa` |
| Soil conductivity / temperature / water content         | `µS/cm` / `°C` / `%` |
| Apogee UV-A irradiance                                  | `W/m²`       |

SenseCAP S2103 indexed measurement values receive `°C`, `%RH`, or `ppm` by their sibling
measurement ID. The same unit policy covers numbered soil probes and Milesight historical
records. Unknown fields, identity values, status flags, counters, and raw payload text remain
unitless rather than receiving an inferred label.

Malformed JSON, missing identity/timestamp/object fields, non-finite values, unsupported value
types, and normalized-name collisions are rejected as permanent payload errors. They are logged
and acknowledged so one poison message cannot block the persistent session.

## LoRaWAN device inventory (version 0.2.0 Tracker mode)

Tracker mode connects directly to the existing IHV-CENIC MQTT broker and ChirpStack v4 gRPC
API on the Mac Studio. At startup it enumerates every enabled device in the configured tenant;
each subsequent live application uplink refreshes that device. For each reconciliation it:

1. reads the device and device-profile inventory with its configured ChirpStack API key;
2. creates or updates the matching Sage sensor-hardware and LoRaWAN-device records; and
3. creates or updates the H02A LoRaWAN connection using the source uplink timestamp.

The registration is intentionally inventory-only. It does not call ChirpStack's activation or
device-key APIs and does not send root keys, session keys, or device addresses to Sage. The
IHV-CENIC ChirpStack instance remains the sole owner of device configuration and sessions. The
Tracker also does not install a second network server or change packet forwarding; a future
standalone Sage ChirpStack can receive the same gateway packets independently.

Sage's portal presents these registrations under **LoRaWAN Devices**, separately from the
node's conventional **Sensors** list. H02A therefore remains at six conventional sensors while
gaining one LoRaWAN-device entry per active IHV-CENIC device.

The same distinction appears in **Latest Records**: the **Sensor** column reads the optional
`meta.sensor` field used by conventional sensor plugins, while **LoRa Device Name** reads
`meta.deviceName`. The official Sage LoRaWAN Listener does not set `meta.sensor`, and neither
does this forwarder. A blank Sensor cell beside a populated LoRa Device Name is therefore the
expected LoRaWAN representation; Tracker adds node inventory and does not rewrite measurement
metadata or historical records.

The Tracker uses a second persistent QoS-1 MQTT client ID,
`ihv-sage-h02a-tracker`. It completes the full startup inventory before subscribing, then
acknowledges each live uplink only after ChirpStack lookup and Sage registration both succeed. A
temporary API failure leaves the delivery unacknowledged and exits the process so Kubernetes can
restart it without losing the inventory event.

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

Both job templates remain pinned to deployed version `0.1.1`. The new unit metadata will not
appear in live H02A records until version `0.2.0` passes review, is published, and the production
forwarder is deliberately rolled to that image.

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

## Review and deploy Tracker mode

[`deploy/tracker-deployment.yaml`](https://gitlab.nrp-nautilus.io/ihv-cenic1/sage-lorawan/-/blob/main/deploy/tracker-deployment.yaml)
is a direct H02A Kubernetes deployment because Tracker is a node inventory service, not a
scheduled science job. It uses the current `wes-identity` ConfigMap for `WAGGLE_NODE_VSN`, runs
as the image's unprivileged user on the core node, and mounts both credentials read-only. It
does not mount or rewrite the generated WES node-manifest ConfigMap; Sage Auth remains the
registry source of truth and WES will incorporate that inventory when it next generates the
node manifest.

Do not apply the deployment until version `0.2.0` has been reviewed and published. Tracker needs
two credentials, of which the ChirpStack credential is now ready:

- `ihv-cenic-chirpstack-api`, key `api-key`: the dedicated
  `ihv-cenic-sage-h02a-tracker` ChirpStack v4 API key. It is non-admin, read-only, scoped only to
  the IHV-CENIC tenant, installed on H02A, and recorded in this repository's ignored mode-`0600`
  `.env` for operator recovery. The existing development key was not copied to H02A.
- `django-token`, key `token`: H02A's Sage node-auth token. The token itself is required, while
  `django-token` is only the conventional Kubernetes Secret name used by the official Tracker
  deployment and this manifest.

The node-auth requirement is not interchangeable with a normal Sage user token. Sage Auth's
LoRaWAN-device endpoint uses `NodeAuthMixin`, and its LoRaWAN-connection endpoint uses the
node-owned variant; the official Tracker consequently sends `Authorization: node_auth <token>`.
H02A currently has no node-auth Secret, and the signed-in `ordingj` account cannot administer
node tokens. A Sage administrator must therefore generate or provide H02A's token. Keep both
credential values out of Git, shell arguments, and command history.

After review, publication, and token delivery, deploy and verify from the authorized H02A SSH
path:

```bash
ssh waggle-dev-node-H02A 'sudo kubectl apply -f -' < deploy/tracker-deployment.yaml
ssh waggle-dev-node-H02A \
  'sudo kubectl rollout status deployment/ihv-cenic-chirpstack-tracker --timeout=180s'
ssh waggle-dev-node-H02A \
  'sudo kubectl logs deployment/ihv-cenic-chirpstack-tracker --tail=100'
```

Completion requires the H02A **LoRaWAN Devices** count and EUIs to match a fresh ChirpStack
enabled-device inventory (27 at the 2026-09-01 review snapshot), current `last_seen_at` values, a
healthy Tracker deployment with zero restarts, and the unchanged production forwarding job
`5782` continuing to publish measurements.

## References

- [IHV-CENIC project overview](https://gitlab.nrp-nautilus.io/ihv-cenic1/ihv/-/blob/main/README.md)
- [IHV-CENIC ChirpStack architecture and Sage H02A deployment plan](https://gitlab.nrp-nautilus.io/ihv-cenic1/ihv/-/blob/main/CHIRPSTACK.md#sage-h02a-forwarder-prepared)
- [IHV-CENIC Sage forwarder design and validation notes](https://gitlab.nrp-nautilus.io/ihv-cenic1/ihv/-/blob/main/sage/ihv_chirpstack_forwarder/README.md)
- [Sage LoRaWAN reference](https://sagecontinuum.org/docs/reference-guides/lorawan)
- [Sage ChirpStack Tracker source](https://github.com/waggle-sensor/wes-chirpstack-tracker)
- [Sage external-ChirpStack deployment reference](https://github.com/waggle-sensor/waggle-edge-stack/tree/main/kubernetes/wes-chirpstack-external)
- [Sage edge app publishing guide](https://sagecontinuum.org/docs/tutorials/edge-apps/publishing-to-ecr)
- [Sage edge app testing guide](https://sagecontinuum.org/docs/tutorials/edge-apps/testing-an-edge-app)
