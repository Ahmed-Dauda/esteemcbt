# Django App Deployment on Hetzner — Complete Guide
### Based on deploying `esteemcbt` → `https://examspower.com`

---

## LEGEND
- 🖥️ **SERVER TERMINAL** — SSH session showing `root@coolify:~#` or `(venv) root@coolify:/var/www/esteemcbt#`
- 💻 **LOCAL TERMINAL** — VS Code terminal showing `PS C:\Users\HP\...>`

---

## STEP 1 — Create Hetzner Server

1. Go to [hetzner.com](https://hetzner.com) and create an account
2. Create a new **Cloud Server**:
   - Location: Your preferred region
   - OS: **Ubuntu 24.04**
   - Type: CX21 or higher (2 vCPU, 4GB RAM recommended)
3. Add your SSH key or note the root password from the email Hetzner sends you
4. Note your server IP (e.g. `204.168.237.20`)

---

## STEP 2 — Connect to Server via SSH

💻 **LOCAL TERMINAL:**
```powershell
ssh root@204.168.237.20
```
Enter the password from Hetzner's email when prompted.

You should see:
```
root@coolify:~#
```

---

## STEP 3 — Set Up PostgreSQL Database

🖥️ **SERVER TERMINAL:**
```bash
# Install PostgreSQL
apt-get update
apt-get install -y postgresql postgresql-contrib

# Start PostgreSQL
systemctl start postgresql
systemctl enable postgresql

# Create database and user
sudo -u postgres psql
```

Inside psql:
```sql
CREATE DATABASE mydb;
CREATE USER myuser WITH PASSWORD 'YourPassword';
GRANT ALL PRIVILEGES ON DATABASE mydb TO myuser;
ALTER DATABASE mydb OWNER TO myuser;
GRANT ALL ON SCHEMA public TO myuser;
\q
```

---

## STEP 4 — Install System Dependencies

🖥️ **SERVER TERMINAL:**
```bash
apt-get install -y python3 python3-pip python3-venv
apt-get install -y libpq-dev python3-dev
apt-get install -y libfreetype6-dev
apt-get install -y nginx
```

---

## STEP 5 — Upload Project Files

🖥️ **SERVER TERMINAL — Create project folder:**
```bash
mkdir -p /var/www/esteemcbt
```

💻 **LOCAL TERMINAL — Upload project files:**
```powershell
# Upload entire project
scp -r "C:\Users\HP\Desktop\DJANGO_PROJECTS\esteemcbt" root@204.168.237.20:/var/www/

# If any folders are missing, upload them individually
scp -r "C:\Users\HP\Desktop\DJANGO_PROJECTS\esteemcbt\school" root@204.168.237.20:/var/www/esteemcbt/
scp -r "C:\Users\HP\Desktop\DJANGO_PROJECTS\esteemcbt\static" root@204.168.237.20:/var/www/esteemcbt/
```

🖥️ **SERVER TERMINAL — Verify upload:**
```bash
ls /var/www/esteemcbt
find /var/www/esteemcbt -name "settings.py"
```

---

## STEP 6 — Fix requirements.txt Encoding Issues

If your `requirements.txt` was created on Windows, it may have UTF-16 encoding issues. Fix it:

🖥️ **SERVER TERMINAL:**
```bash
# Recreate requirements.txt as clean UTF-8
python3 -c "
content = open('requirements.txt', 'rb').read()
if content.startswith(b'\xff\xfe'):
    text = content[2:].decode('utf-16-le', errors='ignore')
else:
    text = content.decode('utf-8', errors='ignore')
open('requirements_clean.txt', 'w', encoding='utf-8', newline='\n').write(text)
print('Done!')
"
mv requirements_clean.txt requirements.txt
```

Also fix any package version issues (e.g. `django-embed-video==1.5.0` doesn't exist):
```bash
# Find and fix line number
sed -n '44,48p' requirements.txt
# Fix specific line (replace N with actual line number)
sed -i 'Ns/.*/django-embed-video==1.4.10/' requirements.txt
```

---

## STEP 7 — Set Up Python Virtual Environment

🖥️ **SERVER TERMINAL:**
```bash
cd /var/www/esteemcbt

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

> ⚠️ If you get build errors, install missing system libraries:
> ```bash
> apt-get install -y libpq-dev python3-dev libfreetype6-dev
> ```
> Then re-run `pip install -r requirements.txt`

---

## STEP 8 — Configure settings.py for Production

🖥️ **SERVER TERMINAL:**
```bash
nano /var/www/esteemcbt/school/settings.py
```

Update these settings:
```python
DEBUG = False

ALLOWED_HOSTS = ['examspower.com', 'www.examspower.com', '204.168.237.20', 'localhost']

CSRF_TRUSTED_ORIGINS = ['https://examspower.com', 'https://www.examspower.com']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mydb',
        'USER': 'myuser',
        'PASSWORD': 'YourPassword',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}
```

Also update your `.env` file:
```bash
nano /var/www/esteemcbt/.env
```
```
DEBUG=False
ALLOWED_HOSTS=examspower.com,www.examspower.com,204.168.237.20,127.0.0.1,localhost
DATABASE_URL=postgresql://myuser:YourPassword@127.0.0.1:5432/mydb
```

---

## STEP 9 — Fix Code Issues

### Fix `import imp` error (removed in Python 3.12)

🖥️ **SERVER TERMINAL:**
```bash
nano /var/www/esteemcbt/student/admin.py
# Remove or replace: import imp → import importlib
```

### Fix any missing migrations
```bash
python manage.py check
python manage.py migrate
```

### Grant PostgreSQL permissions if needed
```bash
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE mydb TO myuser;"
sudo -u postgres psql -c "ALTER DATABASE mydb OWNER TO myuser;"
sudo -u postgres psql mydb -c "GRANT ALL ON SCHEMA public TO myuser;"
```

---

## STEP 10 — Collect Static Files

🖥️ **SERVER TERMINAL:**
```bash
cd /var/www/esteemcbt
source venv/bin/activate
python manage.py collectstatic --noinput
```

> ⚠️ If static files are missing (404 errors in browser), download them from CDN:
> ```bash
> mkdir -p /var/www/esteemcbt/staticfiles/sms/dashboard/css
> mkdir -p /var/www/esteemcbt/staticfiles/sms/dashboard/vendor/fontawesome-free/css
> curl -o /var/www/esteemcbt/staticfiles/sms/prism.css https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism.min.css
> curl -o /var/www/esteemcbt/staticfiles/sms/prism.js https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js
> curl -o /var/www/esteemcbt/staticfiles/sms/dashboard/css/sb-admin-2.min.css https://cdnjs.cloudflare.com/ajax/libs/startbootstrap-sb-admin-2/4.1.4/css/sb-admin-2.min.css
> curl -o /var/www/esteemcbt/staticfiles/sms/dashboard/vendor/fontawesome-free/css/all.min.css https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css
> ```

Also make sure Nginx serves static files correctly using `alias` not `root`:
```nginx
location /static/ {
    alias /var/www/esteemcbt/staticfiles/;
}
```

---

## STEP 11 — Set Up Uvicorn as Systemd Service

> ⚠️ Use **Uvicorn** (not Gunicorn) if your project uses ASGI (has `asgi.py` or Django Channels)

🖥️ **SERVER TERMINAL:**
```bash
pip install uvicorn

nano /etc/systemd/system/esteemcbt.service
```

Paste this:
```ini
[Unit]
Description=Uvicorn daemon for esteemcbt
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/esteemcbt
ExecStart=/var/www/esteemcbt/venv/bin/uvicorn --workers 3 --uds /var/www/esteemcbt/esteemcbt.sock school.asgi:application

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl start esteemcbt
systemctl enable esteemcbt
systemctl status esteemcbt
```

---

## STEP 12 — Configure Nginx

🖥️ **SERVER TERMINAL:**
```bash
nano /etc/nginx/sites-available/esteemcbt
```

Paste this:
```nginx
server {
    listen 80;
    server_name examspower.com www.examspower.com;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias /var/www/esteemcbt/staticfiles/;
    }

    location /media/ {
        root /var/www/esteemcbt;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/esteemcbt/esteemcbt.sock;
    }
}
```

```bash
ln -s /etc/nginx/sites-available/esteemcbt /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

---

## STEP 13 — Create Superuser

🖥️ **SERVER TERMINAL:**
```bash
cd /var/www/esteemcbt
source venv/bin/activate
python manage.py shell
```

Inside shell:
```python
from users.models import NewUser
user = NewUser(email='your@email.com', username='admin')
user.set_password('YourPassword')
user.is_staff = True
user.is_superuser = True
user.is_active = True
user.save()
exit()
```

> ⚠️ Use `username` to login to `/admin`, not email — because `USERNAME_FIELD = 'username'`

---

## STEP 14 — Set Up Redis

🖥️ **SERVER TERMINAL:**
```bash
apt-get install -y redis-server
systemctl start redis
systemctl enable redis
systemctl status redis
```

---

## STEP 15 — Set Up Celery Worker

🖥️ **SERVER TERMINAL:**
```bash
nano /etc/systemd/system/esteemcbt-celery.service
```

Paste this:
```ini
[Unit]
Description=Celery Worker for esteemcbt
After=network.target redis-server.service

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/esteemcbt
ExecStart=/var/www/esteemcbt/venv/bin/celery -A school worker --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl start esteemcbt-celery
systemctl enable esteemcbt-celery
systemctl status esteemcbt-celery
```

---

## STEP 16 — Set Up Celery Beat

🖥️ **SERVER TERMINAL:**
```bash
nano /etc/systemd/system/esteemcbt-celerybeat.service
```

Paste this:
```ini
[Unit]
Description=Celery Beat for esteemcbt
After=network.target redis-server.service

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/esteemcbt
ExecStart=/var/www/esteemcbt/venv/bin/celery -A school beat --loglevel=info
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
systemctl daemon-reload
systemctl start esteemcbt-celerybeat
systemctl enable esteemcbt-celerybeat
systemctl status esteemcbt-celerybeat
```

---

## STEP 17 — Set Up Cron Job Scheduler

🖥️ **SERVER TERMINAL:**
```bash
crontab -e
```

Add this line at the bottom:
```bash
*/30 * * * * /var/www/esteemcbt/venv/bin/python /var/www/esteemcbt/manage.py cleanup_old_sessions >> /var/log/esteemcbt_scheduler.log 2>&1
```

Verify:
```bash
crontab -l
```

Test manually:
```bash
cd /var/www/esteemcbt && source venv/bin/activate && python manage.py cleanup_old_sessions
```

---

## STEP 18 — Set Up PostgreSQL Auto Backups

🖥️ **SERVER TERMINAL:**
```bash
mkdir -p /var/backups/esteemcbt

# Create .pgpass for passwordless auth
echo "127.0.0.1:5432:mydb:myuser:YourPassword" > /root/.pgpass
chmod 600 /root/.pgpass

# Create backup script
nano /usr/local/bin/backup_esteemcbt.sh
```

Paste this:
```bash
#!/bin/bash
DATE=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_DIR=/var/backups/esteemcbt
DB_NAME=mydb
DB_USER=myuser

pg_dump -U $DB_USER -h 127.0.0.1 $DB_NAME > $BACKUP_DIR/backup_$DATE.sql
gzip $BACKUP_DIR/backup_$DATE.sql
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
echo "Backup completed: backup_$DATE.sql.gz"
```

```bash
chmod +x /usr/local/bin/backup_esteemcbt.sh

# Test it
/usr/local/bin/backup_esteemcbt.sh
ls -lh /var/backups/esteemcbt/

# Schedule daily at 2am
crontab -e
```

Add this line:
```bash
0 2 * * * /usr/local/bin/backup_esteemcbt.sh >> /var/log/esteemcbt_backup.log 2>&1
```

---

## STEP 19 — Set Up Domain + SSL

### Point domain to server (Namecheap)
1. Login to Namecheap → Domain List → Manage → Advanced DNS
2. Delete existing records
3. Add:
   - `A Record` | `@` | `204.168.237.20`
   - `A Record` | `www` | `204.168.237.20`

### Install SSL with Certbot
🖥️ **SERVER TERMINAL:**
```bash
apt-get install -y certbot python3-certbot-nginx
certbot --nginx -d examspower.com -d www.examspower.com
```

Follow prompts — enter email, agree to terms.

---

## STEP 20 — Set Up Email (Gmail SMTP)

Update `.env` file:
🖥️ **SERVER TERMINAL:**
```bash
nano /var/www/esteemcbt/.env
```

Add/update:
```
EMAIL_HOST_USER=youremail@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=youremail@gmail.com
```

> ⚠️ Use a Gmail **App Password** (not your regular password).
> Generate at: Google Account → Security → 2-Step Verification → App Passwords

Test email:
```bash
cd /var/www/esteemcbt && source venv/bin/activate && python manage.py shell
```

Inside shell:
```python
from django.core.mail import send_mail
send_mail('Test', 'It works!', 'youremail@gmail.com', ['youremail@gmail.com'])
exit()
```

---

## STEP 21 — Set Up CI/CD with GitHub Actions

CI/CD means every time you push code to GitHub, it automatically deploys to your server. No manual SSH needed.

**The flow:**
```
You push code to GitHub (git push)
          ↓
GitHub Actions SSHs into your server
          ↓
Pulls latest code + restarts app automatically
          ↓
https://examspower.com is updated ✅
```

### STEP 21.1 — Generate SSH key on server

🖥️ **SERVER TERMINAL:**
```bash
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_actions -N ""
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys
```

Save the private key to a file for easy copying:
```bash
cat ~/.ssh/github_actions > /tmp/mykey.txt
```

### STEP 21.2 — Download the private key to your local machine

💻 **LOCAL TERMINAL:**
```powershell
scp root@204.168.237.20:/tmp/mykey.txt "C:\Users\HP\Desktop\mykey.txt"
notepad "C:\Users\HP\Desktop\mykey.txt"
```

Select all (`Ctrl+A`) and copy the entire key content.

### STEP 21.3 — Add secrets to GitHub

1. Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** and add these 3 secrets:

| Secret Name | Value |
|---|---|
| `SERVER_HOST` | `204.168.237.20` |
| `SERVER_USER` | `root` |
| `SERVER_SSH_KEY` | contents of mykey.txt |

> ⚠️ For `SERVER_SSH_KEY` — open `mykey.txt` in Notepad, press `Ctrl+A` to select all, copy and paste into GitHub. Make sure it includes the `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----` lines.

### STEP 21.4 — Create the workflow file

💻 **LOCAL TERMINAL:**
```powershell
New-Item -Path ".github\workflows\deploy.yml" -ItemType File -Force
notepad ".github\workflows\deploy.yml"
```

Paste this inside:
```yaml
name: Deploy to Hetzner

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to server
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SERVER_SSH_KEY }}
          script: |
            cd /var/www/esteemcbt
            git pull origin main
            source venv/bin/activate
            pip install -r requirements.txt
            python manage.py migrate
            python manage.py collectstatic --noinput
            systemctl restart esteemcbt
            systemctl restart esteemcbt-celery
            systemctl restart esteemcbt-celerybeat
            echo "Deployment successful!"
```

Save and close Notepad.

### STEP 21.5 — Set up Git on the server

🖥️ **SERVER TERMINAL:**
```bash
cd /var/www/esteemcbt
git init
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git fetch origin main
git checkout -f main
```

> ⚠️ If you get SSH permission errors, switch to HTTPS:
> ```bash
> git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
> git pull origin main
> ```

### STEP 21.6 — Push and test the pipeline

💻 **LOCAL TERMINAL:**
```powershell
git add .
git commit -m "Add CI/CD workflow"
git push origin main
```

Then go to `https://github.com/YOUR_USERNAME/YOUR_REPO/actions` and watch it deploy!

- ✅ Green tick = deployed successfully
- ❌ Red cross = click the failed step to see the error

### IMPORTANT — Always fix code locally, never on the server!

```
❌ WRONG: Fix bug directly on server → CI/CD overwrites it on next push
✅ RIGHT: Fix bug locally → git push → CI/CD deploys the fix
```

---

## USEFUL COMMANDS

### 🖥️ SERVER TERMINAL — Service Management
```bash
# Restart everything
systemctl restart esteemcbt
systemctl restart esteemcbt-celery
systemctl restart esteemcbt-celerybeat
systemctl restart nginx

# Check status
systemctl status esteemcbt
systemctl status esteemcbt-celery
systemctl status esteemcbt-celerybeat

# View logs
journalctl -u esteemcbt -n 50 --no-pager
tail -20 /var/log/nginx/error.log
tail -20 /var/log/esteemcbt_scheduler.log
tail -20 /var/log/esteemcbt_backup.log
```

### 🖥️ SERVER TERMINAL — Django Commands
```bash
cd /var/www/esteemcbt
source venv/bin/activate

python manage.py check
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py shell
```

### 🖥️ SERVER TERMINAL — Database
```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Manual backup
/usr/local/bin/backup_esteemcbt.sh

# List backups
ls -lh /var/backups/esteemcbt/
```

---

## CREDENTIALS SUMMARY

| Item | Value |
|---|---|
| Site | https://examspower.com |
| Admin Panel | https://examspower.com/admin |
| Admin Username | admin |
| Server IP | 204.168.237.20 |
| SSH | `ssh root@204.168.237.20` |
| DB Name | mydb |
| DB User | myuser |
| Backups | /var/backups/esteemcbt/ |

---

## ARCHITECTURE OVERVIEW

```
Your Laptop (VS Code)
    ↓ git push
GitHub Repository
    ↓ GitHub Actions (CI/CD)
    ↓ SSH into server → git pull → restart
Hetzner Server (204.168.237.20)
    ↓
Nginx (port 80/443)
    ↓
Uvicorn (ASGI, Unix socket)
    ↓
Django App (/var/www/esteemcbt)
    ↓           ↓           ↓
PostgreSQL    Redis      Cloudinary
(database)  (broker)    (media files)
                ↓
            Celery Worker + Beat
            (background tasks)
```

---

*Generated from actual deployment session — May 2026*