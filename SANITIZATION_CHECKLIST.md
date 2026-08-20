# Sanitization Checklist

## Completed for the clean-room candidate

- [x] Content is limited to the strategy-approved umbrella item.
- [x] Production source code, SQL, notebooks, configuration, logs, and prompts are absent.
- [x] Employer, customer, partner, colleague, and vendor identities are absent.
- [x] Internal project IDs, cloud identifiers, bucket names, dataset names, table names, account names, email addresses, URLs, and absolute paths are absent.
- [x] Historical metrics, commercial values, pricing, costs, margins, and performance claims are absent.
- [x] Example records are invented and use fictional identifiers, future dates, and the fake currency code `TST`.
- [x] No production screenshot or redacted production visual is included.
- [x] AI claims distinguish development assistance from deterministic runtime logic.
- [x] No badge or coverage figure is asserted; only commands and results actually executed against the clean-room tree are recorded.
- [x] No `LICENSE` file or open-source claim is included.

## Clean-room implementation review

- [x] Every implementation file was authored in the fresh clean-room tree; no Python file is byte-identical to a source-project Python file.
- [x] Runtime and tests use only the Python standard library; dependency and license implications are documented.
- [x] Source, documentation, fixtures, and the Mermaid asset were scanned; no archive, notebook, raster image, or generated output is committed.
- [x] No configuration or environment example exists.
- [x] Fixture generation accepts only an output directory and deterministic seed and cannot read a production input or configuration.
- [x] No binary image or document metadata exists in the candidate.
- [x] Exact internal-name, identifier, email, path, URL, real-value, and secret-shape scans pass.
- [ ] Review the complete Git history; do not rely only on the current working tree.
- [ ] Inspect the rendered repository while signed out.

## Release rule

Any unchecked item keeps publication blocked.
