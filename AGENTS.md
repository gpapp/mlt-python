# AGENTS.md

## Setup
- `uv sync` to install dependencies
- Requires Python >= 3.10

## Commands
- Tests: `uv run pytest tests/ -v`
- No lint, typecheck, or format tools configured

## Package Structure
- Import name: `mlt_python` (not `mlt_xml` or `mlt-xml`)
- Source: `src/mlt_python/`
- Package name in pyproject.toml: `mlt-xml`

## API Notes
- All public methods use timecodes (HH:MM:SS:FF), not frame numbers
- Main entrypoint: `MLTProject` class in `project.py`
- Profile presets: `hd1080_30`, `hd1080_25`, `hd720_30`, `uhd_30`, etc.
- Output files use `.kdenlive.xml` extension for Kdenlive compatibility
- Kdenlive 23.08+ Compatibility:
    - Detailed technical requirements are documented in [MLT_XML.md](./MLT_XML.md).
    - Key discovery: `main_bin` properties must precede entries, and tracks must be tractor-wrapped.

## Repository
- Pure Python library, no MLT framework dependency
- No CI workflows or pre-commit hooks configured
- Single package, not a monorepo

## MLT documentation
https://www.mltframework.org/docs/xml/ 

## Hint
Be decisive, the user is looking for a clear, concise and correct answer.
Do not add unnecessary explanations, comments or other information. It frustrates the user. You want to be concise, efficient and helpful, not verbose.