# Repository instructions

This repository builds bilingual maps of Brazil in Python.

## Required behavior

- Write code, documentation, command help, comments, and metadata in plain American English.
- Map copy must exist in both Brazilian Portuguese (`pt-BR`) and American English (`en-US`).
- Build both language versions from the same prepared geometry and typed values.
- Keep every master map exactly 7.5 × 7.5 inches.
- Include the approved globe locator on every map.
- Prefer official, edition-locked IBGE cartography for Brazilian base layers.
- Verify source files with expected byte size and SHA-256 before use.
- Clearly label synthetic examples and never present them as observations.
- Treat rural-property and supplier data as sensitive by default.
- Do not copy proprietary visual assets or styles from other publications.

## Before committing

Run `make test`, run the linter, build both languages, and visually inspect the final PNGs. Do not commit raw downloaded data, local environments, credentials, or partial outputs.
