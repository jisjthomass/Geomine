# AGENTS.md

## Project overview
This repository is a Python-based Streamlit dashboard for exploring well and GIS data. The main app entry point is `app.py`, with data and map logic split across the other Python modules in the project root.

## Working conventions
- Prefer the project-local Python environment instead of a global interpreter.
- Keep commands run from the repository root unless a module specifically requires a different working directory.
- Preserve the current module split: `app.py` for UI wiring, `data_source.py` for data loading, `api_client.py` for API access, `gis_engine.py` for GIS logic, and `map_component.py` for map rendering.
- Avoid introducing heavy framework churn or broad refactors without a clear need.
- Keep configuration values centralized in `config.py` and do not hard-code environment-specific secrets in module code.

## Python and environment setup
- Use the workspace virtual environment when running Python commands. If the editor is configured for Python environment files, prefer `.env`-based values and keep `python.terminal.useEnvFile` enabled for terminal sessions.
- When installing dependencies, do it from the project root with the active environment:
  - `python -m pip install -r requirements.txt`
- Run the dashboard with:
  - `python -m streamlit run app.py`

## Routine workflow for agents
1. Inspect the relevant module before editing; this project is intentionally small and file-level organization matters.
2. Keep changes narrow and consistent with the existing naming and layering.
3. Validate with the smallest relevant run or import check after changes.
4. If environment variables are needed, document them in configuration code or `.env` examples instead of burying them in runtime logic.

## Expected pitfalls
- Do not assume the app is packaged as a package; it is a flat Python project in the repository root.
- If a script fails because the interpreter or environment is wrong, check the selected Python environment before diagnosing business logic.
- The empty module files should be treated as a lightweight structure, not as a sign that the app is already fully implemented.
