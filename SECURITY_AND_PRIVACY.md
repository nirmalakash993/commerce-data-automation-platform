# Security and Privacy

## Current release status

The clean-room publication scope, repository creation, and public visibility are owner-approved. Exact-tree and reachable-history scans pass; final acceptance still depends on post-publication signed-out QA recorded in the publication controls.

## Data policy

- Use generated data only. Never mask, hash, perturb, sample, or redact a real row into a fixture.
- Use fictional source labels, identifiers, dates, object names, and the fake currency code `TST`.
- Do not include customer, employee, shipment, payment, address, contact, location, tax, product, pricing, margin, or free-text production data.
- Recreate every visual from synthetic inputs. Do not blur or crop a production screenshot into a public asset.

## Secret and identifier policy

The public tree must contain no credentials, tokens, keys, cookies, connection strings, signed links, mailbox addresses, account names, internal domains, cloud project identifiers, bucket names, datasets, table names, spreadsheet or folder identifiers, absolute paths, or vendor-specific endpoints.

The current implementation has no configuration or environment file and reads no environment variable. If configuration is added later, every value must be an obvious placeholder and the exact file must pass secret and identifier scans.

## Access and change boundaries

- The demo runs locally using only explicit synthetic fixtures.
- Read access and write access should be separated where connectors are eventually added.
- A plan or dry run must precede consequential writes.
- Production visibility, schedules, credentials, and cloud resources are out of scope for this repository.

## Repository-history policy

Create any future repository from a fresh directory. Do not copy an existing `.git` directory or attach a remote to a historical source tree. Before visibility changes, scan both the working tree and every commit for secrets, identities, proprietary terms, and real data.

## Third-party and dependency review

The current dependency review is in `docs/DEPENDENCY_REVIEW.md`: runtime and tests use only Python standard-library modules, with no connector or redistributed third-party asset. Any future dependency requires a new version, license, maintenance, and permission review.

## Incident response before publication

If a secret-shaped or confidential value is discovered, stop publication, remove the artifact from the candidate, assess whether the value was ever active, rotate or revoke it where applicable, and rescan the complete history. Deleting a value from the latest commit alone is insufficient.
