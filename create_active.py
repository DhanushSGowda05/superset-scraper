import gspread
from dotenv import load_dotenv
import os

load_dotenv()

# ============================================================
# CONFIG
# ============================================================

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

SOURCE_SHEET = "Superset Data"
TARGET_SHEET = "Active Applications"


# ============================================================
# CONNECT
# ============================================================

gc = gspread.oauth(
    credentials_filename="credentials.json",
    authorized_user_filename="authorized_user.json"
)

spreadsheet = gc.open_by_key(SPREADSHEET_ID)

source = spreadsheet.worksheet(SOURCE_SHEET)
target = spreadsheet.worksheet(TARGET_SHEET)


# ============================================================
# READ EXISTING ACTIVE APPLICATIONS
# ============================================================

existing_rows = target.get_all_records()

existing_job_ids = set()

for row in existing_rows:

    job_id = str(
        row.get("Job ID", "")
    ).strip()

    if job_id:
        existing_job_ids.add(job_id)


print(
    "Existing active applications:",
    len(existing_job_ids)
)


# ============================================================
# READ SUPERSET DATA
# ============================================================

source_rows = source.get_all_records()

print(
    "Jobs in Superset Data:",
    len(source_rows)
)


# ============================================================
# FIND NEW APPLIED JOBS
# ============================================================

new_applications = []

for job in source_rows:

    # --------------------------------------------------------
    # Only jobs that are Applied
    # --------------------------------------------------------

    if str(
        job.get("Application Status", "")
    ).strip() != "Applied":

        continue

    # --------------------------------------------------------
    # Job ID
    # --------------------------------------------------------

    job_id = str(
        job.get("Job ID", "")
    ).strip()

    if not job_id:
        continue

    # --------------------------------------------------------
    # Already exists?
    # --------------------------------------------------------

    if job_id in existing_job_ids:
        continue

    # --------------------------------------------------------
    # New application
    # --------------------------------------------------------

    new_applications.append([
        job_id,
        job.get("Company", ""),
        job.get("Role", ""),
        job.get("Job Type", ""),
        job.get("Location", ""),
        job.get("CGPA", ""),
        job.get("Eligible", ""),
        "Pending",
    ])

    # Prevent duplicate addition within this run
    existing_job_ids.add(job_id)


# ============================================================
# ADD NEW APPLICATIONS
# ============================================================

if new_applications:

    # Find first empty row
    existing_values = target.get_all_values()

    start_row = len(existing_values) + 1

    end_row = (
        start_row
        + len(new_applications)
        - 1
    )

    target.update(
        range_name=f"A{start_row}:H{end_row}",
        values=new_applications
    )

    print(
        "New applications added:",
        len(new_applications)
    )

else:

    print(
        "New applications added: 0"
    )


# ============================================================
# ENSURE DROPDOWN EXISTS FOR NEW ROWS
# ============================================================

if new_applications:

    start_row = len(existing_rows) + 2

    end_row = (
        start_row
        + len(new_applications)
        - 1
    )

    requests = [
        {
            "setDataValidation": {
                "range": {
                    "sheetId": target.id,
                    "startRowIndex": start_row - 1,
                    "endRowIndex": end_row,
                    "startColumnIndex": 7,
                    "endColumnIndex": 8,
                },
                "rule": {
                    "condition": {
                        "type": "ONE_OF_LIST",
                        "values": [
                            {
                                "userEnteredValue": "Pending"
                            },
                            {
                                "userEnteredValue": "Yes"
                            },
                            {
                                "userEnteredValue": "No"
                            },
                        ],
                    },
                    "showCustomUi": True,
                    "strict": True,
                },
            }
        }
    ]

    spreadsheet.batch_update(
        {
            "requests": requests
        }
    )


# ============================================================
# SUMMARY
# ============================================================

print("\n==============================")
print("ACTIVE APPLICATIONS UPDATED")
print("==============================")

print(
    "Total applications:",
    len(target.get_all_records())
)

print(
    "Existing Got Offer values were preserved."
)

print("\nDone!")