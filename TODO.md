# TODO

## Sage Rollout Finalization

- [ ] Finalize the Sage H02A rollout for IHV-CENIC ChirpStack devices.
  - [ ] Ask a Sage administrator to retrieve or rotate H02A's server-side node-auth token, then
        install it as H02A Secret `django-token`, key `token`, without exposing the value in Git,
        shell arguments, logs, or command history.
  - [ ] Re-run `make all`, review the complete version `0.2.0` source and deployment diff, and
        obtain explicit owner approval before any push, ECR publication, or Tracker deployment.
  - [ ] Push the approved `main` branch to the canonical `ihv-cenic1/sage-lorawan` GitLab project
        and synchronize the public `ordingj/sage-lorawan` GitHub mirror used by Sage ECR.
  - [ ] Publish `ordingj/ihv-cenic-chirpstack-devices:0.2.0` to Sage ECR and verify that its
        immutable image digest supports both `linux/amd64` and `linux/arm64`.
  - [ ] Apply `deploy/tracker-deployment.yaml` on H02A; verify rollout completion, zero restarts,
        successful startup inventory reconciliation, and continued QoS-1 live refreshes.
  - [ ] Compare H02A **LoRaWAN Devices** against a fresh enabled-device ChirpStack inventory by
        exact DevEUI, count, and current connection timestamp; the 2026-09-01 baseline is 27
        devices, but the live inventory at rollout time is authoritative.
  - [ ] Confirm Tracker remains inventory-only: no root/session keys or device addresses entered
        Sage, no second ChirpStack was installed, and gateway packet forwarding was not changed.
  - [ ] Confirm production forwarder job `5782` remains healthy on version `0.1.1`, continues
        publishing current Data API records, and still shows LoRa Device Name while the optional
        conventional Sensor column remains blank as documented.
  - [ ] Record the reviewed commits, ECR digest, Tracker deployment proof, final device count,
        and forwarder regression evidence in `README.md`, `CHANGELOG.md`, and this TODO; then mark
        the rollout complete.

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
