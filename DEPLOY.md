# Publish Lagniappe CRM + turn on email

Everything is pre-packaged in **`lagniappe-crm.zip`** (in this folder). Do Part A,
then Part B. Replace **USERNAME** everywhere with your PythonAnywhere username.

## Part A — Publish it (free, whole team can log in)

**A1. Free account** — go to **pythonanywhere.com** → create a **Beginner account (free)**.
Your web address will be `https://USERNAME.pythonanywhere.com`.

**A2. Upload** — top-right **Files** → **Upload a file** → choose `lagniappe-crm.zip`.

**A3. Unzip** — top-right **Consoles** → **Bash**, then run:
```
unzip lagniappe-crm.zip -d lagniappe-crm
```

**A4. Install libraries** (same console):
```
cd lagniappe-crm
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

**A5. Create the settings file** — change `CHOOSE-A-PASSWORD` (team login, letters/numbers)
and `USERNAME`, then run:
```
printf 'APP_PASSWORD=CHOOSE-A-PASSWORD\nSECRET_KEY=%s\nBASE_URL=https://USERNAME.pythonanywhere.com\n' "$(python3.11 -c 'import secrets;print(secrets.token_hex(32))')" > .env
```

**A6. Create the web app** — top-right **Web** → **Add a new web app** → **Next** →
**Manual configuration** (not "Flask") → **Python 3.11** → **Next**.

**A7. Point it at the app** — on the Web page set:
- **Source code:** `/home/USERNAME/lagniappe-crm`
- **Working directory:** `/home/USERNAME/lagniappe-crm`
- **Virtualenv:** `/home/USERNAME/lagniappe-crm/.venv`
- Click the **WSGI configuration file** link, delete everything, paste this, Save:
```
import sys
path = '/home/USERNAME/lagniappe-crm'
if path not in sys.path:
    sys.path.insert(0, path)
from wsgi import application
```

**A8. Go live** — click the green **Reload** button → visit
`https://USERNAME.pythonanywhere.com` → log in with your team password. Done.
Your 11 companies and 13 contacts are already loaded. Share the link + password.

## Part B — Turn on email (Resend)

**B1.** Make a free account at **resend.com**.

**B2. Verify your domain** — Resend → **Domains** → **Add Domain** → `lagniappefoods.com`.
Add the DNS records it shows (at your domain registrar, or send them to whoever runs
your website). *To test instantly without this, Resend lets you send from
`onboarding@resend.dev` to your own email.*

**B3.** Resend → **API Keys** → **Create API Key** → copy it (starts `re_…`).

**B4. Add it to the app** — PythonAnywhere → **Bash** console:
```
cd lagniappe-crm
printf 'RESEND_API_KEY=re_your_key_here\nFROM_NAME=Lagniappe Foods\nFROM_EMAIL=hello@lagniappefoods.com\nCOMPANY_ADDRESS=YOUR REAL MAILING ADDRESS\n' >> .env
```
Then **Web → Reload**.

**B5. One catch:** PythonAnywhere's *free* plan blocks outgoing email services, so the
**Send** button won't deliver until you switch on their **$5/month "Hacker" plan**
(Account → upgrade). The whole CRM, multiple users, and tracking work fine on free —
only live sending needs the $5 tier.

After the $5 plan is on and your domain is verified: open a campaign → **Send** →
real, tracked emails go out.
