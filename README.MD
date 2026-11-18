# Job Application Tracker

This is my course project for tracking job applications. It uses Flask, MySQL, HTML, and CSS. I can save companies, jobs, applications, and contacts. The Job Match page shows how many required skills match the skills I enter.

## How to run it

1. Install Python 3.12 and MySQL Server 8.0.16 or newer.
2. Clone this repository and open PowerShell in the folder that contains `app.py`.
3. Open `schema.sql` in MySQL Workbench and run the whole file.
4. Use a local MySQL account with SELECT, INSERT, UPDATE, and DELETE access to `job_tracker`. To create one, run this in Workbench with your own password:

```sql
CREATE USER IF NOT EXISTS 'job_tracker_user'@'localhost'
IDENTIFIED BY 'YOUR_LOCAL_PASSWORD';
GRANT SELECT, INSERT, UPDATE, DELETE ON job_tracker.*
TO 'job_tracker_user'@'localhost';
```

5. Run these commands in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

6. Open `.env`. Enter your MySQL password and use the printed string for `SECRET_KEY`.
7. Start the app:

```powershell
.\.venv\Scripts\python.exe app.py
```

8. Open `http://127.0.0.1:5000`. Add a company first, then add a job and an application.

## Tests

Run `.\.venv\Scripts\python.exe -m unittest -v test_match`.

## Video

The project recording is in `video/project-demo.mp4`.