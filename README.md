# Surplus Food Redistribution and Donation Management System
> **Tagline:** *"Rescue Surplus Food. Reduce Waste. Feed Communities."*  
> **Academic Prototype:** Nirman Lab Engineering Project  
> **Theme:** *"Data, Statistics & ML for Real India"*

---

## 1. Executive Summary & Purpose

In India's urban metropolises, significant quantities of edible, wholesome food from hotels, banquet halls, weddings, corporate canteens, and restaurants are discarded daily. Concurrently, millions face persistent nutritional insecurity.

The **Surplus Food Redistribution and Donation Management System** is a full-stack engineering web application developed to bridge this logistical gap. It connects commercial food donors with verified non-governmental organizations (NGOs) and civic volunteers for immediate, auditable, and food-safe redistribution.

---

## 2. Technology Stack & Architecture

- **Backend:** Python 3.10+ & Flask 3.1
- **Database:** SQLite 3 with relational constraints, foreign keys, transaction rollbacks, and indexing
- **Frontend:** Responsive HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3
- **Data Visualizations & Charts:** Chart.js 4.4
- **Icons & Typography:** Font Awesome 6.5, Segoe UI typography
- **Security:** PBKDF2 / SHA-256 password hashing with Werkzeug, session-based Role-Based Access Control (RBAC), SQL injection prevention via parameterized queries, CSRF and concurrency transaction locks.

### Project Directory Structure

```
surplus_food_system/
├── app.py                     # Main Flask routes, controllers, filters & lifecycle handlers
├── database.py                # Database connection, init_db, summary analytics & automated expiry
├── urgency_engine.py          # Nirman Multi-Factor Urgency & Spoilage Risk Model (NMF-SPUM)
├── auth.py                    # Session auth, PBKDF2 password hashing & RBAC decorators
├── seed_data.py               # Realistic Indian scenario seeding script (Bengaluru, Mumbai)
├── schema.sql                 # Pure SQL schema DDL with relational integrity constraints
├── requirements.txt           # Minimal dependencies (Flask, Werkzeug)
├── README.md                  # Comprehensive documentation and exhibition viva guide
├── static/
│   ├── css/
│   │   └── style.css          # Custom food-rescue green/white styling, timeline & cards
│   └── js/
│       ├── main.js            # Live search, confirmation modals, notification pollers
│       └── charts.js          # Chart.js rendering for analytics & admin monitoring
└── templates/
    ├── base.html              # Responsive layout with dynamic unread notification pill
    ├── index.html             # Landing page with stats, workflow, benefits & safety notice
    ├── login.html             # Secure login with 1-Click Exhibition Demo Switcher
    ├── register_donor.html    # Commercial donor onboarding form
    ├── register_ngo.html      # NGO & volunteer registration with verification notice
    ├── notifications.html     # Real-time event notification center
    ├── donor/
    │   ├── dashboard.html     # Donor metrics, status filters, recent listings table
    │   ├── add_donation.html  # Food listing form with safety declaration
    │   └── edit_donation.html # Edit active available listing
    ├── ngo/
    │   ├── dashboard.html     # Collector metrics, active tasks queue & urgent feed
    │   └── available.html     # Marketplace with live search, filters & urgency badges
    ├── donations/
    │   └── detail.html        # End-to-end lifecycle stepper, audit history & safety modal
    ├── admin/
    │   ├── dashboard.html     # System overview cards, Chart.js preview & moderation
    │   ├── users.html         # User management, NGO verification & account toggle
    │   ├── donations.html     # All donations oversight & administrative removal
    │   ├── safety_reports.html# Food safety concern queue & resolution actions
    │   └── analytics.html     # "Data, Statistics & ML for Real India" detailed page
    └── errors/
        ├── 403.html           # Forbidden access handler
        ├── 404.html           # Resource not found handler
        └── 500.html           # Server exception handler
```

---

## 3. Pre-Configured Demonstration Accounts

To facilitate rapid, frictionless testing during college laboratory exhibitions, pre-configured accounts are provided with a **1-Click Demo Login Switcher** located directly on the login page:

| Role | Organization / User | Email | Password | Service Area |
| :--- | :--- | :--- | :--- | :--- |
| **Administrator** | Nirman Lab Administrator | `admin@nirman.edu` | `Admin@123` | Bengaluru |
| **Donor (Restaurant)** | The Spice Garden Restaurant | `donor.spice@gmail.com` | `Donor@123` | Bengaluru |
| **Donor (Convention)** | Grand Orchid Convention Center | `donor.orchid@gmail.com` | `Donor@123` | Bengaluru |
| **Donor (Bakery)** | Fresh Daily Artisan Bakery | `donor.bakery@gmail.com` | `Donor@123` | Bengaluru |
| **NGO (Verified)** | Anna Seva Feeding Foundation | `ngo.annaseva@gmail.com` | `Ngo@123` | Bengaluru |
| **NGO (Unverified)** | Hope Haven Care Society | `ngo.hope@gmail.com` | `Ngo@123` | Bengaluru |
| **Volunteer (Runner)** | Rahul Sharma (Youth Brigade) | `rahul.volunteer@gmail.com` | `Volunteer@123` | Bengaluru |

---

## 4. End-to-End Workflow Demonstration

For a complete exhibition demonstration, execute this step-by-step walkthrough:

```
[Donor Lists Surplus] ──► [Urgency Scoring] ──► [Verified NGO Accepts] ──► [Pickup Confirmed] ──► [Delivered to Shelter]
```

1. **Step 1: Donor Lists Surplus Food**
   - Click **Demo Login -> Donor**.
   - Navigate to **List Food**.
   - Input food details (e.g., *70 servings of Paneer Biryani*, category *Cooked Meals*, storage *Insulated Container*, cutoff *3 hours from now*).
   - Check the **Mandatory Food Safety Declaration** and submit.
   - The listing is saved, and status is logged as `AVAILABLE`.

2. **Step 2: Urgency Triage Engine Computes Score**
   - The system calculates an **Urgency Priority Score (0-100)** based on remaining time to cutoff, perishability index, storage temperature, and volume.
   - The listing is immediately visible on the **Available Food** page with a color-coded urgency badge.

3. **Step 3: NGO Claims Listing**
   - Click **Demo Login -> NGO (Anna Seva)**.
   - Visit **Find Available Food**.
   - Filter by *Cooked Meals* or sort by *Highest Urgency*.
   - Click **Accept Food**.
   - Database transaction verifies availability, prevents double claims, updates status to `ACCEPTED`, logs the audit timestamp, and notifies the donor.

4. **Step 4: Volunteer Confirms Physical Pickup**
   - Click **Demo Login -> Volunteer (Rahul Sharma)** or stay as the assigned NGO.
   - Open **Collector Dashboard -> Active Collection Tasks**.
   - Click **Mark Picked Up**.
   - Donation status updates to `PICKED_UP`. A timestamped audit entry is permanently recorded.

5. **Step 5: Safe Distribution & Delivery Confirmation**
   - After transporting the food in thermal bags to the community shelter, the collector clicks **Mark Delivered**.
   - Donation status transitions to `DELIVERED`. Donor and admin dashboards reflect completed salvage metrics.

6. **Step 6: Administrative Oversight & Governance**
   - Click **Demo Login -> Admin**.
   - Open **Manage Users** to review and verify new NGO applicants.
   - Open **Safety Reports** to review reported hygiene/storage issues.
   - Open **Data Analytics** to inspect conversion rates and Chart.js graphs.

---

## 5. "Data, Statistics & ML for Real India" Implementation

### A. Separation of Measurement Units (Scientific Integrity)
In adherence to statistical methodology, quantities are never conflated into invalid arithmetic sums:
- **Cooked Meals:** Tracked strictly in `servings`.
- **Farm Produce & Raw Staples:** Tracked strictly in `kilograms (kg)`.
- **Packaged Provisions:** Tracked strictly in `packages / boxes`.

### B. Mathematical Delivery Rate Definition
$$\text{Delivery Rate (\%)} = \left(\frac{\text{Eligible donations delivered}}{\text{Eligible donations listed} - \text{Cancelled listings}}\right) \times 100$$
Donor-cancelled listings are removed from the denominator to measure genuine logistics conversion efficiency.

### C. Nirman Multi-Factor Urgency Model (NMF-SPUM v1.2)
To salvage perishable food before bacterial danger zone proliferation, each listing receives a dynamic score:

$$\text{Score} = (0.50 \times F_{\text{time}}) + (0.25 \times F_{\text{perish}}) + (0.15 \times F_{\text{temp}}) + (0.10 \times F_{\text{volume}})$$

- **$F_{\text{time}}$ (50%):** Exponential risk scaling as pickup cutoff approaches (< 1.5 hrs = 100; < 3 hrs = 85; < 6 hrs = 65).
- **$F_{\text{perish}}$ (25%):** FSSAI-aligned biological decay factor (Cooked Meals = 1.0, Bakery = 0.75, Produce = 0.55, Packaged = 0.20).
- **$F_{\text{temp}}$ (15%):** Storage integrity penalty (Cooked food held at Room Temp receives high risk penalty; Refrigerated receives risk mitigation).
- **$F_{\text{volume}}$ (10%):** Volume scaling prioritizes larger batches to maximize community hunger alleviation throughput.

---

## 6. How to Run Locally

### Prerequisites
- Python 3.8 or higher installed on your computer.

### Step 1: Open Terminal / PowerShell
```bash
cd C:\Users\Admin\.gemini\antigravity\scratch\surplus_food_system
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Initialize and Seed Sample Data
```bash
python seed_data.py
```

### Step 4: Launch Web Application
```bash
python app.py
```

### Step 5: Access the System
Open your web browser and navigate to:
```
http://127.0.0.1:5000
```
Use the **Exhibition Fast Access** buttons on the login page for instantaneous role testing.

---

## 7. Viva & Exhibition Presentation Talking Points

1. **Why SQLite?** Zero-configuration, serverless, atomic ACID-compliant transactions ensure reliable demonstrations without external database service dependencies.
2. **How is Food Safety Handled?** Mandatory preparation time recording, strict pickup deadlines with automated system expiry, thermal storage conditions logging, and a dedicated Food Safety Concern escalation queue.
3. **What Prevents Double Claims?** Concurrency-safe SQL transactions check `status = 'AVAILABLE'` atomically during acceptance.
4. **Why are Units Separated?** Adding kilograms to servings is scientifically invalid; separating units ensures genuine volumetric metrics for evaluators.
