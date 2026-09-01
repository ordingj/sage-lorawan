# Changelog

## Unreleased

### Added

- Standalone `ihv-cenic-chirpstack-devices` Sage edge app for forwarding decoded IHV-CENIC
  ChirpStack MQTT uplinks.
- Persistent QoS-1 delivery, source timestamp and device metadata preservation, and dry-run mode.
- Separate H02A canary/production job templates, ECR review metadata, focused tests, GitLab CI,
  and local container checks.
- Public `ordingj/sage-lorawan` GitHub source mirror for the ECR publishing workflow.
- Prepared version `0.2.0` with an inventory-only Tracker mode for the external IHV-CENIC
  ChirpStack v4 API and MQTT broker.
- Reconcile the complete enabled-device tenant inventory at Tracker startup, then refresh each
  device from its subsequent live MQTT uplinks.
- Added an H02A-scoped Kubernetes Tracker deployment that mounts the ChirpStack API key and Sage
  node-auth token from separate read-only secrets.

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

- Version `0.2.0` is prepared for owner review and has not been published or deployed. H02A can
  reach the external MQTT and ChirpStack API endpoints, but the node does not yet contain Sage's
  required `django-token`; the signed-in `ordingj` account cannot administer node tokens.
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
- Production job `5782` is running version `0.1.1` on H02A. Its logs show successful QoS-1
  publication, the initial Data API query returned 394 records from 23 LoRa devices with source
  identity metadata, and the H02A Latest Records page displays current device measurements.
