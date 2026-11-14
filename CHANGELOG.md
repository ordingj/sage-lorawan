# Changelog

## 2026-11-14

- Record the safe historical backfill stop after 101,686 verified records. A bounded
  64-record resumption also reaches the unchanged memory guard. All 431,205 originals remain
  archived, with 8,955 tail records outside completed receipts. Both helpers are removed.
  The primary loader remains healthy with an empty queue and zero OOM events. Keep native
  memory qualification required before more replay. Public Sage CSV normalization does not
  explain the standalone-carriage-return case, so central verification remains required.

## 2026-11-13

- Record patched H02A local loader activation. One consumer has prefetch 250, and the
  waiting queue clears without warnings, errors or restarts. All 431,205 captured messages
  have a verified durable archive. Independent source checks verify all 142 fresh local
  observations, and the configured rule query works. Historical backfill continues with
  unchanged retention and strict capacity stops. Keep its completion and helper cleanup
  required. Classify seven cloud-returned text values that omit source carriage returns,
  while the local database preserves the originals exactly. The central stage remains unknown.

- Roll out Tracker `0.2.7` after a native H02A canary. Both startups reconcile all 27 devices.
  The canary records 14 live updates across ten devices in 171 seconds. Production records
  45 live updates across 21 devices at the final check. Both have zero warnings, errors or
  restarts. Three inventory audits preserve all 27 connection IDs and hardware links, with no
  extra registrations. Keep credentials, settings and the stable MQTT session. Remove both
  owned helpers. The forwarder stays unchanged, and 86 fresh cloud records pass the destination
  check. All 40 tests, lint, native image build and CLI checks pass. Update only the Tracker
  image and its manifest assertion. Retain the immutable `0.2.5` manifest for rollback.

- Activate `0.2.7` as H02A job `5871` after the user accepts the clean 3,019-second canary
  despite its one-event coverage. Preserve the original failed two-event result. Suspend job
  `5792`, verify native goal withdrawal and old-writer absence, then start the exact published
  image. Fresh readback verifies 112 records from 12 events across nine devices, with identity,
  units and sentinel controls. Keep Tracker on `0.2.5`, preserve the stable MQTT session and
  retain the suspended old job and immutable spec for rollback. Local loader recovery remains open.

- Publish `0.2.7` through Jenkins build `10` from reviewed source `ecbb0d2`. Hosted pipeline
  `92826` passes. Both platform images pass CLI and unsupported-port checks, with all six
  application source hashes matching. The manifest-list digest is
  `sha256:cd955af23fb6cc0f414341387a40e4f73be152e23fae153ba96e78823ea0ef25`.
  Keep both earlier published artifacts unchanged. Production and Tracker remain on `0.2.5`
  pending a passing live canary and verified cutover.

- Prepare candidate `0.2.7`. Apply the existing unsupported SDI-12 port filter before
  empty-object validation. Exact replay identifies both rejected events as deliberately empty
  FPort 6 objects. Both now return no measurements. Nearby FPort 2 outputs retain exact hashes.
  Keep supported-port and unrelated empty objects invalid. A filtered delivery is acknowledged
  without publishing. Preserve codecs, raw archives, source timestamps and all canary gates.
  All 40 tests, lint, native image build and CLI smoke checks pass. Keep production and
  Tracker on `0.2.5` pending publication and live qualification.

## 0.2.6 - 2026-11-12

- Publish reviewed source `df193ac745d0b079fa3efcb55b1dc1acc6f36af3` through Jenkins build 9.
  The AMD64/ARM64 manifest-list digest is
  `sha256:5b6844902e7d5c552e6b07d8cee2e39a1a4f36eb4da79b88eb2bdb7172fa4a42`.
- Qualify Python 3.14.7, both published CLI paths and exact application source hashes.
  Hosted pipeline 92751 and all 36 tests pass. ARM64 runs natively. AMD64 uses local emulation.
- Preserve the accepted 0.2.5 image. Keep production activation gated on a new live canary.
  No workload activation occurs in this publication.

## Unreleased

### Python runtime qualification

- Prepare candidate version 0.2.6 and its canary template. Keep the production job and Tracker
  templates on accepted version 0.2.5 until the new canary passes.

- Run GitLab CI with the same pinned Python 3.14.7 Alpine image as the application build.
  Keep the validation commands and warning policy unchanged.

- Use the digest-pinned IHV Python 3.14.7 Alpine base for the next build. Set the local
  development target to Python 3.14 and keep the existing dependency pins.
- Close HTTP error response bodies after missing records, terminal errors and retry attempts.
  Keep the existing authentication, retry limits, request methods and status handling.
- Align the README with the retained 0.2.5 rollout record. Keep the next image unpublished
  until the release checks pass. A new canary must pass before production activation.

### Added

- Standalone `ihv-cenic-chirpstack-devices` Sage edge app for forwarding decoded IHV-CENIC
  ChirpStack MQTT uplinks.
- Persistent QoS-1 delivery, source timestamp and device metadata preservation, and dry-run mode.
- Separate H02A canary/production job templates, ECR review metadata, focused tests, GitLab CI,
  and local container checks.
- Public `ordingj/sage-lorawan` GitHub source mirror for the ECR publishing workflow.
- Version `0.2.0` includes an optional inventory-only Tracker mode for the external IHV-CENIC
  ChirpStack v4 API and MQTT broker.
- Reconcile the complete enabled-device tenant inventory at Tracker startup, then refresh each
  device from its subsequent live MQTT uplinks.
- Added an H02A-scoped Kubernetes Tracker deployment that mounts the ChirpStack API key and Sage
  node-auth token from separate read-only secrets.
- Plural `meta.units` metadata for known physical measurements, including device-specific
  pressure units, numbered soil probes, SenseCAP measurement IDs, and historical Milesight
  values; unknown and operational fields remain unitless.
- Canonical `device_label`, `block`, `slope`, `latitude`, and `longitude` metadata for the 26
  mapped IHV-CENIC telemetry devices, joined by DevEUI from the field-device map snapshot.

### Changed

- Standardized human-facing project references on `IHV-CENIC` and linked the standalone README
  to the related IHV-CENIC project, ChirpStack, and Sage-forwarder documentation.
- Documented Sage LoRaWAN devices as a distinct portal inventory from conventional node sensors,
  and retained Sage Auth as the inventory source of truth instead of rewriting WES ConfigMaps.
- Documented the expected Latest Records split: `meta.sensor` populates conventional Sensor,
  while LoRaWAN records use `meta.deviceName` in the separate LoRa Device Name column.

### Fixed

- Version `0.2.5` retries transient DNS, rate-limit, and Sage server failures with bounded
  exponential backoff. The safeguard was added after the first H02A Tracker deployment exposed
  intermittent external DNS resolution and entered a restart loop during startup reconciliation.
  The H02A deployment also uses explicit public resolvers after a 30-lookup node probe completed
  without a failure through that isolated path.
- Version `0.2.4` applies the full documented sensor-sentinel policy before Sage publication:
  unsupported SDI-12 ports and `BatV == 7.2`, disconnected Dragino soil probes, TEROS-22 error
  codes, and Milesight EM500 CO2 and pressure sentinels no longer become physical measurements.
  Availability measurements preserve the device state where applicable.
- Tracker now rounds ChirpStack's binary-float battery percentage to Sage Auth's two-decimal
  contract and normalizes spaces in device names. Live preflight reconciled all 27 enabled
  tenant devices after an unrounded value reproduced the API's five-total-digit rejection.
- Version `0.2.3` suppresses the Dragino SE01-LS/SE0X-LS `temp_ds18b20 == 327.6`
  disconnected-probe sentinel and publishes the unitless boolean
  `external_temperature_sensor_available` measurement instead. Valid external-probe
  temperatures remain available in `°C` and carry a matching `true` availability record.
- Serialize every ChirpStack metadata value as text before publication, matching PyWaggle's
  required string-to-string metadata contract. The test publisher now enforces that boundary.

### Deployment

- Version `0.2.5` was built by Jenkins build `8` from commit `78f7ab1` for AMD64 and ARM64.
  Its manifest-list digest is
  `sha256:587d318403966ad82010378fbda6cae81c37094982a37e0bd2e51c0d05c6f498`.
- H02A canary job `5791` ran for 10 minutes 50 seconds with 53 decoded uplinks, zero invalid
  sentinel measurements, runtime failures, or restarts before suspension. Its lingering pod and
  orphaned removed-canary pod `5785` were deleted from the node.
- Production job `5789` was suspended and replaced by job `5792` on `0.2.5`. The initial Data
  API proof returned 110 records from 17 uplinks across 13 devices with complete identity
  metadata, four false availability records, and zero filtered sentinel records.
- Tracker's accepted `0.2.5` pod used the published digest, reconciled and live-refreshed all 27
  enabled devices with zero restarts, and produced an exact 27-connection Sage inventory with no
  missing/extra DevEUIs, stale timestamps, or sensitive inventory fields.
- Version `0.2.4` was built by Jenkins build `7` for AMD64 and ARM64 at manifest-list digest
  `sha256:0eb4de931a874155cfa81badb1575c289a96deb9118235499278c7043ee776a9`.
  Its Tracker reconciled all 27 enabled devices once but was not accepted for ongoing deployment
  after intermittent H02A DNS failures caused repeated restarts.
- Version `0.2.3` was built by Jenkins build `6` from commit `84f9a8b` for AMD64 and ARM64.
  Its manifest-list digest is
  `sha256:340cace84379d3f19c3ec875e1fc5051cdddbc7d1b9b1ff5d1237e479a198c01`.
- H02A canary job `5788` ran uninterrupted for about 11 minutes and was suspended. Previous
  production job `5787` was suspended, and production job `5789` is running version `0.2.3`.
- Initial production proof returned 112 records across 12 devices, including four false
  `external_temperature_sensor_available` records and no `temp_ds18b20 == 327.6` records. The
  required device identity metadata remained complete.
- Catalog version `0.2.2` was built by Jenkins build `5` from commit `bdcf79a` and replaces the
  deployment-oriented Science Overview with concise user documentation focused on the app's
  scientific purpose, published measurements and metadata, and how to view those fields in the
  Sage Query Browser. The catalog description is now kept separate from the operator README so
  rollout history cannot leak into the user-facing page. Its AMD64/ARM64 manifest-list digest is
  unchanged from `0.2.0`: `sha256:9d8c240737143e4e504d7912b226cdadaea138ffe0a6ef4cb64a033b7c8b1dee`.
- Catalog version `0.2.1` was built from commit
  `2e2bdfe368b3e7a1dcc3a32a3c0fa8a181540935` and republishes the completed rollout Science
  Overview without changing application source, dependencies, the Dockerfile, deployment
  manifests, or production job `5787`. Jenkins build `4` produced the same multi-architecture
  digest as deployed version `0.2.0`.
- Version `0.2.0` was built and published from commit
  `60938a1efafc17143b5a3557e849906fca00215a` for AMD64 and ARM64. Its manifest-list digest is
  `sha256:9d8c240737143e4e504d7912b226cdadaea138ffe0a6ef4cb64a033b7c8b1dee`.
- H02A canary job `5786` completed the bounded rollout window and was suspended. Its final pod
  ran 9 minutes 29 seconds without a restart after accidental duplicate canary `5785` was
  detected and suspended.
- Production job `5782` was healthy on `0.1.1` immediately before cutover and was suspended.
  Production job `5787` is the sole active forwarder on `0.2.0`.
- Initial post-cutover proof returned 37 fresh Data API records across three devices. Live soil,
  atmospheric, and battery observations carried expected units, and the Query Browser exposed
  mapped device label, block, slope, latitude, and longitude metadata.
- Tracker was deliberately left undeployed because it is not required for measurement
  forwarding. H02A still lacks Sage's required `django-token`; the signed-in `ordingj` account
  cannot administer node tokens.
- Created the non-admin, read-only `ihv-cenic-sage-h02a-tracker` API key scoped to the IHV-CENIC
  ChirpStack tenant, verified its inventory access, installed it as H02A Secret
  `ihv-cenic-chirpstack-api`, and retained it only in the ignored mode-`0600` project `.env`.
- Confirmed that the Sage node-auth token is required by the LoRaWAN device and connection write
  endpoints; `django-token` is the deployment's conventional Kubernetes Secret name, not the
  authentication mechanism itself.
- The 2026-09-01 read-only proof resolved one live uplink through both endpoints and found 27
  configured, enabled devices in the complete IHV-CENIC tenant inventory.
- The existing development ChirpStack API key was used only for read-only proof and was not
  copied to H02A; Tracker will use the dedicated tenant-scoped key already installed there.
- Tracker deployment intentionally omits LoRaWAN activation and key synchronization. IHV-CENIC
  ChirpStack remains the sole configuration/session owner while a future Sage network server can
  remain standalone.

- Owner approval for ECR publication was granted on 2026-09-01. ECR version `0.1.0` was built
  for AMD64 and ARM64 under `ordingj` and made public.
- H02A dry-run job `5779` subscribed to the IHV-CENIC MQTT broker, decoded live SDI-12 and soil
  sensor uplinks without publication errors, and was removed after verification.
- Production job `5780` subscribed successfully but exposed the metadata-type mismatch on its
  first uplink and was suspended to stop the restart loop.
- ECR version `0.1.1` was built for AMD64 and ARM64 from reviewed commit `277f3af`. H02A dry-run
  job `5781` decoded live uplinks with zero restarts and was suspended after verification.
- Production job `5782` ran version `0.1.1` on H02A. Its logs showed successful QoS-1
  publication, the initial Data API query returned 394 records from 23 LoRa devices with source
  identity metadata, and the H02A Latest Records page displayed current device measurements.
