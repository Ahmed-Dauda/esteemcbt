# Daily Development Workflow

## Branch Strategy

Maintain these branches at all times:

* `staging` → Testing environment
* `development` → Production deployment branch
* `main-working` → Last confirmed stable backup

---

# Daily Development Process

## Step 1 — Start from `staging`

Always begin new work on the `staging` branch.

```bash
git checkout staging
git pull origin staging
```

---

## Step 2 — Develop

* Implement your changes.
* Test locally.
* Ensure there are no obvious errors before committing.

---

## Step 3 — Push to `staging`

```bash
git add .
git commit -m "feat: describe what you changed"
git push origin staging
```

After deployment:

* Wait for the deployment notification.
* Open `staging.esteemlearningcenter.com`.
* Test the new feature thoroughly.
* Verify existing functionality still works.

Only proceed if staging passes all tests.

---

## Step 4 — Deploy to Production

Merge the tested code into `development`.

```bash
git checkout development
git pull origin development
git merge staging
git push origin development
```

Wait for deployment to complete.

Then verify production:

* Visit `esteemlearningcenter.com`
* Test the newly deployed feature.
* Confirm no regressions exist.

---

## Step 5 — Update Stable Backup

**Only perform this step after confirming production is working correctly.**

At this point, save the deployed version as the latest stable backup.

```bash
git checkout main-working
git pull origin main-working
git merge development
git push origin main-working

git tag v1.x-stable
git push origin v1.x-stable
```

This ensures `main-working` always represents the latest confirmed working release.

---

# Rollback Procedure

If a production deployment fails **before updating `main-working`**, simply redeploy the current `main-working` branch.

```bash
git checkout main-working
git push origin main-working --force
```

Because `main-working` was not updated yet, it still contains the previous stable release.

---

# Rollback to an Older Stable Version

If you need to return to a specific historical release:

```bash
git checkout main-working
git reset --hard v1.0-stable
git push origin main-working --force
```

This restores production to the tagged stable version.

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

Sync staging with production data to keep testing realistic.

```bash
# On the server

pg_dump -U esteemcbt_user -h localhost -p 5433 esteemcbt > /tmp/prod_dump.sql

sudo -u postgres psql -p 5433 esteemcbt_staging < /tmp/prod_dump.sql
```

---

# Rules

* Always develop on `staging`.
* Never push directly to `development` without testing.
* Test every feature on staging before merging.
* Verify production after deployment.
* Only update `main-working` after production has been confirmed healthy.
* Tag every stable production release.
* Use `main-working` or a stable tag for rollback when necessary.
