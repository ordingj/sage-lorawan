# Changelog

## Unreleased

### Added

- Standalone `ihv-cenic-chirpstack-devices` Sage edge app for forwarding decoded IHV
  ChirpStack MQTT uplinks.
- Persistent QoS-1 delivery, source timestamp and device metadata preservation, and dry-run mode.
- Separate H02A canary/production job templates, ECR review metadata, focused tests, GitLab CI,
  and local container checks.

### Deployment

- No ECR app was registered, built, made public, or scheduled. Those actions require explicit
  owner review and approval.
