# Changelog

## Unreleased

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

- Serialize every ChirpStack metadata value as text before publication, matching PyWaggle's
  required string-to-string metadata contract. The test publisher now enforces that boundary.

### Deployment

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
