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

### Deployment

- Owner approval for ECR publication was granted on 2026-09-01. ECR version `0.1.0` was built
  for AMD64 and ARM64 under `ordingj` and made public.
- H02A dry-run job `5779` subscribed to the IHV-CENIC MQTT broker, decoded live SDI-12 and soil
  sensor uplinks without publication errors, and was removed after verification. Production is
  not yet scheduled.
