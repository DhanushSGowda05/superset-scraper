import gspread


SPREADSHEET_ID = "1m57UwpVeweqhHDLHT0o9BgrMMzm0_R4NQybgHmSdJFY"
SHEET_NAME = "Superset Data"

HEADERS = [
    "Job ID",
    "Company",
    "Role",
    "Job Type",
    "Location",
    "Application Status",
    "Posted Date",
    "Category",
    "Job Function",
    "CTC",
    "CGPA",
    "Eligible",
]


# Connect to Google
gc = gspread.oauth(
    credentials_filename="credentials.json",
    authorized_user_filename="authorized_user.json"
)

spreadsheet = gc.open_by_key(SPREADSHEET_ID)


# ------------------------------------------------------------
# Delete existing Superset Data sheet
# ------------------------------------------------------------

try:
    old_sheet = spreadsheet.worksheet(SHEET_NAME)

    spreadsheet.del_worksheet(old_sheet)

    print(f"Deleted existing '{SHEET_NAME}' sheet.")

except gspread.WorksheetNotFound:
    print(f"'{SHEET_NAME}' did not exist.")


# ------------------------------------------------------------
# Create fresh sheet
# ------------------------------------------------------------

worksheet = spreadsheet.add_worksheet(
    title=SHEET_NAME,
    rows=1000,
    cols=len(HEADERS)
)


# ------------------------------------------------------------
# Add headers
# ------------------------------------------------------------

worksheet.update(
    range_name="A1",
    values=[HEADERS]
)


# Freeze header row
worksheet.freeze(rows=1)


print(f"Created new '{SHEET_NAME}' sheet.")

print("\nColumns:")

for header in HEADERS:
    print("-", header)

print("\nDone!")