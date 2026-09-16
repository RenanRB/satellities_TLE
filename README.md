# Satellite TLE Data Generator

The Satellite TLE Data Generator retrieves GNSS satellite information from the
Celestrak website and generates JSON files for easy usage. By simply reading one
of the files under `data/`, users get all available TLEs (Two-Line Elements) for
that constellation at the given moment. The data is refreshed automatically
every 12 hours by GitHub Actions.

## Constellations

| File | Constellation | Celestrak source |
| --- | --- | --- |
| `data/gps.json` | GPS (USA) | `GROUP=gps-ops` |
| `data/glo.json` | GLONASS (Russia) | `GROUP=glo-ops` |
| `data/galileo.json` | Galileo (EU) | `GROUP=galileo` |
| `data/beidou.json` | BeiDou (China) | `GROUP=beidou` |
| `data/qzss.json` | QZSS / Michibiki (Japan) | `GROUP=gnss`, filtered by name |

Celestrak has no dedicated QZSS group, so `qzss.py` fetches the full `gnss`
group and filters satellites named `QZS-*`.

## Format

Each file is a JSON array of `[name, line1, line2]` triples:

```json
[
    [
        "QZS-2 (QZSS/PRN 194)",
        "1 42738U 17028A   26257.81540112 -.00000175  00000+0  00000+0 0  9998",
        "2 42738  39.2998 241.8342 0750218 270.4378 276.5126  1.00260830  8528"
    ]
]
```

## Validation

Celestrak answers with HTTP 200 even on errors (for example the single-line body
`Invalid query: ...`), so the status code alone is not enough. Before anything is
written, `tle_fetch.py` checks that the response has a multiple of 3 lines, that
each orbital line is 69 characters with the correct `1 `/`2 ` prefix and a valid
TLE checksum, and that the satellite count is above a per-constellation floor.
Requests use an explicit timeout and are retried with exponential backoff. A
constellation is never committed with partial or corrupted data — the run fails
instead.

## Consolidated source (`data/gnss/`, in validation)

Celestrak's `GROUP=gnss` is an exact superset of `gps-ops`, `glo-ops`,
`galileo`, `beidou` and `sbas`, plus the NavIC satellites, so a **single
request** yields every network below. Since most workflow failures here are
Celestrak timeouts, one request instead of five cuts that exposure
proportionally, and all constellations end up sharing the same epoch.

| File | Network |
| --- | --- |
| `data/gnss/gps.json` | GPS (USA) |
| `data/gnss/glo.json` | GLONASS (Russia) |
| `data/gnss/galileo.json` | Galileo (EU) |
| `data/gnss/beidou.json` | BeiDou (China) |
| `data/gnss/qzss.json` | QZSS / Michibiki (Japan) |
| `data/gnss/navic.json` | NavIC / IRNSS (India) |
| `data/gnss/sbas.json` | SBAS augmentation GEOs: WAAS, EGNOS, GAGAN, SDCM |
| `data/gnss/all.json` | all of the above, keyed by network |

The per-network files are kept separate on purpose: a given drone model
supports only some constellations, so the consumer fetches just what it needs.
Every satellite appears in exactly one file — the 171 in `all.json` are
distinct, with no duplication between networks.

`sbas.json` is what remains after the navigation constellations are matched,
which by construction of the group is the augmentation payloads. Celestrak
already ships them here with their PRN labels (`SES-5 (EGNOS/PRN 136)`), so no
extra request is needed. Three names arrive truncated by Celestrak's 24-character
limit (`EUTELSAT 5 WEST B (EGN*)`); they are truncated identically in
`GROUP=sbas`, so nothing is lost by not querying it.

The one detail `GROUP=sbas` would add is that BeiDou's three GEO satellites also
broadcast an SBAS signal: they appear there as `BEIDOU-3 G1 (PRN 130)`, whereas
here they are in `beidou.json` as `BEIDOU-3 G1 (C59)`. Same satellites, same
orbital data, different label. The five QZSS satellites are likewise dual-role
and live in `qzss.json`.

### Migration

The five per-constellation files are **byte-identical** to the ones in `data/`,
so migrating is a path change and nothing else. The legacy `data/*.json` files
and their five workflows keep running untouched until the migration is
validated; once the consumer reads from `data/gnss/`, the old workflows and
scripts can be deleted.

Each network has a minimum satellite count: if Celestrak renames satellites and
a classification rule stops matching, the run fails instead of committing a
short file. The contents of `sbas.json` are printed to the job log on every run,
which is where a new network appearing inside `GROUP=gnss` would show up.

## Use case

I currently use this project to feed the data used in my application:
https://droneweather.xyz/, I use the library:
https://github.com/jhermsmeier/node-tle to read the data and build the necessary
information for presentation.
