JOB_TYPES = ["Full-time", "Part-time", "Contract", "Internship"]
STATUSES = ["Applied", "Screening", "Interview", "Offer", "Rejected", "Withdrawn"]

TABLES = {
    "companies": {
        "name": "Company",
        "pk": "company_id",
        "fields": ["company_name", "industry", "website", "city", "state", "notes"],
        "columns": ["company_name", "industry", "city", "state"],
        "sql": "SELECT t.* FROM companies t",
    },
    "jobs": {
        "name": "Job",
        "pk": "job_id",
        "fields": ["company_id", "job_title", "job_type", "salary_min", "salary_max",
                   "job_url", "date_posted", "requirements"],
        "columns": ["job_title", "company_name", "job_type", "date_posted"],
        "sql": """SELECT t.*, c.company_name FROM jobs t
                  JOIN companies c ON c.company_id = t.company_id""",
    },
    "applications": {
        "name": "Application",
        "pk": "application_id",
        "fields": ["job_id", "application_date", "status", "resume_version",
                   "cover_letter_sent", "interview_data"],
        "columns": ["job_title", "company_name", "application_date", "status"],
        "sql": """SELECT t.*, j.job_title, c.company_name FROM applications t
                  JOIN jobs j ON j.job_id = t.job_id
                  JOIN companies c ON c.company_id = j.company_id""",
    },
    "contacts": {
        "name": "Contact",
        "pk": "contact_id",
        "fields": ["company_id", "contact_name", "title", "email", "phone",
                   "linkedin_url", "notes"],
        "columns": ["contact_name", "company_name", "title", "email"],
        "sql": """SELECT t.*, c.company_name FROM contacts t
                  JOIN companies c ON c.company_id = t.company_id""",
    },
}

REQUIRED = {
    "company_name", "company_id", "job_title", "job_type",
    "job_id", "application_date", "status", "contact_name",
}

INPUT_TYPES = {
    "salary_min": "number", "salary_max": "number",
    "application_date": "date", "date_posted": "date",
    "email": "email", "website": "url", "job_url": "url", "linkedin_url": "url",
}

LIMITS = {
    "company_name": 100, "industry": 50, "website": 200, "city": 50, "state": 50,
    "job_title": 100, "job_url": 300, "resume_version": 50, "contact_name": 100,
    "title": 100, "email": 100, "phone": 20, "linkedin_url": 200,
}

LABELS = {
    "company_id": "Company", "company_name": "Company name", "job_id": "Job",
    "requirements": "Required skills", "interview_data": "Interview details (JSON)",
    "salary_min": "Minimum salary", "salary_max": "Maximum salary",
    "job_url": "Job URL", "linkedin_url": "LinkedIn URL",
}