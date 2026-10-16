# Toni's World Receiver 📻

Mobile-first shortwave receiver simulator based on the nine SW ranges photographed from Toni's physical radio.

## Status
- `index.html`: interactive interface (SW 1–9, tuner, frequency filters, local imports and favorites).
- `import_schedules.py`: draft parser for HFCC ITU and EiBi schedule files. Parsing of the full official archives is **not yet end-to-end validated**.
- `update_database.py`: draft fetch, validate and export pipeline.
- `.github/workflows/update.yml`: weekly scheduled attempt every Monday 06:17 UTC and manual dispatch. A workflow run **does not prove** the import succeeded; verify the Actions logs and generated `senderdaten.json`.
- No fabricated station data is bundled. The directory can be empty until real files are successfully parsed.

## Hosting
This repository is currently private. To publish on GitHub Pages under a regular GitHub Free account, make it public first (Settings → General → Danger Zone → Change repository visibility). Then enable Pages under Settings → Pages → Build and deployment → Deploy from a branch → main / (root). The expected URL would be https://tonko714.github.io/toni-world-radio/ once GitHub actually deploys it.

## Run and test locally
Open index.html in a browser. For a server: `python -m http.server 8000`, then visit http://localhost:8000.

## Data
HFCC: https://new.hfcc.org/data/ ; EiBi: https://www.eibispace.de/ . Seasonal schedules in UTC can differ from actual reception and may be wrong or superseded. Attribution and reuse terms must be respected. Never interpret an empty listing as a free frequency.

## Next
Test downloads and full A26/B26 files; resolve HFCC broadcaster and transmitter codes; normalize EiBi day exceptions; add validation and a clear data freshness indicator.
