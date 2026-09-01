# Changelog

## Unreleased

### Added

- Standalone `ihv-cenic-chirpstack-devices` Sage edge app for forwarding decoded IHV-CENIC
  ChirpStack MQTT uplinks.
- Persistent QoS-1 delivery, source timestamp and device metadata preservation, and dry-run mode.
- Separate H02A canary/production job templates, ECR review metadata, focused tests, GitLab CI,
  and local container checks.
- Public `ordingj/sage-lorawan` GitHub source mirror for the ECR publishing workflow.

### Changed

- Standardized human-facing project references on `IHV-CENIC` and linked the standalone README
  to the related IHV-CENIC project, ChirpStack, and Sage-forwarder documentation.

### Fixed

- Serialize every ChirpStack metadata value as text before publication, matching PyWaggle's
  required string-to-string metadata contract. The test publisher now enforces that boundary.

### Deployment

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
