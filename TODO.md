# TODO

- [x] Record qualified node-local loader activation. The patched loader has one consumer
      and prefetch 250. All 431,205 captured messages have a verified durable archive.
      Independent source checks verify 142 fresh local observations. The rule query works,
      and the waiting queue clears with zero observed warnings, errors or restarts. Keep
      historical backfill and helper cleanup required in the IHV recovery task. Retain older
      originals outside the unchanged two-day bucket. Track seven cloud text responses that
      omit original carriage returns separately from the passing local-delivery gate.
- [x] Qualify and roll out Tracker `0.2.7`. The native canary and production startup reconcile
      all 27 devices. Three inventory audits retain every connection ID and hardware link, with
      exactly 27 active connections. Production has 45 live updates across 21 devices and zero
      warnings, errors or restarts at the final check. Preserve credentials, settings and the
      stable MQTT session. Remove both owned helpers. The forwarder remains unchanged, and 86
      fresh cloud records pass the destination check. All 40 tests, lint, native build and CLI
      checks pass. Keep the immutable `0.2.5` Tracker manifest for rollback.
- [x] Fix the unsupported SDI-12 empty-object ordering in candidate `0.2.7`. Replay the exact
      rejected archive events, preserve valid outputs, verify acknowledgement without publication,
      and keep other empty objects invalid. All 40 tests, lint, native image build and CLI smoke
      checks pass. Publication and live qualification remain separate.
- [x] Publish and image-qualify `0.2.7`. Jenkins build `10` succeeds from reviewed source
      `ecbb0d2`, and hosted pipeline `92826` passes. Both published platform images pass CLI,
      source-hash and unsupported-port checks. Keep 0.2.5 and 0.2.6 registry digests unchanged.
- [x] Activate `0.2.7` after the user accepts the clean 3,019-second live canary. Its one
      filtered event does not pass the original two-event gate. Preserve that result and the
      explicit acceptance. Job `5792` is suspended, and native checks prove the old writer stops
      before job `5871` starts. The exact published image is the sole native writer. Fresh
      destination readback verifies 112 records from 12 source events across nine devices,
      with complete identity, expected units and no invalid sentinels. Tracker remains on 0.2.5
      at that cutover. Retain the old spec and job for rollback. Local loader recovery remains separate.

## Python 3.14 release

- [x] Publish version `0.2.6` with the qualified Python 3.14.7 base and HTTP response cleanup.
  - Jenkins build `9` publishes reviewed source `df193ac` for AMD64 and ARM64.
  - Hosted pipeline `92751`, all 36 tests, source hashes and both published CLI checks pass.
  - Keep the accepted 0.2.5 image and production templates. A new live canary remains required
    before production activation. This publication makes no workload change.

## Sage Forwarder Measurement Metadata

- [x] Publish and roll out version `0.2.5` with complete sensor-sentinel safeguards.
  - [x] Cover invalid SDI-12 ports and battery voltage, Dragino soil-probe availability,
        TEROS-22 errors, and Milesight EM500 CO2/pressure errors with focused tests.
  - [x] Publish the reviewed AMD64/ARM64 image, run a bounded H02A canary, and roll production
        forward only after current records prove the invalid values remain absent.
  - Version `0.2.4` was published by Jenkins build `7`, but the first Tracker rollout exposed
    intermittent H02A DNS resolution. Version `0.2.5` adds bounded transient-request retries and
    is the replacement release.
  - Jenkins build `8` published commit `78f7ab1` for AMD64 and ARM64 at manifest-list digest
    `sha256:587d318403966ad82010378fbda6cae81c37094982a37e0bd2e51c0d05c6f498`.
  - Canary `5791` ran for 10 minutes 50 seconds with 53 decoded uplinks, zero invalid sentinel
    measurements, zero runtime failures, and zero restarts before it was suspended and its
    lingering node pod removed. Production `5789` was suspended and replaced by job `5792`.
  - The initial `0.2.5` Data API proof returned 110 records from 17 uplinks across 13 devices;
    all records retained identity metadata, four carried explicit false availability, and none
    contained a filtered sentinel.

- [x] Suppress Dragino's `temp_ds18b20 == 327.6` unavailable sentinel and publish an
      external-temperature-sensor availability measurement instead.
  - ECR build `6` published commit `84f9a8b` for AMD64 and ARM64 at manifest-list digest
    `sha256:340cace84379d3f19c3ec875e1fc5051cdddbc7d1b9b1ff5d1237e479a198c01`.
  - H02A canary job `5788` ran uninterrupted for about 11 minutes and was suspended. Previous
    production job `5787` was suspended, and production job `5789` is running version `0.2.3`.
  - Initial production proof returned 112 records across 12 devices, four false availability
    records (rendered by Sage as `0`), no sentinel temperatures, and complete identity metadata.

- [x] Deploy version `0.2.0` to H02A, verify fresh measurements expose units and canonical
      field metadata.
  - ECR build `0.2.0` used commit `60938a1efafc17143b5a3557e849906fca00215a` and published
    the AMD64/ARM64 manifest list at digest
    `sha256:9d8c240737143e4e504d7912b226cdadaea138ffe0a6ef4cb64a033b7c8b1dee`.
  - H02A canary job `5786` passed and was suspended; accidental duplicate `5785` was also
    suspended. Production job `5782` was suspended and replaced by active `0.2.0` job `5787`.
  - The Data API and Query Browser show live atmospheric, battery, and `temp_soil`,
    `conduct_soil`, and `water_soil` units plus mapped field metadata.
  - Catalog-only version `0.2.2` was built from commit
    `bdcf79a` with the same multi-architecture digest as `0.2.0`; the My App Science Overview
    now contains only the scientific purpose, published data and metadata, and viewing guidance.
  - [x] Replace the deployment-history-heavy Science Overview with concise user documentation
        and publish it as catalog version `0.2.2`.
  - [ ] Stop the stale `0.1.1` task from removed job `5782`; Sage still reports current
        `0.1.1` records even though the job inventory marks it removed. Direct H02A SSH currently
        rejects the available public key, so node-owner or Sage operator access is required.

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

## Tracker Deployment

- [x] Deploy Tracker for H02A LoRaWAN inventory; it remains separate from the working
      measurement-forwarding path.
  - [x] Retrieve H02A's server-side node-auth token, then
        install it as H02A Secret `django-token`, key `token`, without exposing the value in Git,
        shell arguments, logs, or command history.
  - [x] Apply `deploy/tracker-deployment.yaml` on H02A; verify rollout completion, zero restarts,
        successful startup inventory reconciliation, and continued QoS-1 live refreshes.
  - [x] Compare H02A **LoRaWAN Devices** against a fresh enabled-device ChirpStack inventory by
        exact DevEUI, count, and current connection timestamp; the 2026-09-01 baseline is 27
        devices, but the live inventory at rollout time is authoritative.
  - [x] Confirm Tracker remains inventory-only: no root/session keys or device addresses entered
        Sage, no second ChirpStack was installed, and gateway packet forwarding was not changed.
  - Live preflight exposed Sage Auth's two-decimal battery contract, then reconciled the fresh
    27-device ChirpStack inventory after rounding battery values and normalizing device names.
  - Live `0.2.5` proof matched 27 enabled ChirpStack devices to 27 H02A Sage connections with no
    missing or extra DevEUIs, exact current timestamps, no sensitive inventory fields, and live
    QoS-1 refreshes. The final pod used the published digest and remained at zero restarts.

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
