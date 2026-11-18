import json
import os
import re
import secrets
from datetime import date
from urllib.parse import urlsplit

import mysql.connector
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

from database import close_db, execute, query
from tables import INPUT_TYPES, JOB_TYPES, LABELS, LIMITS, REQUIRED, STATUSES, TABLES

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or secrets.token_hex(32)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
app.teardown_appcontext(close_db)


def label(field):
    return LABELS.get(field, field.replace("_", " ").capitalize())


@app.context_processor
def shared():
    if "token" not in session:
        session["token"] = secrets.token_hex(16)
    return dict(tables=TABLES, label=label, token=session["token"],
                required=REQUIRED, types=INPUT_TYPES, limits=LIMITS)


@app.before_request
def check_token():
    if request.method == "POST":
        sent = request.form.get("token", "")
        saved = session.get("token", "")
        if not saved or not secrets.compare_digest(sent.encode(), saved.encode()):
            abort(400, description="Refresh the form and try again.")


def info_for(table):
    if table not in TABLES:
        abort(404)
    return TABLES[table]


def get_record(info, record_id):
    sql = info["sql"] + f" WHERE t.{info['pk']} = %s"
    row = query(sql, (record_id,), one=True)
    if row is None:
        abort(404)
    return row


def options_for(table):
    options = {}
    if table in ("jobs", "contacts"):
        companies = query("SELECT company_id, company_name FROM companies ORDER BY company_name")
        options["company_id"] = {
            str(c["company_id"]): c["company_name"] for c in companies
        }
    if table == "jobs":
        options["job_type"] = {v: v for v in JOB_TYPES}
    if table == "applications":
        jobs = query(TABLES["jobs"]["sql"] + " ORDER BY t.job_title")
        options["job_id"] = {
            str(j["job_id"]): f"{j['job_title']} - {j['company_name']}" for j in jobs
        }
        options["status"] = {v: v for v in STATUSES}
    return options


# Count each skill once.
def skills(value):
    if isinstance(value, str):
        value = value.replace("\n", ",").split(",")
    return {s.strip().casefold() for s in value if isinstance(s, str) and s.strip()}


def read_json(value, default):
    if value is None or value == "":
        return default
    return json.loads(value) if isinstance(value, str) else value


def job_skills(value):
    saved = read_json(value, [])
    if isinstance(saved, dict):
        saved = saved.get("skills", [])
    return skills(saved) if isinstance(saved, list) else set()


def rank_jobs(jobs, entered):
    have = skills(entered)
    results = []

    for job in jobs:
        needed = job_skills(job["requirements"])
        matched = sorted(have & needed)
        percent = round(100 * len(matched) / len(needed)) if needed else None
        results.append(dict(job, matched=matched, missing=sorted(needed - have),
                            total=len(needed), percent=percent))

    def order(row):
        score = row["percent"] if row["percent"] is not None else -1
        return -score, row["job_title"].casefold(), row["job_id"]

    return sorted(results, key=order)


# Check the form before saving it.
def read_form(info, options):
    data = {}
    for field in info["fields"]:
        raw = request.form.get(field, "").strip()
        value = raw or None

        if field in REQUIRED and not raw:
            raise ValueError(f"{label(field)} is required.")
        if field in LIMITS and len(raw) > LIMITS[field]:
            raise ValueError(f"{label(field)} is too long.")

        if field in options:
            if raw not in options[field]:
                raise ValueError(f"Choose a valid {label(field).lower()}.")
            value = int(raw) if field in ("company_id", "job_id") else raw

        elif field == "cover_letter_sent":
            value = raw == "1"

        elif field == "requirements":
            value = json.dumps(sorted(skills(raw)))

        elif field == "interview_data":
            try:
                details = json.loads(raw or "{}")
                if not isinstance(details, (dict, list)):
                    raise ValueError
                value = json.dumps(details, allow_nan=False)
            except (ValueError, RecursionError):
                raise ValueError("Interview details must be a JSON object or list.") from None

        elif raw and INPUT_TYPES.get(field) == "number":
            if not re.fullmatch(r"[0-9]{1,10}", raw) or int(raw) > 2147483647:
                raise ValueError("Salary must be a nonnegative whole number in range.")
            value = int(raw)

        elif raw and INPUT_TYPES.get(field) == "date":
            try:
                value = date.fromisoformat(raw)
                if value.isoformat() != raw or value.year < 1000:
                    raise ValueError
            except ValueError:
                raise ValueError("Enter a valid date in YYYY-MM-DD format.") from None

        elif raw and INPUT_TYPES.get(field) == "url":
            address = urlsplit(raw)
            if address.scheme not in ("http", "https") or not address.hostname:
                raise ValueError("Enter a full website address beginning with http:// or https://.")

        elif raw and field == "email" and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", raw):
            raise ValueError("Enter a valid email.")

        elif field == "notes" and len(raw.encode("utf-8")) > 65535:
            raise ValueError("The notes are too long.")

        data[field] = value

    low, high = data.get("salary_min"), data.get("salary_max")
    if low is not None and high is not None and low > high:
        raise ValueError("Minimum salary cannot be higher than maximum salary.")
    return data


@app.get("/")
def dashboard():
    counts = {
        t: query(f"SELECT COUNT(*) AS n FROM {t}", one=True)["n"] for t in TABLES
    }
    rows = query("SELECT status, COUNT(*) AS n FROM applications GROUP BY status")
    by_status = {r["status"]: r["n"] for r in rows}
    return render_template("dashboard.html", counts=counts, statuses=STATUSES,
                           by_status=by_status)


@app.get("/<table>")
def records(table):
    info = info_for(table)
    rows = query(info["sql"] + f" ORDER BY t.{info['pk']} DESC")
    return render_template(f"{table}.html", table=table, info=info, rows=rows)


@app.get("/<table>/<int:record_id>")
def detail(table, record_id):
    info = info_for(table)
    return render_template("detail.html", table=table, info=info,
                           row=get_record(info, record_id))


@app.route("/<table>/add", methods=["GET", "POST"])
@app.route("/<table>/<int:record_id>/edit", methods=["GET", "POST"])
def form(table, record_id=None):
    info = info_for(table)
    values = dict(get_record(info, record_id)) if record_id is not None else {}
    options = options_for(table)

    if request.method == "POST":
        try:
            data = read_form(info, options)
        except ValueError as error:
            flash(str(error))
            return render_template("form.html", table=table, info=info,
                                   values=request.form, options=options,
                                   record_id=record_id), 422

        fields = info["fields"]
        params = tuple(data[f] for f in fields)

        if record_id is None:
            columns = ", ".join(fields)
            slots = ", ".join(["%s"] * len(fields))
            record_id = execute(f"INSERT INTO {table} ({columns}) VALUES ({slots})", params)
        else:
            changes = ", ".join(f"{f}=%s" for f in fields)
            execute(f"UPDATE {table} SET {changes} WHERE {info['pk']}=%s",
                    params + (record_id,))

        flash(f"{info['name']} saved.")
        return redirect(url_for("detail", table=table, record_id=record_id))

    if table == "jobs":
        values["requirements"] = ", ".join(sorted(job_skills(values.get("requirements"))))
        values.setdefault("job_type", "Full-time")
    if table == "applications":
        values.setdefault("application_date", date.today().isoformat())
        values.setdefault("status", "Applied")
        values["interview_data"] = json.dumps(read_json(values.get("interview_data"), {}), indent=2)

    return render_template("form.html", table=table, info=info, values=values,
                           options=options, record_id=record_id)


@app.route("/<table>/<int:record_id>/delete", methods=["GET", "POST"])
def delete_record(table, record_id):
    info = info_for(table)
    row = get_record(info, record_id)
    if request.method == "POST":
        execute(f"DELETE FROM {table} WHERE {info['pk']}=%s", (record_id,))
        flash(f"{info['name']} deleted.")
        return redirect(url_for("records", table=table))
    return render_template("delete.html", table=table, info=info, row=row)


@app.route("/job-match", methods=["GET", "POST"])
def job_match():
    entered = request.form.get("skills", "")
    results = None
    if request.method == "POST":
        if skills(entered):
            results = rank_jobs(query(TABLES["jobs"]["sql"]), entered)
        else:
            flash("Enter at least one skill.")
    return render_template("job_match.html", entered=entered, results=results)


@app.errorhandler(mysql.connector.Error)
def database_error(error):
    if error.errno in (1451, 1452):
        return render_template(
            "error.html",
            message="Check the linked records. Move or delete child records first."
        ), 409
    app.logger.exception("MySQL error")
    return render_template("error.html",
                           message="Check MySQL, your .env settings, and schema.sql."), 503


if __name__ == "__main__":
    app.run()