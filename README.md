# FINAL FIXED SPRINT 1 — EECE430

**Extract into a NEW folder** (for example `pharmacy_sprint1_FIXED`). Do not merge with your old `pharmacy_sprint1` folder or its `db.sqlite3` and `core/migrations/` files. Your old data is not transferred into this new demo project.

Windows PowerShell / VS Code terminal:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py test
python manage.py runserver
```

If your terminal is Command Prompt instead of PowerShell, activate with `.venv\Scripts\activate.bat`.

Open http://127.0.0.1:8000/ . Add medications through the interface. No `makemigrations` is needed: `core/migrations/0001_initial.py` is included.

**To keep existing medications:** Do NOT replace your old database. Ask for a data-preserving migration based on your original `core/models.py` and migrations. This fresh demo package intentionally starts with an empty database.

**Testing note:** Source files were syntax-checked, but Django integration tests could not be executed in the build environment. Run `python manage.py test` locally.

## What each file does

- `manage.py`: runs Django commands.
- `pharmacy_project/settings.py`: database, templates, static assets, and app configuration.
- `pharmacy_project/urls.py`: routes `/admin/` and delegates the site to `core`.
- `pharmacy_project/asgi.py` / `wsgi.py`: deployment entry points (not needed for local demo).
- `core/models.py`: Medication table and properties that call shared services.
- `core/services/stock.py`: reusable low-stock rule.
- `core/services/expiry.py`: reusable expired/near-expiry and days-remaining rules.
- `core/services/search.py`: reusable medication search.
- `core/forms.py`: validates medication input and generates form fields.
- `core/views.py`: handles dashboard, CRUD, alerts, and finder requests.
- `core/urls.py`: connects page addresses to views.
- `core/admin.py`: optional Django admin medication management.
- `core/tests.py`: automated tests for stock thresholds, expiry, search, creation and validation.
- `core/apps.py`: app configuration.
- `core/migrations/`: Django-generated database changes; created by `makemigrations`.
- `templates/core/base.html`: shared sidebar and page layout.
- `templates/core/dashboard.html`: statistics and overview.
- `templates/core/medication_list.html`: searchable inventory table.
- `templates/core/medication_form.html`: add/edit medication form.
- `templates/core/medication_confirm_delete.html`: deletion confirmation.
- `templates/core/notifications.html`: three alert lists.
- `templates/core/location_finder.html`: shelf lookup.
- `static/core/style.css`: mint-green styling.

- `.gitignore`: excludes database and local environment from Git.




## Architecture coverage

- UI: HTML/CSS screens.
- Login/screen management: URL routing only; authentication and roles are NOT implemented.
- Application components: inventory, expiry, notifications and shelf finder.
- Shared services: stock, expiry and search helpers. Logging and encryption are NOT implemented.
- Database: SQLite. Automatic daily backup is NOT implemented.

This is a classroom demo, not suitable for real patient data or production pharmacy use.


## Interactive floor-map location finder
Search for a medication and select its result to display the shortest walking path from the counter to the assigned shelf. The floor plan and route logic are in `static/core/finder.js`. The map is a demonstration layout, not a scan or automatically generated plan of a real store. Use location codes A1–A8 or B1–B8 for sample medications. Change the `layout`, `shelves`, and `start` constants to match the actual pharmacy. Routes are calculated in-browser with breadth-first search and avoid blocked shelf tiles. No new migrations are required for this feature.
