import gspread
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from dotenv import load_dotenv
import os

load_dotenv()

# ============================================================
# CONFIG
# ============================================================

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SHEET_NAME = "Superset Data"
SUPERSET_URL = os.getenv("SUPERSET_URL")

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


# ============================================================
# EXTRACT ELIGIBILITY
# ============================================================

def extract_eligibility(page):

    try:

        page.get_by_role(
            "tab",
            name="Eligibility Criteria"
        ).click()

        page.wait_for_timeout(400)

        panel = page.locator(
            '[role="tabpanel"]'
        ).filter(
            has_text="Eligibility Criteria"
        ).first

        text = panel.inner_text()

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        # ----------------------------------------------------
        # CGPA
        # ----------------------------------------------------

        cgpa = ""

        for i, line in enumerate(lines):

            if line.startswith("UG -"):

                if i + 1 < len(lines):

                    required_line = lines[i + 1]

                    if "Required:" in required_line:

                        required = required_line.split(
                            "Required:",
                            1
                        )[1]

                        if "Actual:" in required:

                            required = required.split(
                                "Actual:",
                                1
                            )[0]

                        cgpa = required.strip().rstrip(",")

                break

        # ----------------------------------------------------
        # ELIGIBLE
        # ----------------------------------------------------

        eligible = "Unknown"

        if "Criteria satisfied" in text:
            eligible = "Yes"

        failure_words = [
            "Criteria not satisfied",
            "Not eligible",
            "Failed",
            "does not satisfy",
            "not satisfied"
        ]

        for word in failure_words:

            if word.lower() in text.lower():

                eligible = "No"
                break

        return cgpa, eligible

    except Exception as e:

        print(
            "Warning: Could not extract eligibility:",
            e
        )

        return "", "Unknown"


# ============================================================
# EXTRACT ONE JOB
# ============================================================

def extract_job(page, card):

    # --------------------------------------------------------
    # Click job
    # --------------------------------------------------------

    card.click()

    page.wait_for_timeout(800)

    # --------------------------------------------------------
    # JOB ID
    # --------------------------------------------------------

    job_id = ""

    current_url = page.url

    if "currentJobId=" in current_url:

        job_id = current_url.split(
            "currentJobId=",
            1
        )[1].split(
            "&",
            1
        )[0]

    # --------------------------------------------------------
    # ROLE
    # --------------------------------------------------------

    role = page.locator(
        "div.MuiContainer-root p.text-base.font-bold.text-dark"
    ).first.inner_text().strip()

    # --------------------------------------------------------
    # COMPANY / JOB TYPE / LOCATION
    # --------------------------------------------------------

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
    # APPLICATION STATUS
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
    # POSTED DATE
    # --------------------------------------------------------

    posted = ""

    posted_element = card.locator(
        "p.text-xs.text-zinc-400"
    )

    if posted_element.count() > 0:

        posted = posted_element.first.inner_text().strip()

    # --------------------------------------------------------
    # OPENING OVERVIEW
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
    # ELIGIBILITY
    # --------------------------------------------------------

    cgpa, eligible = extract_eligibility(page)

    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {
        "Job ID": job_id,
        "Company": company,
        "Role": role,
        "Job Type": job_type,
        "Location": location,
        "Application Status": status,
        "Posted Date": posted,
        "Category": category,
        "Job Function": job_function,
        "CTC": ctc,
        "CGPA": cgpa,
        "Eligible": eligible
    }


# ============================================================
# GOOGLE SHEETS
# ============================================================

def get_worksheet():

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


# ============================================================
# SETUP SHEET
# ============================================================

def setup_sheet(worksheet):

    existing_headers = worksheet.row_values(1)

    if existing_headers != HEADERS:

        worksheet.update(
            range_name="A1",
            values=[HEADERS]
        )

        print("Headers updated.")


# ============================================================
# GET LAST JOB FROM SHEET
# ============================================================

def get_last_processed_job(worksheet):

    values = worksheet.get_all_values()

    if len(values) <= 1:
        return None

    # LAST DATA ROW
    last_job = values[-1]

    if len(last_job) >= 1:

        job_id = last_job[0].strip()

        if job_id:
            return job_id

    return None


# ============================================================
# CHECKPOINT
# ============================================================

def is_checkpoint(data, checkpoint):

    if checkpoint is None:
        return False

    return data["Job ID"] == checkpoint


# ============================================================
# INSERT JOB AT BOTTOM
# ============================================================

def insert_jobs(worksheet, jobs):

    if not jobs:
        return

    rows = []

    for data in jobs:

        rows.append([
            data["Job ID"],
            data["Company"],
            data["Role"],
            data["Job Type"],
            data["Location"],
            data["Application Status"],
            data["Posted Date"],
            data["Category"],
            data["Job Function"],
            data["CTC"],
            data["CGPA"],
            data["Eligible"]
        ])

    # Append all jobs together.
    worksheet.append_rows(
        rows,
        value_input_option="USER_ENTERED"
    )


# ============================================================
# MAIN
# ============================================================

with sync_playwright() as p:

    # --------------------------------------------------------
    # GOOGLE SHEETS
    # --------------------------------------------------------

    worksheet = get_worksheet()

    setup_sheet(worksheet)

    checkpoint = get_last_processed_job(
        worksheet
    )

    print("\n==============================")
    print("GOOGLE SHEETS")
    print("==============================")

    if checkpoint:

        print(
            "Last processed Job ID:",
            checkpoint
        )

    else:

        print(
            "No previous checkpoint."
        )

    # --------------------------------------------------------
    # BROWSER
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

    # --------------------------------------------------------
    # OPEN SUPERSET
    # --------------------------------------------------------

    print("\nOpening Superset...")

    page.goto(
        SUPERSET_URL,
        wait_until="domcontentloaded"
    )

    cards = page.locator(
        'div.cursor-pointer:has(div.p-4)'
    )

    print(
        "Waiting for jobs to load..."
    )

    try:

        cards.first.wait_for(
            state="visible",
            timeout=30000
        )

    except PlaywrightTimeoutError:

        print(
            "\nERROR: Job cards did not load."
        )

        print(
            "Current URL:",
            page.url
        )

        print(
            "Page title:",
            page.title()
        )

        input(
            "\nPress ENTER to close..."
        )

        context.close()

        raise SystemExit

    page.wait_for_timeout(1000)

    total_jobs = cards.count()

    print("\n==============================")
    print("SUPERSET")
    print("==============================")

    print(
        "Jobs available:",
        total_jobs
    )

    if total_jobs == 0:

        print(
            "\nERROR: Superset loaded 0 jobs."
        )

        print(
            "No data will be written."
        )

        input(
            "\nPress ENTER to close..."
        )

        context.close()

        raise SystemExit

    # --------------------------------------------------------
    # PROCESS JOBS
    # --------------------------------------------------------

    new_jobs = []

    for i in range(total_jobs):

        print("\n------------------------------")

        print(
            f"Checking job {i + 1}/{total_jobs}"
        )

        print("------------------------------")

        card = cards.nth(i)

        try:

            data = extract_job(
                page,
                card
            )

        except Exception as e:

            print(
                "ERROR extracting job:"
            )

            print(e)

            print(
                "Skipping..."
            )

            continue

        print(
            data["Company"],
            "|",
            data["Role"]
        )

        print(
            "Job ID:",
            data["Job ID"]
        )

        # ----------------------------------------------------
        # CHECKPOINT
        # ----------------------------------------------------

        if is_checkpoint(
            data,
            checkpoint
        ):

            print(
                "\nReached last processed job."
            )

            print(
                "Stopping scraper."
            )

            break

        # ----------------------------------------------------
        # STORE NEW JOB IN MEMORY
        # ----------------------------------------------------

        new_jobs.append(data)

        print(
            "NEW JOB → Stored temporarily"
        )

    # --------------------------------------------------------
    # APPEND NEW JOBS
    # --------------------------------------------------------

    if new_jobs:

        print("\n==============================")

        print(
            "ADDING NEW JOBS"
        )

        print("==============================")

        # Superset = newest → oldest
        #
        # Reverse it so Google Sheet becomes:
        # oldest → newest
        #
        # Example:
        #
        # Superset:
        # A newest
        # B
        # C oldest
        #
        # Reverse:
        # C
        # B
        # A newest

        new_jobs.reverse()

        insert_jobs(
            worksheet,
            new_jobs
        )

        print(
            "Added",
            len(new_jobs),
            "new jobs to Google Sheet."
        )

    else:

        print(
            "\nNo new jobs found."
        )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print("\n==============================")
    print("SCRAPING COMPLETE")
    print("==============================")

    print(
        "New jobs added:",
        len(new_jobs)
    )

    input(
        "\nPress ENTER to close..."
    )

    context.close()