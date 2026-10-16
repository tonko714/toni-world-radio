# Toni's World Receiver 📻

Web-App: https://tonko714.github.io/toni-world-radio/

## What's running
- Nine real-radio SW ranges, 5-kHz tuning, UTC time and weekday filters, source-labeled station cards.
- Generated `senderdaten.json` combines verified HFCC schedule downloads over HTTPS with EiBi records from a third-party HTTPS mirror. Updates run on Mondays at 06:17 UTC and via Actions.
- `hfcc_html.py`: official HFCC timetable parser.
- `eibi_mirror.py`: EiBi semicolon CSV parser with safe day/date filtering and validation.
- `update_database.py`: atomic merge, timestamp and per-source import status.
- Tests: `python -m unittest test_hfcc_html test_eibi_mirror -v`.

## EiBi certificate workaround and trust
The official EiBi host currently has a **hostname-mismatched HTTPS certificate**. Disabling verification is not acceptable. EiBi traditionally distributes the CSV over plain HTTP, which lacks tamper-resistant transport.

Instead we fetch from **https://github.com/cdburgess75/SkyWave/tree/data** (a separately maintained EiBi mirror) using valid HTTPS. The parser checks the mirror metadata, expected season, byte count, row count, age, CSV structure and plausible schedules before publishing. The original provider is **Eike Bierwirth (EiBi)**, not the mirror author.

**Trust limitation:** HTTPS authenticates the GitHub mirror, not the original EiBi data. Fully authoritative authentication would require EiBi to offer working HTTPS or signed official releases. Source provenance is retained in each record and source statistics.

## Data behavior
EiBi entries with special or ambiguous weekday markers are skipped instead of falsely treated as daily. Inactive/out-of-season entries are skipped; partial-season entries are evaluated against the date of import. HFCC/EiBi records are kept distinguishable because publisher schedules may overlap.

The generated JSON includes source counts and warnings. If EiBi fetching fails, validated HFCC data still update; the EiBi status reflects the failure.

**This is a schedule reference and reception simulation, not actual radio reception.** Schedule listings do not establish actual signal strength or guaranteed reception in Cologne.

Sources and usage conditions:
- Official HFCC: https://new.hfcc.org/data/
- EiBi: https://www.eibispace.de/ (official README at http://www.eibispace.de/dx/README.TXT)
- Mirror: https://github.com/cdburgess75/SkyWave/tree/data
