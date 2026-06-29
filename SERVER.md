# DEPLOYMENT QUICK REFERENCE
# ===========================


# 1. SSH INTO SERVER
ssh root@204.168.237.20
MyServer2026!Coolify

# ===========================
# 2. STAGING ENVIRONMENT
# ===========================

# NAVIGATE TO STAGING PROJECT
MyServer2026!Coolify
cd /var/www/esteemcbt-staging
source venv/bin/activate

# RESTART STAGING SERVICES (if applicable)
systemctl restart esteemcbt-staging
systemctl restart celery-staging

# CHECK STAGING SERVICE STATUS
systemctl status esteemcbt-staging
systemctl status celery-staging

# CHECK STAGING LOGS
journalctl -u esteemcbt-staging -n 20 --no-pager


# ===========================
# 3. PRODUCTION ENVIRONMENT
# ===========================

# NAVIGATE TO PRODUCTION PROJECT
cd /var/www/esteemcbt
source venv/bin/activate
MyServer2026!Coolify

# RESTART PRODUCTION SERVICES
systemctl restart esteemcbt
systemctl restart celery

# CHECK PRODUCTION SERVICE STATUS
systemctl status esteemcbt
systemctl status celery

# CHECK PRODUCTION LOGS
journalctl -u esteemcbt -n 20 --no-pager


# ===========================
# 4. CORE INFRASTRUCTURE CHECK
# ===========================

systemctl status redis
systemctl status nginx


# ===========================
# 5. FILE SYNC (SERVER → LOCAL)
# ===========================

scp root@204.168.237.20:/var/www/esteemcbt/quiz/tasks.py ./quiz/tasks.py
scp root@204.168.237.20:/var/www/esteemcbt/school/settings.py ./school/settings.py


# IF AI QUESTIONS ARE NOT GENERATING

# Fix: Celery Task Stuck on PENDING (Shared Redis Database Issue)

## Root Cause
Production and staging share the same Redis database, causing the production Celery worker to pick up staging tasks — then fail because the job record exists in the staging database, not production.

---

## Symptoms
- Task shows `PENDING` forever on staging
- Job is created in the staging database but never processed
- Production Celery logs show `DoesNotExist` errors for staging jobs

---

## Fix

### Step 1 — Check which Redis db each environment uses
```bash
grep REDIS_URL /var/www/your-app/.env
grep REDIS_URL /var/www/your-app-staging/.env
```
If both return the same db (e.g. both `/0`), they are conflicting.

### Step 2 — Assign staging a different Redis db
```bash
nano /var/www/your-app-staging/.env
```
Change all three Redis values:
```
REDIS_URL=redis://127.0.0.1:6379/2
CELERY_BROKER_URL=redis://127.0.0.1:6379/2
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/2
```

### Step 3 — Update the staging Celery service file
```bash
nano /etc/systemd/system/celery-your-app-staging.service
```
Add this under `[Service]`:
```
Environment="REDIS_URL=redis://127.0.0.1:6379/2"
```

### Step 4 — Reload and restart
```bash
systemctl daemon-reload
systemctl restart your-app-staging
systemctl restart celery-your-app-staging
```

---

## Redis DB Convention (This Server)
| DB | Environment             |
|----|-------------------------|
| 0  | esteemcbt production    |
| 1  | examspower staging      |
| 2  | esteemcbt staging       |
| 3  | examspower production   |
| 4  | codethinkers production |
| 5  | codethinkers staging    |

---

## Prevention
Always set different Redis db numbers per environment in `.env` and update the GitHub Secret accordingly so it persists after every deployment.