# PulseWatch

A small uptime-monitoring dashboard (Flask + SQLite): add endpoints, check
their status, browse check history.

> ⚠️ **Intentionally vulnerable.** This app exists as a target for automated
> security-remediation experiments. Do not deploy it or reuse its code.

## Run

```bash
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./.venv/bin/python -m app.db        # create + seed the database
./.venv/bin/python -m app.server    # http://localhost:5000
```
