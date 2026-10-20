# Deployment Guide: Surplus Food Redistribution System
> Complete step-by-step instructions to take this application live on the public internet.

---

## Pre-Configured Deployment Assets in this Project

This repository already includes all cloud deployment configuration files:
- [`requirements.txt`](file:///C:/Users/Admin/.gemini/antigravity/scratch/surplus_food_system/requirements.txt): Includes `Flask`, `Werkzeug`, and `gunicorn` (production WSGI server).
- [`Procfile`](file:///C:/Users/Admin/.gemini/antigravity/scratch/surplus_food_system/Procfile): Instructs cloud providers to run `web: gunicorn app:app`.
- [`app.py`](file:///C:/Users/Admin/.gemini/antigravity/scratch/surplus_food_system/app.py): Automatically binds to dynamic cloud `$PORT` and auto-initializes & seeds the SQLite database if not present.
- [`.gitignore`](file:///C:/Users/Admin/.gemini/antigravity/scratch/surplus_food_system/.gitignore): Prevents cache files and sensitive artifacts from leaking to GitHub.

---

## Method 1: Render.com (Recommended Free Cloud Hosting)

**Render** offers a generous free tier for Python web services with automated HTTPS and GitHub integration.

### Step 1: Push Code to GitHub
1. Open PowerShell or Terminal in the project directory:
   ```bash
   cd C:\Users\Admin\.gemini\antigravity\scratch\surplus_food_system
   ```
2. Initialize Git and commit:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of Surplus Food Redistribution System"
   ```
3. Create a new repository on [GitHub](https://github.com/new) (e.g., `surplus-food-system`).
4. Link and push your repository:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/surplus-food-system.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy on Render
1. Visit [Render.com](https://render.com) and sign up / log in with your GitHub account.
2. In the Render Dashboard, click **New +** and select **Web Service**.
3. Select your GitHub repository (`surplus-food-system`).
4. Fill in the deployment settings:
   - **Name:** `surplus-food-system` (or any custom name)
   - **Region:** Singapore / Frankfurt / Oregon (choose closest)
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
   - **Instance Type:** `Free`
5. Click **Create Web Service**.
6. Render will build and deploy your app in 2–3 minutes. Once finished, you will receive a public HTTPS URL:
   ```
   https://surplus-food-system.onrender.com
   ```

---

## Method 2: PythonAnywhere (No Git Required, Native Flask Hosting)

**PythonAnywhere** is a Python-specific platform with a free tier (`yourusername.pythonanywhere.com`).

### Steps:
1. Register for a free account at [PythonAnywhere.com](https://www.pythonanywhere.com).
2. Go to the **Web** tab and click **Add a new web app**.
3. Choose **Flask** and select **Python 3.10**.
4. Go to the **Files** tab and upload your project files or clone your GitHub repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/surplus-food-system.git
   ```
5. In the **Bash Console**, install the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
6. In the **Web** tab, configure the **WSGI configuration file**:
   ```python
   import sys
   path = '/home/YOUR_USERNAME/surplus_food_system'
   if path not in sys.path:
       sys.path.append(path)

   from app import app as application
   ```
7. Click the green **Reload** button.
8. Your app is live at: `https://YOUR_USERNAME.pythonanywhere.com`

---

## Method 3: Instant Live Exhibition Tunnel via ngrok (Fastest for College Presentation)

If you are presenting at a college exhibition booth and want **evaluators to scan a QR code and use the system immediately from their smartphones**:

### Steps:
1. Start your Flask application locally on your laptop:
   ```powershell
   cd C:\Users\Admin\.gemini\antigravity\scratch\surplus_food_system
   python app.py
   ```
   *(It runs on `http://127.0.0.1:5000`)*

2. In a second terminal window, run [ngrok](https://ngrok.com) or [localtunnel](https://localtunnel.me):
   ```bash
   npx localtunnel --port 5000
   ```
   *OR with ngrok:*
   ```bash
   ngrok http 5000
   ```

3. You will get an instant public URL:
   ```
   https://random-subdomain.loca.lt
   ```
4. Generate a free QR code using [qr-code-generator.com](https://www.qr-code-generator.com) pointing to this URL and paste it on your project poster or exhibition desk!
