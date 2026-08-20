# Dependency Review

Review date: 2026-08-20

## Runtime and tests

The implementation imports only Python standard-library modules:

- `argparse`, `csv`, `datetime`, `hashlib`, `json`, `pathlib`, and `random`;
- `collections`, `contextlib`, and `dataclasses`;
- `sqlite3` for the portable local warehouse;
- `tempfile` and `unittest` in tests.

No third-party package, cloud SDK, connector, JavaScript package, binary, vendored source, font, image, or externally hosted runtime asset is required.

## Network and credentials

The code contains no HTTP client, socket call, cloud client, credential loader, secret manager, environment-variable read, or production configuration path. The generator accepts only a destination directory and deterministic seed.

## License implications

The repository does not redistribute Python or SQLite. It relies on the user's installed Python runtime. No third-party notice file is required for the repository's current contents.

The repository itself intentionally has no license; public visibility is not represented as permission to reuse the code or documentation.

## Recheck trigger

Any future dependency, connector, asset, generated binary, or installation step requires a new maintenance, permission, transitive-dependency, and license review before release.
