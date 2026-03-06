# Tools

Python scripts for deterministic execution — API calls, data transformations, file operations, database queries.

## Conventions
- Each script should do one thing well and be independently testable.
- Read credentials from `../.env` (never hardcode keys).
- Write intermediate outputs to `../tmp/`.
- Print clear success/error messages so the agent can detect failures.

## Usage
```bash
python tools/<script_name>.py
```
