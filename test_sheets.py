import gspread
from playwright.sync_api import sync_playwright


# ============================================================
# CONFIG
# ============================================================

SPREADSHEET_ID = "1m57UwpVeweqhHDLHT0o9BgrMMzm0_R4NQybgHmSdJFY"
SHEET_NAME = "Superset Data"

HEADERS = [
    "Company",
    "Role",
    "Job Type",
    "Location",
    "Application Status",
    "Posted Date",
    "Category",
    "Job Function",
    "CTC",
    "Eligibility",
]


# ============================================================
# ELIGIBILITY CLEANING
# ============================================================

def clean_eligibility(text):

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    useful = []

    for line in lines:

        # Remove heading
        if line == "Eligibility Criteria":
            continue

        # Remove evaluation date
        if line.startswith("Evaluated on"):
            continue

        # Remove Superset account-specific offer information
        if "offers allowed" in line:
            continue

        if "attempts allowed" in line:
            continue

        if "currently has" in line:
            continue

        if "completed" in line and "attempt" in line:
            continue

        # Remove personal actual marks
        if "Actual:" in line:
            line = line.split("Actual:")[0].strip()
            line = line.rstrip("-").strip()

        useful.append(line)

    return "\n".join(useful)


# ============================================================
# SCRAPE ONE JOB
# ============================================================

def extract_job(page, card):

    # Click job
    card.click()

    page.wait_for_timeout(1000)

    # --------------------------------------------------------
    # Header
    # --------------------------------------------------------

    role = page.locator(
        "div.MuiContainer-root p.text-base.font-bold.text-dark"
    ).first.inner_text().strip()

    header = page.locator(
        "div.MuiContainer-root div.text-xs.text-dark.font-bold"
    ).first

    header_text = header.inner_text()

    parts = [
        part.strip()
        for part in header_text.split("|")
    ]

    company = parts[0] if len(parts) > 0 else ""
    job_type = parts[1] if len(parts) > 1 else ""
    location = parts[2] if len(parts) > 2 else ""

    # --------------------------------------------------------
    # Application Status
    # --------------------------------------------------------

    status = ""

    status_badges = page.locator(
        "div.MuiContainer-root span"
    )

    for i in range(status_badges.count()):

        text = status_badges.nth(i).inner_text().strip()

        if text in [
            "Applied",
            "Yet to apply",
            "Applications closed"
        ]:
            status = text
            break

    # --------------------------------------------------------
    # Posted Date
    # --------------------------------------------------------

    posted = ""

    posted_element = card.locator(
        "p.text-xs.text-zinc-400"
    )

    if posted_element.count() > 0:
        posted = posted_element.first.inner_text().strip()

    # --------------------------------------------------------
    # Opening Overview
    # --------------------------------------------------------

    category = ""
    job_function = ""
    ctc = ""

    rows = page.locator("table tr")

    for i in range(rows.count()):

        row = rows.nth(i)

        cells = row.locator("td")

        if cells.count() < 2:
            continue

        label = cells.nth(0).inner_text().strip()
        value = cells.nth(1).inner_text().strip()

        if "Category:" in label:
            category = value

        elif "Job Functions:" in label:
            job_function = value

        elif "Job Profile CTC:" in label:
            ctc = value

    # --------------------------------------------------------
    # Eligibility
    # --------------------------------------------------------

    page.get_by_role(
        "tab",
        name="Eligibility Criteria"
    ).click()

    page.wait_for_timeout(500)

    eligibility_panel = page.locator(
        '[role="tabpanel"]'
    ).filter(
        has_text="Eligibility Criteria"
    ).first

    raw_eligibility = eligibility_panel.inner_text()

    eligibility = clean_eligibility(
        raw_eligibility
    )

    # --------------------------------------------------------
    # Return dictionary
    # --------------------------------------------------------

    return {
        "Company": company,
        "Role": role,
        "Job Type": job_type,
        "Location": location,
        "Application Status": status,
        "Posted Date": posted,
        "Category": category,
        "Job Function": job_function,
        "CTC": ctc,
        "Eligibility": eligibility,
    }


# ============================================================
# GOOGLE SHEETS
# ============================================================

def get_sheet():

    gc = gspread.oauth(
        credentials_filename="credentials.json",
        authorized_user_filename="authorized_user.json"
    )

    spreadsheet = gc.open_by_key(
        SPREADSHEET_ID
    )

    try:

        worksheet = spreadsheet.worksheet(
            SHEET_NAME
        )

    except gspread.WorksheetNotFound:

        worksheet = spreadsheet.add_worksheet(
            title=SHEET_NAME,
            rows=1000,
            cols=len(HEADERS)
        )

    return worksheet


def setup_headers(worksheet):

    existing_headers = worksheet.row_values(1)

    if existing_headers != HEADERS:

        worksheet.update(
            "A1",
            [HEADERS]
        )


# ============================================================
# MAIN
# ============================================================

with sync_playwright() as p:

    # --------------------------------------------------------
    # Google Sheets
    # --------------------------------------------------------

    worksheet = get_sheet()

    setup_headers(worksheet)

    print("Google Sheet ready.")

    # --------------------------------------------------------
    # Superset
    # --------------------------------------------------------

    context = p.chromium.launch_persistent_context(
        user_data_dir="./browser_data",
        headless=False
    )

    page = (
        context.pages[0]
        if context.pages
        else context.new_page()
    )

    page.goto(
        "https://app.joinsuperset.com/students/jobprofiles"
    )

    page.wait_for_timeout(5000)

    # --------------------------------------------------------
    # Find jobs
    # --------------------------------------------------------

    cards = page.locator(
        'div.cursor-pointer:has(div.p-4)'
    )

    print(
        "Jobs found:",
        cards.count()
    )

    # --------------------------------------------------------
    # TEST ONLY: first job
    # --------------------------------------------------------

    data = extract_job(
        page,
        cards.nth(0)
    )

    print("\n==============================")
    print("SCRAPED JOB")
    print("==============================")

    for key, value in data.items():

        print(f"\n{key}:")
        print(value)

    # --------------------------------------------------------
    # Write ONE job to Google Sheets
    # --------------------------------------------------------

    row = [
        data["Company"],
        data["Role"],
        data["Job Type"],
        data["Location"],
        data["Application Status"],
        data["Posted Date"],
        data["Category"],
        data["Job Function"],
        data["CTC"],
        data["Eligibility"],
    ]

    worksheet.append_row(
        row,
        value_input_option="USER_ENTERED"
    )

    print("\n==============================")
    print("SUCCESS")
    print("==============================")

    print(
        "Added job to:",
        SHEET_NAME
    )

    input("\nPress ENTER to close...")

    context.close()