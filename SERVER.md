# DEPLOYMENT QUICK REFERENCE
# ===========================


# 1. SSH INTO SERVER
ssh root@204.168.237.20
MyServer2026!Coolify

# ===========================
# 2. STAGING ENVIRONMENT
# ===========================

# NAVIGATE TO STAGING PROJECT
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
MyServer2026!Coolify
cd /var/www/esteemcbt
source venv/bin/activate

#  TO REFLECT CHANGES OF LOCAL MACHINE U NEED TO
# See what changed
git status
git fetch origin
git log --oneline HEAD..origin/main
# Pull the update
git pull origin main
# If using gunicorn via systemd
systemctl restart esteemcbt
# or whatever your service is called, e.g.:
# systemctl restart gunicorn
# If using supervisor
supervisorctl restart esteemcbt
# If using nginx + uwsgi
systemctl restart uwsgi


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