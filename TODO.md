# TODO

## Sage Forwarder Measurement Metadata

- [x] Deploy version `0.2.0` to H02A, verify fresh measurements expose units and canonical
      field metadata.
  - ECR build `0.2.0` used commit `60938a1efafc17143b5a3557e849906fca00215a` and published
    the AMD64/ARM64 manifest list at digest
    `sha256:9d8c240737143e4e504d7912b226cdadaea138ffe0a6ef4cb64a033b7c8b1dee`.
  - H02A canary job `5786` passed and was suspended; accidental duplicate `5785` was also
    suspended. Production job `5782` was suspended and replaced by active `0.2.0` job `5787`.
  - The Data API and Query Browser show live atmospheric, battery, and `temp_soil`,
    `conduct_soil`, and `water_soil` units plus mapped field metadata.
  - Catalog-only version `0.2.1` was built from commit
    `2e2bdfe368b3e7a1dcc3a32a3c0fa8a181540935` with the same multi-architecture digest as
    `0.2.0`; the My App Science Overview now displays the completed rollout status.
  - [x] Refresh and verify the My App Science Overview from the final release description.

- [x] Add Sage unit metadata to known physical sensor measurements.
  - The forwarder now emits plural `meta.units` for known battery, atmospheric, soil, UV-A,
    device-specific pressure, SenseCAP indexed, and Milesight historical measurements while
    leaving unknown and operational fields unitless.
  - Focused payload contracts and the complete pre-rollout `make all` gate passed for version
    `0.2.0`.

- [x] Add canonical field context to Sage measurement metadata.
  - Version `0.2.0` bundles the 26-device IHV-CENIC field-map snapshot and emits available
    `device_label`, `block`, `slope`, `latitude`, and `longitude` values as strings by DevEUI.
  - Missing fields and unmapped devices remain publishable without fabricated metadata.

## Sage Forwarder Rollout Finalization

- [x] Finalize the forwarder-only Sage H02A rollout for IHV-CENIC ChirpStack devices.
  - [x] Re-run `make all`, review the complete version `0.2.0` source and deployment diff, and
        obtain explicit owner approval before any push, ECR publication, or Tracker deployment.
  - [x] Push the approved `main` branch to the canonical `ihv-cenic1/sage-lorawan` GitLab project
        and synchronize the public `ordingj/sage-lorawan` GitHub mirror used by Sage ECR.
  - [x] Publish `ordingj/ihv-cenic-chirpstack-devices:0.2.0` to Sage ECR and verify that its
        immutable image digest supports both `linux/amd64` and `linux/arm64`.
  - [x] Run and suspend bounded H02A canary `5786`; suspend duplicate canary `5785` after its
        shared MQTT client ID was detected.
  - [x] Confirm production forwarder job `5782` remained healthy on version `0.1.1` immediately
        before cutover, then suspend it so only one stable MQTT client remained.
  - [x] Roll production to job `5787` on reviewed version `0.2.0`, then verify representative
        fresh `temp_soil`, atmospheric, soil, and battery records expose expected plural
        `meta.units` values plus mapped `device_label`, `block`, `slope`, `latitude`, and
        `longitude` fields in the Sage Data API and portal; focused contracts cover the less
        frequent UV-A and device-specific pressure families.
  - [x] Record the reviewed commit, ECR digest, job IDs, and forwarder regression evidence in
        `README.md`, `CHANGELOG.md`, and this TODO.

## Optional Tracker Deployment (Deferred)

- [ ] Deploy Tracker only if Sage LoRaWAN inventory is later required; it is not necessary for
      the working measurement-forwarding path.
  - [ ] Ask a Sage administrator to retrieve or rotate H02A's server-side node-auth token, then
        install it as H02A Secret `django-token`, key `token`, without exposing the value in Git,
        shell arguments, logs, or command history.
  - [ ] Apply `deploy/tracker-deployment.yaml` on H02A; verify rollout completion, zero restarts,
        successful startup inventory reconciliation, and continued QoS-1 live refreshes.
  - [ ] Compare H02A **LoRaWAN Devices** against a fresh enabled-device ChirpStack inventory by
        exact DevEUI, count, and current connection timestamp; the 2026-09-01 baseline is 27
        devices, but the live inventory at rollout time is authoritative.
  - [ ] Confirm Tracker remains inventory-only: no root/session keys or device addresses entered
        Sage, no second ChirpStack was installed, and gateway packet forwarding was not changed.

## Completed Preparation

- [x] Prepare Sage's ChirpStack Tracker for H02A against the existing IHV-CENIC MQTT and
      ChirpStack API endpoints without deploying a second network server.
  - [x] Confirm Sage portal inventory uses `lorawanconnections` and does not require LoRaWAN key
        records.
  - [x] Add a ChirpStack v4 API-key Tracker mode that registers hardware, devices, and H02A
        connections without reading or copying root/session keys.
  - [x] Add an H02A-scoped, secret-backed Kubernetes deployment and focused regression tests.
  - [x] Verify H02A reaches both IHV-CENIC MQTT port `1883` and ChirpStack API port `8080`.
  - [x] Resolve a live uplink through both endpoints and confirm the startup inventory contains
        all 27 currently configured, enabled IHV-CENIC devices.
  - [x] Create a dedicated read-only, tenant-scoped ChirpStack API key; install it as H02A Secret
        `ihv-cenic-chirpstack-api`; and retain it in the ignored mode-`0600` project `.env`.

- [x] Configure ChirpStack/MQTT to also output to Sage node H02A.
  - [x] Verify H02A can reach the existing IHV-CENIC MQTT broker and observe a live uplink.
  - [x] Prepare the standalone, multi-architecture Sage edge app and delivery-contract tests.
  - [x] Add an H02A-only job template and ECR review metadata.
  - [x] Obtain owner review and explicit approval for Sage ECR publication.
  - [x] Create the reviewed public `ordingj/sage-lorawan` GitHub source mirror required by ECR.
  - [x] Register/build version `0.1.0`, run a bounded dry-run canary, and verify logs.
  - [x] Submit production job `5780`, capture the PyWaggle metadata failure, and suspend it.
  - [x] Prepare version `0.1.1` with string-only metadata and a regression contract test.
  - [x] Obtain owner review and publish version `0.1.1` to ECR.
  - [x] Schedule production job `5782` and verify matching Sage Data API and Latest Records data.
