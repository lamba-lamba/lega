import subprocess
import time
import sys

# --- CONFIG ---
FILENAME = "numbers.txt"
BASE_BRANCH = "master"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 5  # pass N as argument, default 5
WAIT_SECONDS = 2
# --------------

def run(cmd, check=True):
    print(f"  $ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip())
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}")
    return result

for i in range(1, N + 1):
    print(f"\n{'='*40}")
    print(f"  Iteration {i} of {N}")
    print(f"{'='*40}")

    branch = f"auto-pr-{i}"

    # 1. Make sure we're on base branch and up to date
    run(f"git checkout {BASE_BRANCH}")
    run(f"git pull origin {BASE_BRANCH}")

    # 2. Create a new branch
    run(f"git checkout -b {branch}")

    # 3. Append number to file
    with open(FILENAME, "a") as f:
        f.write(f"{i}\n")
    print(f"  Appended {i} to {FILENAME}")

    # 4. Commit and push
    run(f"git add {FILENAME}")
    run(f'git commit -m "Add number {i}"')
    run(f"git push origin {branch}")

    # 5. Create PR using GitHub CLI
    run(f'gh pr create --title "Auto PR #{i}" --body "Adds number {i} to {FILENAME}" --base {BASE_BRANCH} --head {branch}')

    # 6. Merge the PR
    run(f"gh pr merge {branch} --merge --delete-branch")

    print(f"  ✅ PR #{i} created and merged.")

    # 7. Wait before next iteration
    if i < N:
        print(f"  ⏳ Waiting {WAIT_SECONDS} seconds...")
        time.sleep(WAIT_SECONDS)

print(f"\n🎉 Done! Created and merged {N} pull requests.")
