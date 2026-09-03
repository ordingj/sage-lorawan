# Sage LoRaWAN Forwarder for IHV-CENIC

This app publishes decoded sensor observations from IHV-CENIC's vineyard LoRaWAN network
through Sage node H02A. It listens to the existing ChirpStack MQTT application-uplink stream
and republishes decoded values through PyWaggle. It does not change device codecs, ChirpStack
integrations, or the existing ThingsBoard, InfluxDB, and PostgreSQL delivery paths.

## Scientific purpose

The vineyard's distributed low-power sensors observe soil, atmospheric, radiation, pressure,
and equipment conditions. Depending on the device, measurements include soil temperature,
water content and conductivity; air temperature, relative humidity, pressure and CO2; pipe
pressure; UV-A irradiance; and battery state.

The forwarder preserves each observation's original ChirpStack timestamp and device identity.
This supports comparison with the existing IHV-CENIC data paths without silently changing the
scientific record.

## Published data

Each scalar in a decoded ChirpStack `object` becomes a Sage measurement. Nested fields are
flattened with underscores and names are normalized to lowercase. For example,
`messages[0].measurementValue` becomes `messages_0_measurementvalue`.

Records include source and radio context such as:

- device name and DevEUI;
- tenant, application, and device-profile identity;
- deduplication ID, frame counter, FPort, and data rate; and
- receiver RSSI and SNR.

For devices in the IHV-CENIC field map, records also include `device_label`, `block`, `slope`,
`latitude`, and `longitude`. Missing field-map values are omitted rather than guessed.

Known physical measurements include `meta.units`, including `V`, `%`, `ppm`, `%RH`, `hPa`,
`kPa`, `°C`, `µS/cm`, and `W/m²`. Status fields, counters, identifiers, and unknown measurement
types remain unitless.

Delivery is at least once. Consumers can identify a replay using the measurement name together
with `deduplicationId`, `devEui`, and `fCnt`.

## View the data

Open the [H02A Query Browser](https://portal.sagecontinuum.org/query-browser?nodes=H02A&apps=registry.sagecontinuum.org%2Fordingj%2Fihv-cenic-chirpstack-devices%3A0.2.0.*&start=-5m&page=0)
to view current measurements. Units appear beside supported values. Enable **meta** above the
results table to display the device label, block, slope, coordinates, and other provenance.
