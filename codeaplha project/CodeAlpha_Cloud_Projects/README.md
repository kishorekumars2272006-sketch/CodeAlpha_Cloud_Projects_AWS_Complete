# CodeAlpha Cloud Computing Internship — Tasks 1 and 3

A beginner-friendly Flask project that implements the two selected tasks from the supplied CodeAlpha PDF:
- **Task 1 — Data Redundancy Removal System:** validates records, normalizes name/email/category, creates a SHA-256 fingerprint, and blocks duplicate inserts with an application check plus a database uniqueness constraint.
- **Task 3 — Cloud-Based Bus Pass System:** creates online demo bookings, assigns a unique booking code, rejects past dates, and calculates prices on the server rather than trusting the browser.

This is a learning/demo app. It uses SQLite locally and supports PostgreSQL through `DATABASE_URL` for a cloud deployment. The fares and routes are fictional examples.

## 1. Requirements

- Windows 10/11
- Python 3.11 or 3.12
- VS Code or PyCharm
- Internet connection for package installation
- For AWS deployment: AWS account, AWS CLI, and AWS Elastic Beanstalk CLI (`eb`)

## 2. Run locally on Windows

Open PowerShell in this folder:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

If PowerShell blocks activation, run this for the current terminal only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Open http://127.0.0.1:5000 in your browser. `/health` should return `{"status":"ok"}`.

SQLite database `codealpha.db` is created automatically. Do not upload it to GitHub.

## 3. Test the project

With the virtual environment activated:

```powershell
python -m unittest discover -s tests -v
```

The tests check dashboard availability, unique record insertion, duplicate rejection despite case/space differences, invalid email rejection, server-side fare calculation, rejection of past dates, and the health endpoint.

Manual checks:
1. Task 1: add `Priya Kumar`, `priya@example.com`, `Student`.
2. Submit the same record again. It should be blocked.
3. Submit ` PRIYA   KUMAR `, `PRIYA@example.com`, ` student `. It should also be blocked.
4. Task 3: make a booking for a future date. A `CA-...` booking code and sample price should appear.
5. Try a past date; the booking should be rejected.
6. Visit `/health`.

## 4. How Task 1 works

1. Validate required fields and a basic email format.
2. Normalize case and repeated spaces.
3. Build a canonical string from name, email and category.
4. Compute a SHA-256 fingerprint.
5. Check whether the fingerprint already exists.
6. Store only a unique record. A database `UNIQUE` constraint provides a second layer against duplicate keys during simultaneous requests.

The chosen duplicate rule is a demonstrator. It may miss duplicates where the same person uses a different email, or treat two people with identical fields as duplicates. In a real system, define a domain-specific identity rule and review uncertain matches as possible false positives.

## 5. How Task 3 works

1. User selects a route, pass type and date.
2. The server validates the input and rejects past dates.
3. The server looks up the fare in `ROUTES`; a user-supplied price is ignored.
4. The app generates a booking code and saves the booking.
5. The database enforces uniqueness for the booking code.

This is a demo, not a production ticketing platform. It does not integrate with real buses, payments, QR ticket validation, user accounts or live capacity management.

## 6. AWS deployment overview

**Recommended beginner deployment:** AWS Elastic Beanstalk for the Flask web app, with Amazon RDS for PostgreSQL for persistent database storage.

Do not rely on a local SQLite file for a public AWS deployment: application instances can be replaced, and their local filesystem is not a durable shared database.

### A. Prepare AWS access

1. Create/sign in to an AWS account and enable MFA.
2. Install and configure AWS CLI using an IAM identity with least-privilege permissions. Do not use root access keys.
3. Install the Elastic Beanstalk CLI by following the official AWS documentation for your operating system.
4. Be aware that Elastic Beanstalk, EC2, RDS, data transfer, and public IPv4 can incur charges. Set a budget alert before creating resources.

### B. Create a PostgreSQL database

In AWS Console, open **Amazon RDS → Create database**:
- Engine: PostgreSQL
- Template: Free tier only if your account currently qualifies and the offered configuration is free; otherwise choose a low-cost test configuration and review the estimate.
- Create a strong database username/password and store them securely.
- Prefer private access from the Elastic Beanstalk application. Configure the RDS security group to accept PostgreSQL (TCP 5432) only from the Elastic Beanstalk instance security group, not from `0.0.0.0/0`.
- Record the endpoint, database name, username and password.

### C. Deploy to Elastic Beanstalk

From the project directory, initialize the environment (choose a supported Python platform branch shown by the CLI):

```powershell
eb init
eb create codealpha-cloud-projects
```

Set environment variables through Elastic Beanstalk configuration (Console → Environment → Configuration → Updates, monitoring, and logging / Software, depending on console version). Set:
- `SECRET_KEY`: a long random secret; never commit it
- `DATABASE_URL`: `postgresql://DB_USER:URL_ENCODED_PASSWORD@RDS_ENDPOINT:5432/DB_NAME`

If the password contains reserved URL characters, URL-encode it before putting it in the URI. For a real deployment, prefer Secrets Manager or Parameter Store rather than storing credentials directly as plain environment configuration.

Then deploy:

```powershell
eb deploy
eb open
```

Confirm the homepage loads and `/health` returns `{"status":"ok"}`. Check logs with:

```powershell
eb logs
```

**Important:** Creating RDS separately and connecting it securely requires careful VPC/security-group setup. Do not make the database publicly accessible just to make the connection work. Follow the current official AWS guides linked below, because console labels and platform versions can change.

Official documentation:
- Elastic Beanstalk Python: https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-flask.html
- Elastic Beanstalk CLI: https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/eb-cli3.html
- Environment properties: https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/environments-cfg-softwaresettings.html
- Amazon RDS for PostgreSQL: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html
- AWS Budgets: https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html

### D. Verify cloud deployment

- Open the public app URL.
- Check `/health`.
- Add a unique Task 1 record, then confirm a duplicate is rejected.
- Create a future bus-pass booking and confirm the server-calculated fare and booking code.
- Restart/redeploy the app and verify data remains in RDS.
- Inspect logs for errors.
- When finished, delete the Elastic Beanstalk environment and RDS resources if you no longer need them, to avoid ongoing charges. Take a backup first if needed.

## 7. GitHub repository

Create a public or private repository named exactly:

`CodeAlpha_CloudComputing`

The PDF asks for a repository named `CodeAlpha_ProjectName`; if your coordinator expects separate repositories, use `CodeAlpha_DataRedundancyRemoval` and `CodeAlpha_BusPassSystem`. Confirm the preferred naming with the internship coordinator.

Before pushing, check that `.env`, passwords, AWS keys, database files and secrets are not included.

```powershell
git init
git add .
git status
git commit -m "Build CodeAlpha cloud computing tasks 1 and 3"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/CodeAlpha_CloudComputing.git
git push -u origin main
```

Replace `YOUR_USERNAME` with your GitHub username. If Git asks you to authenticate, use GitHub's supported sign-in or token workflow; do not paste credentials into source files.

## 8. LinkedIn submission preparation

The supplied PDF says to:
1. Share internship status on LinkedIn and tag `@CodeAlpha`.
2. Upload complete source code to GitHub in a repository named `CodeAlpha_ProjectName`.
3. Post a video explanation with the GitHub repository link.
4. Submit the completed task through the submission form shared in the WhatsApp group.

Suggested post (edit before publishing):

> Excited to share my Cloud Computing internship projects with CodeAlpha!
>
> I built two Python Flask projects:
> 1. Data Redundancy Removal System — validates records and prevents duplicate entries using normalized data fingerprints and database uniqueness constraints.
> 2. Cloud-Based Bus Pass System — supports demo bookings, unique booking codes, date validation and server-side fare calculation.
>
> I tested the applications locally and prepared an AWS Elastic Beanstalk + Amazon RDS deployment path.
>
> GitHub: [add your repository link]
>
> #CodeAlpha #CloudComputing #Python #AWS #Flask

### 2–3 minute video outline

1. Introduce yourself and name both tasks.
2. Show the dashboard.
3. Demonstrate adding a unique record, then show duplicate prevention.
4. Demonstrate a valid bus-pass booking and its booking code.
5. Show the code structure and briefly explain database uniqueness and server-side fare calculation.
6. If deployed, show the AWS app URL and `/health`.
7. Finish with the GitHub repository link.

## 9. Known limitations and next improvements

- No authentication or role-based access control.
- No payment gateway, actual operator timetable, seat inventory or QR scanning.
- Basic email validation only; no email verification.
- No automated backups configured by this code.
- The demo lists recent bookings/records publicly; do not use real personal information.
- For production, add authentication, CSRF protection, rate limits, stronger validation, logging/monitoring, database migrations, secrets management, HTTPS, backups and privacy controls.

## 10. Deliverables checklist

- [ ] Run locally
- [ ] Pass all unit tests
- [ ] Complete both manual demonstrations
- [ ] Deploy to AWS and verify persistence (if required/within budget)
- [ ] Push source code to GitHub without secrets
- [ ] Record project demo video
- [ ] Post on LinkedIn and tag CodeAlpha
- [ ] Submit through the official form
