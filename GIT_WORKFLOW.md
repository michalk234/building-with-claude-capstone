# Git & GitHub Workflow Guide

This guide walks you through creating a GitHub repository for this project
and maintaining a daily commit habit throughout the training.

---

## Part 1 — One-time setup

### Step 1: Create a GitHub account

If you do not already have one:
1. Go to **https://github.com**
2. Click **Sign up** and follow the prompts
3. Verify your email address

---

### Step 2: Create a new repository on GitHub

1. Click the **+** icon (top-right) → **New repository**
2. Fill in:
   - **Repository name:** `loan-origination-assistant`
   - **Description:** `Apex Bank Loan Origination Assistant — Building with Claude`
   - **Visibility:** Private (recommended — this is your working repo)
   - **Do NOT** tick "Add a README" or ".gitignore" — you already have them
3. Click **Create repository**
4. Copy the URL shown on the next page, e.g.:
   ```
   https://github.com/your-username/loan-origination-assistant.git
   ```

---

### Step 3: Configure git on your machine (first time only)

Open a terminal and run:

```bash
git config --global user.name  "Your Name"
git config --global user.email "your.email@example.com"
```

Check it worked:
```bash
git config --global --list
```

---

### Step 4: Initialise your local repository

Navigate to the project folder you received from the instructor:

```bash
cd /path/to/loan-origination-assistant

# Initialise git
git init

# Tell git which files NOT to track (.gitignore is already provided)
# Verify .gitignore is present:
ls -a
```

---

### Step 5: Make your first commit

```bash
# Stage all files
git add .

# Verify what will be committed (check .env is NOT listed)
git status

# Create the first commit
git commit -m "Initial project structure"
```

---

### Step 6: Connect to GitHub and push

Replace `<your-username>` with your actual GitHub username:

```bash
git remote add origin https://github.com/<your-username>/loan-origination-assistant.git

git branch -M main

git push -u origin main
```

Go to `https://github.com/<your-username>/loan-origination-assistant` in your
browser — you should see the files.

---

## Part 2 — Daily workflow

At the end of each training day, follow these four steps.

### Step 1: Check what changed

```bash
git status
```

This shows untracked and modified files. Confirm `.env` is **not** listed.

---

### Step 2: Stage your changes

```bash
# Stage the main file (always)
git add loan_origination_assistant.py

# Stage any other files you edited today
git add README.md          # if you added notes
git add data/              # if you added new data files
```

Avoid `git add .` unless you are certain no secrets are included.

---

### Step 3: Commit with a meaningful message

Use this naming convention so your history is readable:

```
Day N / Phase N — <what you implemented>
```

Examples:
```bash
# End of Day 1
git commit -m "Day 1 / Phase 1 — make_client, system prompt, cost estimator"

# End of Day 2
git commit -m "Day 2 / Phase 2 — LoanApplicationRecord, ConversationManager, parse retry"

# End of Day 3
git commit -m "Day 3 / Phase 3 — tool definitions, agentic loop"

# Mid-day checkpoint (if you want to save progress)
git commit -m "Day 3 / Phase 3 WIP — tool definitions done, loop in progress"

# End of Day 4
git commit -m "Day 4 / Phase 4 — RAG index, policy retrieval, prompt caching"

# End of Day 4 (evaluation)
git commit -m "Day 4 / Phase 5 — faithfulness judge, eval loop, regression test"
```

---

### Step 4: Push to GitHub

```bash
git push
```

If you set up the upstream in Step 6 above (`-u origin main`), just `git push`
is enough from now on.

---

## Part 3 — Checking your history

View your commits in the terminal:

```bash
# One line per commit
git log --oneline

# With dates
git log --oneline --format="%h %ad %s" --date=short
```

Or visit `https://github.com/<your-username>/loan-origination-assistant/commits/main`
in your browser.

---

## Part 4 — Common problems and fixes

### Problem: `git push` asks for a password

GitHub no longer accepts passwords over HTTPS since August 2021. Use a
**Personal Access Token (PAT)** instead:

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click **Generate new token (classic)**
3. Set expiry to **90 days**, tick **repo** scope → Generate
4. Copy the token (starts with `ghp_...`)
5. When `git push` asks for a password, paste the token

To avoid typing it every time:
```bash
git config --global credential.helper store
```
Then push once — the token is saved locally.

---

### Problem: "Updates were rejected because the remote contains work not present locally"

This happens if you edited something directly on GitHub. Fix:

```bash
git pull --rebase origin main
git push
```

---

### Problem: You accidentally staged `.env`

```bash
# Unstage .env immediately — does NOT delete the file
git reset HEAD .env

# Double-check it is gone from staging
git status
```

If you already committed it (before pushing):
```bash
# Amend the last commit to remove .env
git rm --cached .env
git commit --amend -m "Remove .env accidentally staged"
```

If you already pushed it — rotate your API key immediately at
`https://console.anthropic.com` before doing anything else.

---

### Problem: You want to undo the last commit (not yet pushed)

```bash
# Keep your changes, just undo the commit
git reset --soft HEAD~1
```

---

## Part 5 — End-of-programme checklist

Before the programme closes:

- [ ] All 5 phases committed and pushed
- [ ] `git log --oneline` shows at least one commit per training day
- [ ] `.env` does **not** appear anywhere in `git log -p`
- [ ] `eval_logs/loan_assistant_v1.jsonl` is gitignored (not committed)
- [ ] `README.md` updated with your actual output from the final evaluation run
