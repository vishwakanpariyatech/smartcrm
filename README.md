# SmartCRM — Enterprise Customer Relationship Management System

SmartCRM is a professional, modern, responsive, and secure Customer Relationship Management (CRM) web application built using Python, Django, HTML5, CSS3, Bootstrap 5, and Chart.js.

Designed for real-world small and medium-sized enterprises (SMEs) and crafted as a showcase portfolio application for Python-Django developers, SmartCRM delivers end-to-end operational capabilities: multi-role authentication (Admin, Manager, Employee), customer life-cycle management, Kanban lead pipelines, deals and revenue analytics with strict double-counting prevention, tasks, follow-up scheduling with interactive calendar grids, in-app notifications, and audit logging.

---

## 🌟 Key Features

1. **Role-Based Access Control (RBAC):**
   - **Admin:** Full CRM administration, user provisioning, team metrics, global data access, system settings.
   - **Manager:** Team performance monitoring, task/lead re-assignment, analytics reports.
   - **Employee:** Scoped access to own assigned customers, leads, follow-ups, deals, and tasks.
   - Server-side access enforcement using Django decorators and CBV mixins.

2. **Executive Live Dashboard:**
   - 8 live database-driven KPI summary cards (Won Sales Revenue, Total Customers, Total Leads, Converted Leads, Pending Tasks, Overdue Tasks, Active Employees, Upcoming Follow-ups).
   - Interactive Chart.js visualizations (Monthly Sales Bar Chart, Lead Pipeline Breakdown Donut, Customer Growth Trend Line).
   - Real-time recent customer, deal, and upcoming follow-up feeds with live activity trail.

3. **Customer Life-cycle Management:**
   - Auto-generated customer identifiers (`CUST-00101`).
   - Rich profile details: contact numbers, email, organization, address, city, state, postal code.
   - Customer detail page featuring customer notes, purchase/deal records, follow-up history, and activity logs.
   - Search by name, company, email, or phone; filter by status, city, and assigned rep.

4. **Lead Pipeline & Kanban Board:**
   - Visual Kanban pipeline with real-time column aggregates (Lead count and pipeline value in INR ₹).
   - Track progression across stages: *New*, *Contacted*, *Interested*, *Qualified*, *Converted*, *Lost*.
   - **1-Click Lead Conversion Workflow:** Converts qualified prospects into active Customer accounts while maintaining full historical context and optionally instantiating a Sales Deal.
   - Reasons recorded for lost leads to support sales retrospectives.

5. **Sales & Deals Pipeline:**
   - Auto-generated deal identifiers (`DEAL-00101`).
   - Stages: *New*, *Proposal*, *Negotiation*, *Won*, *Lost*.
   - Strict commercial revenue calculation based on won deals with zero double-counting.
   - Expected vs. actual closing dates tracking and stage transition shortcuts.

6. **Task Management & Accountability:**
   - Auto-generated task identifiers (`TSK-00101`).
   - Priority indicators: *Low*, *Medium*, *High*, *Urgent*.
   - Instant single-click checkbox toggle for task completion with automated completion timestamp.
   - Visual overdue indicators and dedicated overdue task filter.

7. **Follow-up Calendar & Communications:**
   - Schedule Calls, Meetings, Emails, and Touchpoints.
   - Monthly interactive Calendar Grid View displaying scheduled events by day.
   - Outcome logging modal upon completion of client interactions.

8. **Business Intelligence & Reporting:**
   - Report categories: Sales & Revenue, Leads & Conversion, Customer Acquisition, Team Performance, Task Velocity.
   - Date range pickers, assignee filters, KPI summary cards, and dynamic Chart.js plots.
   - **1-Click CSV Export** for offline spreadsheets.
   - Print-friendly stylesheets (`@media print`) for hard-copy report generation.

9. **In-App Notification Center & Audit Trail:**
   - Unread notification badges and quick dropdown in the top navigation bar.
   - Dedicated notification management page.
   - Immutable audit logging tracking every create, update, delete, convert, and stage transition event.

---

## 🏗️ Architecture & Technology Stack

| Layer | Technologies |
|---|---|
| **Backend Framework** | Python 3.12, Django 6.x |
| **Database** | SQLite (Development), MySQL / PostgreSQL (Production supported) |
| **Frontend Framework** | HTML5, CSS3, Bootstrap 5.3, Bootstrap Icons 1.11 |
| **Data Visualizations** | Chart.js 4.4 |
| **Forms & Styling** | Django Crispy Forms (Bootstrap 5 Template Pack) |
| **Security** | CSRF Tokens, Secure Passwords (PBKDF2/Argon2), Server-Side RBAC, Parameterized SQL via Django ORM |
| **Localization** | Currency: INR (₹), Timezone: `Asia/Kolkata`, Date Format: `DD-MM-YYYY` |

---

## 📂 Project Directory Structure

```text
smartcrm/
│
├── smartcrm/                 # Core Project Configuration
│   ├── settings.py           # Application settings, DB config, installed apps
│   ├── urls.py               # Root URL router & custom error handlers
│   ├── views.py              # Custom 403, 404, 500 error views and redirects
│   ├── wsgi.py               # WSGI server entrypoint
│   └── asgi.py               # ASGI async server entrypoint
│
├── accounts/                 # Authentication, Custom User Model & RBAC
├── dashboard/                # Live Executive Dashboard & Global Search
├── customers/                # Customer Directory, Profiles & Notes
├── leads/                    # Lead Tracking, Kanban Board & Conversion Flow
├── sales/                    # Deals Pipeline, Revenue & Won Contract Tracking
├── tasks/                    # Task Management, Assignments & Overdue Trackers
├── followups/                # Scheduled Follow-ups & Monthly Calendar View
├── employees/                # Team Directory, Roles & Individual Performance
├── reports/                  # BI Reports, Interactive Charts & CSV Exports
├── notifications/            # In-App Notification Center & Context Processors
├── activity_logs/            # Audit Trail & System Security Logs
│
├── static/
│   ├── css/custom.css        # Enterprise SaaS styling & responsive layout
│   └── js/main.js            # Sidebar toggle, modal injectors, alert dismissers
│
├── templates/
│   ├── base.html             # Master layout template
│   ├── includes/             # Sidebar, Navbar, Messages, Modals, Pagination
│   ├── accounts/             # Login, Profile, Settings, Password Reset
│   ├── dashboard/            # Executive Dashboard & Search views
│   ├── customers/            # Customer list, forms, detail
│   ├── leads/                # Lead list, Kanban board, form, detail
│   ├── sales/                # Deal list, form, detail
│   ├── tasks/                # Task list, form, detail
│   ├── followups/            # Follow-up list, calendar, form
│   ├── employees/            # Employee directory, form, detail
│   ├── reports/              # Interactive reports & BI dashboard
│   ├── notifications/        # Notification center
│   ├── activity_logs/        # Audit trail table
│   └── errors/               # Custom 403, 404, 500 error pages
│
├── media/                    # User profile avatars & attachments
├── manage.py                 # Django command-line utility
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── .env                      # Local environment configuration
└── .gitignore                # Git ignore rules
```

---

## 🚀 Getting Started: Local Setup

### 1. Clone or Open the Repository
```bash
cd smartcrm
```

### 2. Create and Activate Virtual Environment
**Windows (PowerShell / Command Prompt):**
```powershell
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Required Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

### 5. Run Database Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Seed Demo Data (Recommended)
Populate realistic enterprise customers, leads across stages, won deals, calendar follow-ups, tasks, and role-based test users:
```bash
python manage.py seed_data
```

This creates the following ready-to-test accounts:

| Username | Password | Role | Description |
|---|---|---|---|
| **admin** | `admin123` | **Admin** | Full system administration & all data access |
| **manager** | `pass123` | **Manager** | Team management, reports & assignment monitoring |
| **employee** | `pass123` | **Employee** | Scoped sales representative view |
| **priya** | `pass123` | **Employee** | Additional sales representative |
| **rohit** | `pass123` | **Employee** | Customer support representative |

*(Optional)* You can also create an independent superuser using:
```bash
python manage.py createsuperuser
```

### 7. Run the Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser to sign in and explore the CRM!

---

## 🗄️ Optional MySQL Configuration

By default, SmartCRM uses SQLite for simple, zero-configuration local development. To switch to a production-grade MySQL database:

1. Install `mysqlclient` or `PyMySQL`:
   ```bash
   pip install mysqlclient
   ```
2. Create your database in MySQL:
   ```sql
   CREATE DATABASE smartcrm_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
3. Update your `.env` file:
   ```env
   DB_ENGINE=mysql
   DB_NAME=smartcrm_db
   DB_USER=your_mysql_username
   DB_PASSWORD=your_mysql_password
   DB_HOST=127.0.0.1
   DB_PORT=3306
   ```
4. Re-run migrations and seed data:
   ```bash
   python manage.py migrate
   python manage.py seed_data
   ```

---

## 🧪 Automated Testing

SmartCRM includes comprehensive automated unit and integration tests covering authentication, permission validation, customer and lead lifecycles, lead conversion, sales revenue math, tasks, follow-up calendar, and BI reports.

To run the full automated test suite:
```bash
python manage.py test
```

To run tests for a specific module:
```bash
python manage.py test accounts
python manage.py test customers
python manage.py test leads
python manage.py test sales
python manage.py test tasks
```

---

## 🌐 Production Deployment Guide

### Recommended Stack:
- **Server:** Ubuntu 22.04 / 24.04 LTS (AWS EC2, DigitalOcean Droplet, Linode) or Platform-as-a-Service (Render, Railway, Fly.io, Heroku)
- **WSGI Server:** Gunicorn (`pip install gunicorn`)
- **Reverse Proxy:** NGINX with SSL (Let's Encrypt / Certbot)
- **Static Assets:** WhiteNoise (`pip install whitenoise`) or AWS S3

### Production Checklist:
1. In `.env`:
   - Set `DEBUG=False`
   - Set a strong, random `SECRET_KEY`
   - Set `ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com`
2. Collect static files:
   ```bash
   python manage.py collectstatic --noinput
   ```
3. Run Gunicorn service:
   ```bash
   gunicorn smartcrm.wsgi:application --bind 0.0.0.0:8000 --workers 3
   ```
4. Configure NGINX proxy pass and enable HTTPS.

---

## 📤 Uploading to GitHub

```bash
git init
git add .
git commit -m "Initial commit: Complete SmartCRM Enterprise Application"
git branch -M main
git remote add origin https://github.com/your-username/smartcrm.git
git push -u origin main
```

---

## 📄 License
This project is licensed under the MIT License — free for educational, portfolio, and commercial use.
