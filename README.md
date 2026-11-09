# FINAL FIXED SPRINT 1 — EECE430

# Pharmacy Management System

A small Django web app for managing a pharmacy's medication inventory. Built for EECE430.

## What it does

- Add, edit, delete and search medications
- Track quantity, minimum quantity, price, expiry date and shelf location
- Flag medications that are low on stock, close to expiring, or already expired
- Dashboard with totals and a short overview
- Notifications page that lists the three kinds of alerts
- Location finder: search a medication and see the walking route from the counter to its shelf on a floor map

## Rules used

- **Low stock:** quantity is equal to or below the minimum quantity
- **Near expiry:** expires within the next 14 days
- **Expired:** expiry date is before today

## How to run

You need Python 3 installed. On Windows (PowerShell):

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

On Command Prompt, activate with `.venv\Scripts\activate.bat` instead.
On Mac/Linux, use `python3 -m venv .venv` and `source .venv/bin/activate`.

Then open http://127.0.0.1:8000/ and add medications from the Medications page.

The database (`db.sqlite3`) is created when you run `migrate`. It is not stored in Git, so every new copy of the project starts empty.

## Location finder

Each medication has a location field. To show up on the map, the location must be one of the shelf codes **A1 to A8** or **B1 to B8**. Selecting a result draws the shortest path from the counter to that shelf. You can also click a shelf directly on the map.

The floor plan is only a sample layout. To match a real pharmacy, edit the `layout`, `shelves` and `start` values at the top of `static/core/finder.js`. The route is calculated in the browser with breadth-first search and goes around the shelves.

## Project structure

```
pharmacy_project/     project settings and main urls
core/
    models.py         Medication model
    forms.py          medication form and price validation
    views.py          dashboard, list, add/edit/delete, notifications, finder
    urls.py           page routes
    admin.py          Django admin setup
    services/
        stock.py      low-stock rule
        expiry.py     expired / near-expiry / days remaining
        search.py     medication search by name
    migrations/       database migrations
    tests.py          automated tests
templates/core/       HTML pages
static/core/
    style.css         styling
    finder.js         floor map and route finding
```

## Not included

- Login and user roles (anyone who can open the site can edit the data)
- Logging
- Automatic database backups

