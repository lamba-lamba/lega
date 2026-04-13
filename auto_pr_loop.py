import subprocess
import time
import sys
import shutil

# --- CONFIG ---
FILENAME = "numbers.txt"
BASE_BRANCH = "main"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 5
WAIT_SECONDS = 0
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


def ensure_tool_exists(tool_name):
    if shutil.which(tool_name) is None:
        raise RuntimeError(f"Required tool not found: {tool_name}")


def ensure_git_repo():
    result = run("git rev-parse --is-inside-work-tree")
    if result.stdout.strip() != "true":
        raise RuntimeError("Current directory is not a git repository.")


def ensure_clean_working_tree():
    result = run("git status --porcelain")
    if result.stdout.strip():
        raise RuntimeError(
            "Working tree is not clean. Commit/stash your changes first.\n"
            "Tip: run `git stash` and try again."
        )


def branch_exists_local(branch):
    result = run(f"git branch --list {branch}", check=False)
    return bool(result.stdout.strip())


def branch_exists_remote(branch):
    result = run(f"git ls-remote --heads origin {branch}", check=False)
    return bool(result.stdout.strip())


def delete_local_branch_if_exists(branch):
    if branch_exists_local(branch):
        run(f"git branch -D {branch}")


def delete_remote_branch_if_exists(branch):
    if branch_exists_remote(branch):
        run(f"git push origin --delete {branch}", check=False)


def ensure_file_exists(filename):
    try:
        with open(filename, "a"):
            pass
    except Exception as e:
        raise RuntimeError(f"Could not access file {filename}: {e}")


def main():
    ensure_tool_exists("git")
    ensure_tool_exists("gh")
    ensure_git_repo()
    ensure_clean_working_tree()
    ensure_file_exists(FILENAME)

    for i in range(1, N + 1):
        print(f"\n{'=' * 40}")
        print(f"  Iteration {i} of {N}")
        print(f"{'=' * 40}")

        branch = f"auto-pr-{i}"

        # 1. Switch to base branch and sync it safely
        run(f"git checkout {BASE_BRANCH}")
        run(f"git branch --unset-upstream", check=False)
        run(f"git fetch origin")
        run(f"git branch --set-upstream-to=origin/{BASE_BRANCH} {BASE_BRANCH}", check=False)
        run(f"git pull --rebase origin {BASE_BRANCH}")

        # 2. Remove stale branch if it exists
        delete_local_branch_if_exists(branch)
        delete_remote_branch_if_exists(branch)

        # 3. Create new branch
        run(f"git checkout -b {branch}")

        # 4. Append number to file
        with open(FILENAME, "a", encoding="utf-8") as f:
            f.write(f"{i}\n")
        print(f"  Appended {i} to {FILENAME}")

        # 5. Commit and push
        run(f"git add {FILENAME}")
        commit_result = run(f'git commit -m "Add number {i}"', check=False)

        if commit_result.returncode != 0:
            raise RuntimeError(
                f"No commit created in iteration {i}. "
                f"Check whether {FILENAME} actually changed."
            )

        run(f"git push -u origin {branch}")

        # 6. Create PR and capture URL
        pr_result = run(
            f'gh pr create --title "Auto PR #{i}" '
            f'--body "Adds number {i} to {FILENAME}" '
            f'--base {BASE_BRANCH} --head {branch}'
        )
        pr_url = pr_result.stdout.strip().splitlines()[-1].strip()

        # 7. Merge PR
        run(f'gh pr merge "{pr_url}" --merge --delete-branch')

        print(f"  ✅ PR #{i} created and merged.")

        # 8. Sync local main after merge
        run(f"git checkout {BASE_BRANCH}")
        run(f"git pull --rebase origin {BASE_BRANCH}")

        if i < N:
            print(f"  ⏳ Waiting {WAIT_SECONDS} seconds...")
            time.sleep(WAIT_SECONDS)

    print(f"\n🎉 Done! Created and merged {N} pull requests.")


if __name__ == "__main__":
    main()