# Daily Development Workflow — EsteemCBT

## Branch Strategy

Maintain these branches at all times:

* `development` → Active development. Does not deploy anywhere — just your working branch and GitHub backup.
* `staging` → Reviewed features ready for testing. Deploys automatically to `https://staging.esteemlearningcenter.com`.
* `main` → Production branch. Deploys automatically to `https://esteemlearningcenter.com`.

---

# Daily Development Process

## Step 1 — Start from `development`

Always begin new work on the `development` branch.

```bash
git branch
git checkout development
git pull origin development
```

---

## Step 2 — Develop

* Implement your changes.
* Test locally.
* Ensure there are no obvious errors before committing.

---

## Step 3 — Push to `development`

```bash
git add .
git commit -m "feat: describe what you changed"
git push origin development
```

This only backs up your work to GitHub. It does not deploy anywhere yet.

---

## Step 4 — Merge to `staging` and test

```bash
git checkout staging
git pull origin staging
git merge development
git push origin staging
```

After deployment:

* Wait for the deployment notification.
* Open `https://staging.esteemlearningcenter.com`.
* Test the new feature thoroughly.
* Verify existing functionality still works.

Only proceed to production if staging passes all tests.

---

## Step 5 — Tag current production before touching it

**Always do this before merging anything into `main`** — it's your rollback point if the new deployment fails.

```bash
git checkout main
git pull origin main
git tag v1.x-stable
git push origin v1.x-stable
```

Increment the version each time (`v1.1-stable`, `v1.2-stable`, etc.) so you can always identify and return to a specific past release.

---

## Step 6 — Deploy to Production

Merge tested and reviewed code from `staging` into `main`.

```bash
git merge staging
git push origin main
```

Wait for deployment to complete, then verify production:

* Visit `esteemlearningcenter.com`.
* Test the newly deployed feature.
* Confirm no regressions exist.

If everything works, you're done — the tag from Step 5 stays as your safety net for next time.

---

# Rollback Procedure

If a production deployment fails — or you need to return to any earlier confirmed-stable release — reset `main` to the relevant tag:

```bash
git checkout main
git reset --hard v1.x-stable
git push origin main --force
```

Replace `v1.x-stable` with the specific tag you need (e.g. the tag from Step 5 for the most recent rollback, or an older tag like `v1.0-stable` for a historical release).

Or trigger the rollback workflow manually from GitHub Actions:

---

# Commit Message Convention

Use clear commit prefixes:

```text
feat: add new exam timer feature
fix: resolve quiz not saving issue
style: update dashboard colors
refactor: clean up student views
hotfix: critical exam submission bug
```

---

# Weekly Maintenance

Sync staging database with production to keep testing realistic.

```bash
# On the server
pg_dump -U esteemcbt_user -h localhost -p 5433 esteemcbt > /tmp/prod_dump.sql

sudo -u postgres psql -p 5433 -c "DROP DATABASE esteemcbt_staging;"
sudo -u postgres psql -p 5433 -c "CREATE DATABASE esteemcbt_staging OWNER esteemcbt_user;"
sudo -u postgres psql -p 5433 esteemcbt_staging < /tmp/prod_dump.sql
```

---

# Rules

* Always develop on `development` — never deploy from it directly.
* Never push directly to `main` without testing on staging first.
* Test every feature on `https://staging.esteemlearningcenter.com` before merging to `main`.
* Always tag the current `main` **before** merging new code into it.
* Verify production immediately after every deployment.
* Use stable tags for rollback whenever something breaks.

# Update `.env` in Production

### 1. SSH into the server

```bash
ssh root@204.168.237.20
MyServer2026!Coolify
cd /var/www/esteemcbt
source env/bin/activate
cat .env
```
### 4. Update the GitHub secret

- Go to **GitHub** → **Settings** → **Secrets and variables**
- Select the secret/variable to update
- Save the changes

### 5. Trigger deployment
Run on your local machine:
```bash
git commit --allow-empty -m "Update OpenAI API key"
git push origin esteemcbt
```
systemctl restart esteemcbt

# Update `.env` in Production

### 1. SSH into the server

```bash
ssh root@204.168.237.20
MyServer2026!Coolify
cd /var/www/esteemcbt
source env/bin/activate
cat .env
```
### 4. Update the GitHub secret

- Go to **GitHub** → **Settings** → **Secrets and variables**
- Select the secret/variable to update
- Save the changes

### 5. Trigger deployment
Run on your local machine:
```bash
git commit --allow-empty -m "Update OpenAI API key"
git push origin main
```
```bash
git pull origin staging
git push origin staging
```


systemctl restart esteemcbt