import subprocess
import sys


print("\n==============================")
print("STEP 1: SCRAPING SUPERSET")
print("==============================")

result = subprocess.run(
    [sys.executable, "scraper.py"]
)

# If scraper failed, don't update Active Applications
if result.returncode != 0:

    print("\nSuperset scraper failed.")
    print("Active Applications was NOT updated.")

    sys.exit(result.returncode)


print("\n==============================")
print("STEP 2: UPDATING APPLICATIONS")
print("==============================")

result = subprocess.run(
    [sys.executable, "create_active.py"]
)

if result.returncode != 0:

    print("\nActive Applications update failed.")

    sys.exit(result.returncode)


print("\n==============================")
print("ALL DONE")
print("==============================")