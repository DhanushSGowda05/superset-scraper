from playwright.sync_api import sync_playwright


def clean_eligibility(text):
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    useful = []

    for line in lines:

        # Remove the heading
        if line == "Eligibility Criteria":
            continue

        # Remove evaluation timestamp
        if line.startswith("Evaluated on"):
            continue

        # Remove placement/offer attempt rules
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

            # Remove trailing "-"
            line = line.rstrip("-").strip()

        useful.append(line)

    return "\n".join(useful)


def extract_job(page, card):

    # --------------------------------
    # Click job
    # --------------------------------

    card.click()

    page.wait_for_timeout(1000)

    # --------------------------------
    # Header
    # --------------------------------

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

    # --------------------------------
    # Application Status
    # --------------------------------

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

    # --------------------------------
    # Posted Date
    # --------------------------------

    posted = ""

    posted_element = card.locator(
        "p.text-xs.text-zinc-400"
    )

    if posted_element.count() > 0:
        posted = posted_element.first.inner_text().strip()

    # --------------------------------
    # Opening Overview
    # --------------------------------

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

    # --------------------------------
    # Eligibility
    # --------------------------------

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

    # --------------------------------
    # Return
    # --------------------------------

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


# ==========================================
# TEST
# ==========================================

with sync_playwright() as p:

    context = p.chromium.launch_persistent_context(
        user_data_dir="./browser_data",
        headless=False
    )

    page = context.pages[0] if context.pages else context.new_page()

    page.goto(
        "https://app.joinsuperset.com/students/jobprofiles"
    )

    page.wait_for_timeout(5000)

    cards = page.locator(
        'div.cursor-pointer:has(div.p-4)'
    )

    print("Jobs found:", cards.count())

    # Test first job
    data = extract_job(
        page,
        cards.nth(0)
    )

    print("\n==============================")
    print("EXTRACTED JOB")
    print("==============================")

    for key, value in data.items():

        print(f"\n{key}:")
        print(value)

    input("\nPress ENTER to close...")

    context.close()