# TODO

<!-- working-on: Wire Sage's ChirpStack Tracker on H02A to the existing IHV-CENIC MQTT and ChirpStack API endpoints without deploying a second network server. -->

## Tracker Integration

- [/] Wire Sage's ChirpStack Tracker on H02A to the existing IHV-CENIC MQTT and ChirpStack API
      endpoints without deploying a second network server.
  - [x] Confirm Sage portal inventory uses `lorawanconnections` and does not require LoRaWAN key
        records.
  - [x] Add a ChirpStack v4 API-key Tracker mode that registers hardware, devices, and H02A
        connections without reading or copying root/session keys.
  - [x] Add an H02A-scoped, secret-backed Kubernetes deployment and focused regression tests.
  - [x] Verify H02A reaches both IHV-CENIC MQTT port `1883` and ChirpStack API port `8080`.
  - [x] Resolve a live uplink through both endpoints and confirm the startup inventory contains
        all 27 currently configured, enabled IHV-CENIC devices.
  - [ ] Obtain owner review and publish version `0.2.0` to Sage ECR.
  - [ ] Create a dedicated tenant-scoped ChirpStack API key, obtain H02A's `django-token` from a
        Sage administrator, and install both required secrets.
  - [ ] Deploy Tracker, confirm all active devices under H02A **LoRaWAN Devices**, and verify
        production forwarder job `5782` remains healthy.

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
