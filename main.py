import os
import shutil
import re
import json
import subprocess
from pydriller import Repository

# ===== CONFIG =====
REPO_PATH = r"C:\repo\camel"
REPO_URL = "https://github.com/apache/camel.git"
ISSUE_IDS = ["CAMEL-180", "CAMEL-321", "CAMEL-1818", "CAMEL-3214", "CAMEL-18065"]
# ==================

# Step 1: Fix Windows long path issue
subprocess.run("git config --global core.longpaths true", shell=True)

# Step 2: Delete broken repo if exists
if os.path.exists(REPO_PATH):
    print("Deleting old/broken repo...")
    shutil.rmtree(REPO_PATH, ignore_errors=True)

# Step 3: Fresh clone
print("Cloning fresh repository...")
subprocess.run(f"git clone {REPO_URL} {REPO_PATH}", shell=True, check=True)

# Step 4: Regex for issues
escaped = [re.escape(i) for i in ISSUE_IDS]
issue_pattern = re.compile(
    r"(?<![A-Z0-9-])(" + "|".join(escaped) + r")(?![A-Z0-9-])",
    re.IGNORECASE
)

unique_commits = {}

print("Analyzing commits... (this will take time)")

for commit in Repository(REPO_PATH, only_no_merge=True).traverse_commits():

    message = commit.msg or ""
    matches = sorted({m.upper() for m in issue_pattern.findall(message)})

    if not matches:
        continue

    paths = set()

    for mf in commit.modified_files:
        if mf.change_type is None:
            continue

        if mf.change_type.name not in {"ADD", "MODIFY", "DELETE"}:
            continue

        path = mf.new_path or mf.old_path
        if path:
            paths.add(path)

    dmm_size = commit.dmm_unit_size or 0.0
    dmm_complexity = commit.dmm_unit_complexity or 0.0
    dmm_interface = commit.dmm_unit_interfacing or 0.0

    unique_commits[commit.hash] = {
        "files_changed": len(paths),
        "dmm_total": dmm_size + dmm_complexity + dmm_interface
    }

commits = list(unique_commits.values())
total = len(commits)

if total == 0:
    print("No commits found.")
else:
    avg_files = sum(c["files_changed"] for c in commits) / total
    avg_dmm = sum(c["dmm_total"] for c in commits) / total

    print("\n===== RESULTS =====")
    print(f"Total commits analysed: {total}")
    print(f"Average files changed: {round(avg_files, 4)}")
    print(f"Average DMM score: {round(avg_dmm, 4)}")