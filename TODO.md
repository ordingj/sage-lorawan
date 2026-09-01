# TODO

<!-- working-on: configure chirpstack/mqtt to also output to sage node h02a -->

- [/] Configure ChirpStack/MQTT to also output to Sage node H02A.
  - [x] Verify H02A can reach the existing IHV-CENIC MQTT broker and observe a live uplink.
  - [x] Prepare the standalone, multi-architecture Sage edge app and delivery-contract tests.
  - [x] Add an H02A-only job template and ECR review metadata.
  - [x] Obtain owner review and explicit approval for Sage ECR publication.
  - [x] Create the reviewed public `ordingj/sage-lorawan` GitHub source mirror required by ECR.
  - [x] Register/build version `0.1.0`, run a bounded dry-run canary, and verify logs.
  - [ ] Schedule the production subscriber and verify matching records in the Sage Data API.
