"""
Surplus Food Redistribution and Donation Management System
Flask Web Application
College Nirman Lab Project: "Data, Statistics & ML for Real India"
"""

import os
from datetime import datetime, timedelta
from flask import (
    Flask, render_template, request, redirect, url_for, 
    flash, session, jsonify, abort, g
)
from database import (
    get_db, check_and_expire_listings, log_status_change, 
    add_notification, get_system_summary_stats
)
from auth import (
    hash_password, verify_password, get_current_user,
    login_required, donor_required, ngo_required, admin_required
)
from urgency_engine import calculate_urgency_score, get_ml_model_metadata

app = Flask(__name__)
app.config['SECRET_KEY'] = 'nirman-lab-surplus-food-redistribution-secret-key-2026'

# Custom Jinja Template Filters
@app.template_filter('format_dt')
def format_datetime(value, format="%d %b %Y, %I:%M %p"):
    if not value:
        return "-"
    try:
        if isinstance(value, str):
            val_clean = value.replace('T', ' ')
            if len(val_clean) == 16:
                val_clean += ":00"
            dt = datetime.strptime(val_clean, "%Y-%m-%d %H:%M:%S")
        else:
            dt = value
        return dt.strftime(format)
    except Exception:
        return value

@app.template_filter('badge_status')
def badge_status(status):
    mapping = {
        'AVAILABLE': 'bg-success',
        'ACCEPTED': 'bg-primary',
        'PICKED_UP': 'bg-warning text-dark',
        'DELIVERED': 'bg-info text-dark',
        'CANCELLED': 'bg-secondary',
        'EXPIRED': 'bg-dark',
        'REJECTED': 'bg-danger'
    }
    return mapping.get(status, 'bg-secondary')

@app.template_filter('urgency_badge')
def urgency_badge(level):
    mapping = {
        'CRITICAL': 'bg-danger',
        'HIGH': 'bg-warning text-dark',
        'MODERATE': 'bg-info text-dark',
        'STABLE': 'bg-success'
    }
    return mapping.get(level, 'bg-secondary')

@app.context_processor
def inject_global_data():
    """Injects current user and unread notification count across all templates."""
    user = get_current_user()
    unread_count = 0
    recent_notifications = []
    if user:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND is_read = 0", (user['id'],))
        unread_count = c.fetchone()[0]
        c.execute("""
            SELECT id, title, message, link, is_read, created_at 
            FROM notifications 
            WHERE user_id = ? 
            ORDER BY created_at DESC LIMIT 5
        """, (user['id'],))
        recent_notifications = c.fetchall()
        conn.close()

    return {
        'current_user': user,
        'unread_count': unread_count,
        'recent_notifications': recent_notifications,
        'now_year': datetime.now().year
    }

@app.before_request
def auto_check_expiries():
    # Keep database state accurate on every navigation
    if not request.path.startswith('/static'):
        check_and_expire_listings()

# -------------------------------------------------------------
# PUBLIC ROUTES
# -------------------------------------------------------------

@app.route('/')
def index():
    stats = get_system_summary_stats()
    conn = get_db()
    c = conn.cursor()
    # Fetch top 3 urgent available listings for home page preview
    c.execute("""
        SELECT d.*, u.name as donor_name, u.org_name as donor_org
        FROM donations d
        JOIN users u ON d.donor_id = u.id
        WHERE d.status = 'AVAILABLE'
        ORDER BY d.urgency_score DESC, d.pickup_deadline ASC
        LIMIT 3
    """)
    urgent_donations = c.fetchall()
    conn.close()
    return render_template('index.html', stats=stats, urgent_donations=urgent_donations)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash("Please provide both email and password.", "danger")
            return redirect(url_for('login'))

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = c.fetchone()
        conn.close()

        if user and verify_password(user['password_hash'], password):
            if not user['is_active']:
                flash("Your account has been deactivated. Please contact the administrator.", "danger")
                return redirect(url_for('login'))
            
            session.clear()
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['name'] = user['name']

            flash(f"Welcome back, {user['name']}!", "success")
            if user['role'] == 'donor':
                return redirect(url_for('donor_dashboard'))
            elif user['role'] in ('ngo', 'volunteer'):
                return redirect(url_for('ngo_dashboard'))
            elif user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('index'))
        else:
            flash("Invalid email or password credentials. Please try again.", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/demo-login/<role>')
def demo_login(role):
    """Convenient 1-click evaluator login helper for testing."""
    role_map = {
        'admin': 'admin@nirman.edu',
        'donor': 'donor.spice@gmail.com',
        'ngo': 'ngo.annaseva@gmail.com',
        'volunteer': 'rahul.volunteer@gmail.com'
    }
    email = role_map.get(role)
    if not email:
        flash("Invalid demo role specified.", "warning")
        return redirect(url_for('login'))

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    conn.close()

    if user:
        session.clear()
        session['user_id'] = user['id']
        session['role'] = user['role']
        session['name'] = user['name']
        flash(f"Logged in via Demo Mode as {user['name']} ({user['role'].upper()}).", "info")
        if user['role'] == 'donor':
            return redirect(url_for('donor_dashboard'))
        elif user['role'] in ('ngo', 'volunteer'):
            return redirect(url_for('ngo_dashboard'))
        elif user['role'] == 'admin':
            return redirect(url_for('admin_dashboard'))
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('login'))

# -------------------------------------------------------------
# REGISTRATION MODULES
# -------------------------------------------------------------

@app.route('/register/donor', methods=['GET', 'POST'])
def register_donor():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        org_name = request.form.get('org_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        donor_type = request.form.get('donor_type', 'Restaurant')
        city = request.form.get('city', '').strip()
        address = request.form.get('address', '').strip()

        # Validation
        if not (name and email and phone and password and city and address):
            flash("Please complete all required fields.", "danger")
            return redirect(url_for('register_donor'))

        if '@' not in email or '.' not in email:
            flash("Please enter a valid email address.", "danger")
            return redirect(url_for('register_donor'))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('register_donor'))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return redirect(url_for('register_donor'))

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE email = ?", (email,))
        if c.fetchone():
            conn.close()
            flash("An account with this email address already exists.", "warning")
            return redirect(url_for('register_donor'))

        hashed = hash_password(password)
        c.execute("""
            INSERT INTO users (name, email, password_hash, role, org_name, phone, city, address, donor_type, is_verified, is_active)
            VALUES (?, ?, ?, 'donor', ?, ?, ?, ?, ?, 1, 1)
        """, (name, email, hashed, org_name, phone, city, address, donor_type))
        user_id = c.lastrowid

        add_notification(conn, user_id, None, "Welcome to Surplus Food System!", "Your donor account is active. You can now post surplus food listings.")
        conn.commit()
        conn.close()

        flash("Donor registration successful! Please log in to publish surplus food.", "success")
        return redirect(url_for('login'))

    return render_template('register_donor.html')

@app.route('/register/ngo', methods=['GET', 'POST'])
def register_ngo():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        contact_person = request.form.get('contact_person', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        user_type = request.form.get('user_type', 'ngo') # 'ngo' or 'volunteer'
        city = request.form.get('city', '').strip()
        address = request.form.get('address', '').strip()
        capacity_info = request.form.get('capacity_info', '').strip()

        if not (name and contact_person and email and phone and password and city):
            flash("Please fill in all mandatory fields.", "danger")
            return redirect(url_for('register_ngo'))

        if '@' not in email or '.' not in email:
            flash("Please enter a valid email format.", "danger")
            return redirect(url_for('register_ngo'))

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('register_ngo'))

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE email = ?", (email,))
        if c.fetchone():
            conn.close()
            flash("An account with this email is already registered.", "warning")
            return redirect(url_for('register_ngo'))

        # By requirement: Mark as unverified (is_verified = 0) so admin reviews before authorization
        hashed = hash_password(password)
        c.execute("""
            INSERT INTO users (name, email, password_hash, role, org_name, phone, city, address, capacity_info, is_verified, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 1)
        """, (contact_person, email, hashed, user_type, name, phone, city, address, capacity_info))
        user_id = c.lastrowid

        # Notify administrator
        c.execute("SELECT id FROM users WHERE role = 'admin'")
        admins = c.fetchall()
        for a in admins:
            add_notification(conn, a['id'], None, "New NGO Verification Request", f"New {user_type.upper()} registered: '{name}'. Verification required.", "/admin/users")

        add_notification(conn, user_id, None, "Account Pending Verification", "Your registration is submitted. An administrator will verify your credentials shortly.", None)

        conn.commit()
        conn.close()

        flash("Registration submitted! For safety, NGO & Volunteer accounts undergo admin verification before accepting food. You may log in now.", "info")
        return redirect(url_for('login'))

    return render_template('register_ngo.html')

# -------------------------------------------------------------
# DONOR MODULE
# -------------------------------------------------------------

@app.route('/donor/dashboard')
@donor_required
def donor_dashboard():
    user = get_current_user()
    conn = get_db()
    c = conn.cursor()

    # Donor specific metrics
    c.execute("SELECT COUNT(*) FROM donations WHERE donor_id = ?", (user['id'],))
    total_listed = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM donations WHERE donor_id = ? AND status = 'AVAILABLE'", (user['id'],))
    total_available = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM donations WHERE donor_id = ? AND status = 'ACCEPTED'", (user['id'],))
    total_accepted = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM donations WHERE donor_id = ? AND status = 'PICKED_UP'", (user['id'],))
    total_picked_up = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM donations WHERE donor_id = ? AND status = 'DELIVERED'", (user['id'],))
    total_delivered = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM donations WHERE donor_id = ? AND status IN ('CANCELLED', 'EXPIRED')", (user['id'],))
    total_inactive = c.fetchone()[0]

    # Filter by status if query parameter present
    filter_status = request.args.get('status', 'ALL')
    if filter_status and filter_status != 'ALL':
        c.execute("""
            SELECT d.*, u.name as recipient_name, u.org_name as recipient_org
            FROM donations d
            LEFT JOIN users u ON d.recipient_id = u.id
            WHERE d.donor_id = ? AND d.status = ?
            ORDER BY d.created_at DESC
        """, (user['id'], filter_status))
    else:
        c.execute("""
            SELECT d.*, u.name as recipient_name, u.org_name as recipient_org
            FROM donations d
            LEFT JOIN users u ON d.recipient_id = u.id
            WHERE d.donor_id = ?
            ORDER BY d.created_at DESC
        """, (user['id'],))
    
    donations = c.fetchall()
    conn.close()

    metrics = {
        'total_listed': total_listed,
        'total_available': total_available,
        'total_accepted': total_accepted,
        'total_picked_up': total_picked_up,
        'total_delivered': total_delivered,
        'total_inactive': total_inactive
    }

    return render_template('donor/dashboard.html', metrics=metrics, donations=donations, filter_status=filter_status)

@app.route('/donor/donations/new', methods=['GET', 'POST'])
@donor_required
def add_donation():
    user = get_current_user()
    if request.method == 'POST':
        food_name = request.form.get('food_name', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'Cooked Meals')
        quantity_str = request.form.get('quantity', '0')
        quantity_unit = request.form.get('quantity_unit', 'servings')
        preparation_time = request.form.get('preparation_time', '')
        storage_condition = request.form.get('storage_condition', 'Room Temperature')
        pickup_address = request.form.get('pickup_address', '').strip()
        city = request.form.get('city', '').strip()
        available_from = request.form.get('available_from', '')
        pickup_deadline = request.form.get('pickup_deadline', '')
        allergen_info = request.form.get('allergen_info', '').strip()
        handling_instructions = request.form.get('handling_instructions', '').strip()
        image_url = request.form.get('image_url', '').strip()
        safety_agreement = request.form.get('safety_agreement')

        # Mandatory checks
        if not (food_name and pickup_address and city and pickup_deadline and safety_agreement):
            flash("Please complete all mandatory fields and confirm the food safety declaration.", "danger")
            return redirect(url_for('add_donation'))

        try:
            quantity = float(quantity_str)
            if quantity <= 0:
                flash("Quantity must be greater than zero.", "danger")
                return redirect(url_for('add_donation'))
        except ValueError:
            flash("Please enter a valid numeric quantity.", "danger")
            return redirect(url_for('add_donation'))

        # Pickup deadline validation
        now = datetime.now()
        try:
            deadline_dt = datetime.strptime(pickup_deadline.replace('T', ' '), "%Y-%m-%d %H:%M")
            if deadline_dt <= now:
                flash("Pickup deadline must be a future date and time.", "danger")
                return redirect(url_for('add_donation'))
        except ValueError:
            pass # Form datetime formats vary; fallback to string

        if not available_from:
            available_from = now.strftime('%Y-%m-%d %H:%M:%S')

        # Default fallback image if none provided
        if not image_url:
            default_images = {
                'Cooked Meals': 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=500&auto=format&fit=crop&q=60',
                'Bakery Items': 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500&auto=format&fit=crop&q=60',
                'Fruits': 'https://images.unsplash.com/photo-1619566636858-adf3ef46400b?w=500&auto=format&fit=crop&q=60',
                'Vegetables': 'https://images.unsplash.com/photo-1540420773420-3366772f4999?w=500&auto=format&fit=crop&q=60',
                'Packaged Food': 'https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=500&auto=format&fit=crop&q=60',
                'Other': 'https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=500&auto=format&fit=crop&q=60'
            }
            image_url = default_images.get(category, default_images['Other'])

        # Calculate Urgency Score
        score, level, _ = calculate_urgency_score(category, storage_condition, pickup_deadline, quantity, quantity_unit)

        conn = get_db()
        c = conn.cursor()
        c.execute("""
            INSERT INTO donations (
                donor_id, food_name, description, category, quantity, quantity_unit,
                preparation_time, storage_condition, pickup_address, city, available_from, pickup_deadline,
                allergen_info, handling_instructions, image_url, donor_contact_shared, safety_agreement,
                status, urgency_score, urgency_level, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1, 'AVAILABLE', ?, ?, ?, ?)
        """, (
            user['id'], food_name, description, category, quantity, quantity_unit,
            preparation_time if preparation_time else None, storage_condition, pickup_address, city,
            available_from, pickup_deadline, allergen_info, handling_instructions, image_url,
            score, level, now.strftime('%Y-%m-%d %H:%M:%S'), now.strftime('%Y-%m-%d %H:%M:%S')
        ))
        donation_id = c.lastrowid

        # Record Status History Audit Log
        log_status_change(conn, donation_id, None, 'AVAILABLE', user['id'], 'Listing published by donor.')

        # In-app notification for donor
        add_notification(conn, user['id'], donation_id, "Donation Listed", f"'{food_name}' has been listed. Authorized NGOs in {city} can now claim it.", f"/donations/{donation_id}")

        # Notify active verified NGOs in that city
        c.execute("SELECT id FROM users WHERE role IN ('ngo', 'volunteer') AND is_verified = 1 AND LOWER(city) = LOWER(?)", (city,))
        recipients = c.fetchall()
        for r in recipients:
            add_notification(conn, r['id'], donation_id, "New Food Donation Alert", f"New {category} ({quantity} {quantity_unit}) listed in {city}: '{food_name}'.", f"/donations/{donation_id}")

        conn.commit()
        conn.close()

        flash("Surplus food listing published successfully! Verified NGOs have been notified.", "success")
        return redirect(url_for('donor_dashboard'))

    return render_template('donor/add_donation.html')

@app.route('/donor/donations/<int:id>/edit', methods=['GET', 'POST'])
@donor_required
def edit_donation(id):
    user = get_current_user()
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM donations WHERE id = ?", (id,))
    donation = c.fetchone()

    if not donation:
        conn.close()
        flash("Donation listing not found.", "danger")
        return redirect(url_for('donor_dashboard'))

    # Only listing owner or admin can edit
    if donation['donor_id'] != user['id'] and user['role'] != 'admin':
        conn.close()
        flash("You are not authorized to edit this listing.", "danger")
        return redirect(url_for('donor_dashboard'))

    # Can only edit if still AVAILABLE
    if donation['status'] != 'AVAILABLE':
        conn.close()
        flash("Only listings with 'AVAILABLE' status can be edited.", "warning")
        return redirect(url_for('view_donation', id=id))

    if request.method == 'POST':
        food_name = request.form.get('food_name', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category')
        quantity_str = request.form.get('quantity')
        quantity_unit = request.form.get('quantity_unit')
        storage_condition = request.form.get('storage_condition')
        pickup_address = request.form.get('pickup_address', '').strip()
        city = request.form.get('city', '').strip()
        pickup_deadline = request.form.get('pickup_deadline')
        allergen_info = request.form.get('allergen_info', '').strip()
        handling_instructions = request.form.get('handling_instructions', '').strip()
        image_url = request.form.get('image_url', '').strip()

        try:
            quantity = float(quantity_str)
        except ValueError:
            quantity = donation['quantity']

        # Recompute urgency score
        score, level, _ = calculate_urgency_score(category, storage_condition, pickup_deadline, quantity, quantity_unit)
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        c.execute("""
            UPDATE donations
            SET food_name = ?, description = ?, category = ?, quantity = ?, quantity_unit = ?,
                storage_condition = ?, pickup_address = ?, city = ?, pickup_deadline = ?,
                allergen_info = ?, handling_instructions = ?, image_url = ?,
                urgency_score = ?, urgency_level = ?, updated_at = ?
            WHERE id = ?
        """, (
            food_name, description, category, quantity, quantity_unit,
            storage_condition, pickup_address, city, pickup_deadline,
            allergen_info, handling_instructions, image_url or donation['image_url'],
            score, level, now_str, id
        ))

        log_status_change(conn, id, 'AVAILABLE', 'AVAILABLE', user['id'], 'Listing details updated by donor.')
        conn.commit()
        conn.close()

        flash("Donation listing updated successfully.", "success")
        return redirect(url_for('view_donation', id=id))

    conn.close()
    return render_template('donor/edit_donation.html', donation=donation)

@app.route('/donor/donations/<int:id>/cancel', methods=['POST'])
@donor_required
def cancel_donation(id):
    user = get_current_user()
    reason = request.form.get('reason', 'Cancelled by donor').strip()
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM donations WHERE id = ?", (id,))
    donation = c.fetchone()

    if not donation:
        conn.close()
        flash("Donation not found.", "danger")
        return redirect(url_for('donor_dashboard'))

    if donation['donor_id'] != user['id'] and user['role'] != 'admin':
        conn.close()
        flash("You are not authorized to cancel this donation.", "danger")
        return redirect(url_for('donor_dashboard'))

    if donation['status'] not in ('AVAILABLE', 'ACCEPTED'):
        conn.close()
        flash(f"Cannot cancel a donation with status '{donation['status']}'.", "warning")
        return redirect(url_for('view_donation', id=id))

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("""
        UPDATE donations
        SET status = 'CANCELLED', cancelled_at = ?, updated_at = ?
        WHERE id = ?
    """, (now_str, now_str, id))

    log_status_change(conn, id, donation['status'], 'CANCELLED', user['id'], f"Cancelled: {reason}")

    # Notify recipient if it was already accepted
    if donation['recipient_id']:
        add_notification(conn, donation['recipient_id'], id, "Donation Cancelled by Donor", f"The donation '{donation['food_name']}' was cancelled by the donor. Reason: {reason}", f"/donations/{id}")

    add_notification(conn, donation['donor_id'], id, "Donation Cancelled", f"You cancelled listing '{donation['food_name']}'.", f"/donations/{id}")

    conn.commit()
    conn.close()

    flash("Donation has been cancelled.", "info")
    return redirect(url_for('donor_dashboard'))

# -------------------------------------------------------------
# NGO & VOLUNTEER MODULE
# -------------------------------------------------------------

@app.route('/ngo/dashboard')
@ngo_required
def ngo_dashboard():
    user = get_current_user()
    conn = get_db()
    c = conn.cursor()

    # User's activity stats
    c.execute("SELECT COUNT(*) FROM donations WHERE recipient_id = ? AND status = 'ACCEPTED'", (user['id'],))
    my_accepted = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM donations WHERE recipient_id = ? AND status = 'PICKED_UP'", (user['id'],))
    my_picked_up = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM donations WHERE recipient_id = ? AND status = 'DELIVERED'", (user['id'],))
    my_delivered = c.fetchone()[0]

    # Available count in system
    c.execute("SELECT COUNT(*) FROM donations WHERE status = 'AVAILABLE'")
    total_available = c.fetchone()[0]

    # Fetch active tasks (ACCEPTED or PICKED_UP assigned to this user)
    c.execute("""
        SELECT d.*, u.name as donor_name, u.org_name as donor_org, u.phone as donor_phone
        FROM donations d
        JOIN users u ON d.donor_id = u.id
        WHERE d.recipient_id = ? AND d.status IN ('ACCEPTED', 'PICKED_UP')
        ORDER BY d.pickup_deadline ASC
    """, (user['id'],))
    active_tasks = c.fetchall()

    # Urgent available listings in their service area or city
    c.execute("""
        SELECT d.*, u.name as donor_name, u.org_name as donor_org
        FROM donations d
        JOIN users u ON d.donor_id = u.id
        WHERE d.status = 'AVAILABLE'
        ORDER BY d.urgency_score DESC, d.pickup_deadline ASC
        LIMIT 4
    """)
    urgent_listings = c.fetchall()

    conn.close()

    metrics = {
        'my_accepted': my_accepted,
        'my_picked_up': my_picked_up,
        'my_delivered': my_delivered,
        'total_available': total_available
    }

    return render_template('ngo/dashboard.html', metrics=metrics, active_tasks=active_tasks, urgent_listings=urgent_listings)

@app.route('/available-food')
def available_food():
    # Publicly browsable, but acceptance requires verified NGO/volunteer login
    check_and_expire_listings()
    
    search_q = request.args.get('search', '').strip()
    category = request.args.get('category', 'ALL')
    city = request.args.get('city', 'ALL')
    sort_by = request.args.get('sort', 'urgency') # urgency, deadline, quantity

    conn = get_db()
    c = conn.cursor()

    query = """
        SELECT d.*, u.name as donor_name, u.org_name as donor_org, u.phone as donor_phone, u.donor_type
        FROM donations d
        JOIN users u ON d.donor_id = u.id
        WHERE d.status = 'AVAILABLE'
    """
    params = []

    if search_q:
        query += " AND (d.food_name LIKE ? OR d.description LIKE ? OR d.pickup_address LIKE ?)"
        wildcard = f"%{search_q}%"
        params.extend([wildcard, wildcard, wildcard])

    if category and category != 'ALL':
        query += " AND d.category = ?"
        params.append(category)

    if city and city != 'ALL':
        query += " AND LOWER(d.city) = LOWER(?)"
        params.append(city)

    # Sorting
    if sort_by == 'deadline':
        query += " ORDER BY d.pickup_deadline ASC"
    elif sort_by == 'quantity':
        query += " ORDER BY d.quantity DESC"
    else: # urgency (default)
        query += " ORDER BY d.urgency_score DESC, d.pickup_deadline ASC"

    c.execute(query, params)
    donations = c.fetchall()

    # Get distinct cities for filter dropdown
    c.execute("SELECT DISTINCT city FROM donations WHERE status = 'AVAILABLE'")
    cities = [r['city'] for r in c.fetchall()]

    conn.close()

    return render_template(
        'ngo/available.html',
        donations=donations,
        search_q=search_q,
        current_category=category,
        current_city=city,
        current_sort=sort_by,
        cities=cities
    )

@app.route('/donations/<int:id>/accept', methods=['POST'])
@ngo_required
def accept_donation(id):
    user = get_current_user()

    # NGO verification safeguard: Unverified accounts cannot accept food
    if not user['is_verified'] and user['role'] != 'admin':
        flash("Your account is currently pending administrator verification. Unverified accounts cannot accept donations.", "warning")
        return redirect(url_for('view_donation', id=id))

    conn = get_db()
    c = conn.cursor()

    # Safeguard against race conditions: Transaction with row-level verification
    c.execute("SELECT * FROM donations WHERE id = ?", (id,))
    donation = c.fetchone()

    if not donation:
        conn.close()
        flash("Donation listing not found.", "danger")
        return redirect(url_for('available_food'))

    if donation['status'] != 'AVAILABLE':
        conn.close()
        flash(f"This donation is no longer available (Current status: {donation['status']}).", "warning")
        return redirect(url_for('available_food'))

    # Check deadline
    now = datetime.now()
    try:
        deadline_dt = datetime.strptime(donation['pickup_deadline'].replace('T', ' ')[:19], "%Y-%m-%d %H:%M:%S")
        if deadline_dt <= now:
            c.execute("UPDATE donations SET status = 'EXPIRED' WHERE id = ?", (id,))
            conn.commit()
            conn.close()
            flash("This donation has expired and cannot be accepted.", "danger")
            return redirect(url_for('available_food'))
    except Exception:
        pass

    now_str = now.strftime('%Y-%m-%d %H:%M:%S')

    # Atomically accept donation
    c.execute("""
        UPDATE donations
        SET status = 'ACCEPTED', recipient_id = ?, accepted_at = ?, updated_at = ?
        WHERE id = ? AND status = 'AVAILABLE'
    """, (user['id'], now_str, now_str, id))

    if c.rowcount == 0:
        conn.close()
        flash("Another NGO or volunteer just accepted this donation.", "warning")
        return redirect(url_for('available_food'))

    # Audit history
    log_status_change(conn, id, 'AVAILABLE', 'ACCEPTED', user['id'], f"Accepted by {user['org_name'] or user['name']} ({user['role'].upper()}).")

    # Notifications
    org_or_name = user['org_name'] or user['name']
    add_notification(conn, donation['donor_id'], id, "Donation Accepted!", f"{org_or_name} has accepted your donation '{donation['food_name']}'. Please prepare for pickup.", f"/donations/{id}")
    add_notification(conn, user['id'], id, "Donation Claim Confirmed", f"You accepted '{donation['food_name']}'. Pickup address: {donation['pickup_address']}, {donation['city']}.", f"/donations/{id}")

    conn.commit()
    conn.close()

    flash(f"Successfully accepted donation '{donation['food_name']}'. Please review pickup location and proceed.", "success")
    return redirect(url_for('view_donation', id=id))

@app.route('/donations/<int:id>/pickup', methods=['POST'])
@ngo_required
def confirm_pickup(id):
    user = get_current_user()
    notes = request.form.get('notes', 'Food collected in good condition.').strip()
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM donations WHERE id = ?", (id,))
    donation = c.fetchone()

    if not donation:
        conn.close()
        flash("Donation not found.", "danger")
        return redirect(url_for('ngo_dashboard'))

    # Check permission
    if donation['recipient_id'] != user['id'] and user['role'] != 'admin':
        conn.close()
        flash("Only the assigned recipient can mark this donation as picked up.", "danger")
        return redirect(url_for('view_donation', id=id))

    if donation['status'] != 'ACCEPTED':
        conn.close()
        flash(f"Invalid transition. Cannot mark as PICKED UP from current status '{donation['status']}'.", "warning")
        return redirect(url_for('view_donation', id=id))

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("""
        UPDATE donations
        SET status = 'PICKED_UP', picked_up_at = ?, updated_at = ?
        WHERE id = ?
    """, (now_str, now_str, id))

    log_status_change(conn, id, 'ACCEPTED', 'PICKED_UP', user['id'], f"Collection confirmed: {notes}")

    add_notification(conn, donation['donor_id'], id, "Food Collected", f"Your donation '{donation['food_name']}' has been picked up by {user['name']}.", f"/donations/{id}")
    add_notification(conn, user['id'], id, "Pickup Recorded", f"Pickup recorded for '{donation['food_name']}'. Please confirm delivery once distributed.", f"/donations/{id}")

    conn.commit()
    conn.close()

    flash("Food pickup confirmed! Donation status changed to PICKED UP.", "success")
    return redirect(url_for('view_donation', id=id))

@app.route('/donations/<int:id>/deliver', methods=['POST'])
@ngo_required
def confirm_delivery(id):
    user = get_current_user()
    delivery_notes = request.form.get('notes', 'Delivered and distributed to community beneficiaries.').strip()
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM donations WHERE id = ?", (id,))
    donation = c.fetchone()

    if not donation:
        conn.close()
        flash("Donation not found.", "danger")
        return redirect(url_for('ngo_dashboard'))

    if donation['recipient_id'] != user['id'] and user['role'] != 'admin':
        conn.close()
        flash("Only the assigned recipient can mark this donation as delivered.", "danger")
        return redirect(url_for('view_donation', id=id))

    # Crucial workflow guard: Prevent DELIVERED before PICKED_UP
    if donation['status'] != 'PICKED_UP':
        conn.close()
        flash(f"A donation must be marked as 'PICKED UP' before it can be marked as 'DELIVERED'. Current: {donation['status']}", "warning")
        return redirect(url_for('view_donation', id=id))

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("""
        UPDATE donations
        SET status = 'DELIVERED', delivered_at = ?, updated_at = ?
        WHERE id = ?
    """, (now_str, now_str, id))

    log_status_change(conn, id, 'PICKED_UP', 'DELIVERED', user['id'], f"Delivery confirmed: {delivery_notes}")

    add_notification(conn, donation['donor_id'], id, "Donation Successfully Delivered!", f"Your donation '{donation['food_name']}' reached people in need! Thank you for reducing food waste.", f"/donations/{id}")
    add_notification(conn, user['id'], id, "Delivery Completed", f"Successfully recorded distribution of '{donation['food_name']}'.", f"/donations/{id}")

    conn.commit()
    conn.close()

    flash("Outstanding! Donation has been marked as DELIVERED.", "success")
    return redirect(url_for('view_donation', id=id))

# -------------------------------------------------------------
# DONATION DETAILS & SAFETY REPORTING
# -------------------------------------------------------------

@app.route('/donations/<int:id>')
def view_donation(id):
    conn = get_db()
    c = conn.cursor()

    c.execute("""
        SELECT d.*, 
               u_d.name as donor_name, u_d.org_name as donor_org, u_d.email as donor_email, u_d.phone as donor_phone, u_d.donor_type,
               u_r.name as recipient_name, u_r.org_name as recipient_org, u_r.email as recipient_email, u_r.phone as recipient_phone, u_r.role as recipient_role
        FROM donations d
        JOIN users u_d ON d.donor_id = u_d.id
        LEFT JOIN users u_r ON d.recipient_id = u_r.id
        WHERE d.id = ?
    """, (id,))
    donation = c.fetchone()

    if not donation:
        conn.close()
        flash("Donation listing not found.", "danger")
        return redirect(url_for('index'))

    # Status history audit logs
    c.execute("""
        SELECT sh.*, u.name as user_name, u.role as user_role, u.org_name
        FROM donation_status_history sh
        JOIN users u ON sh.changed_by_user_id = u.id
        WHERE sh.donation_id = ?
        ORDER BY sh.created_at ASC
    """, (id,))
    history = c.fetchall()

    # Safety reports on this donation
    c.execute("""
        SELECT sr.*, u.name as reporter_name
        FROM safety_reports sr
        JOIN users u ON sr.reported_by_user_id = u.id
        WHERE sr.donation_id = ?
        ORDER BY sr.created_at DESC
    """, (id,))
    safety_reports = c.fetchall()

    conn.close()
    return render_template('donations/detail.html', donation=donation, history=history, safety_reports=safety_reports)

@app.route('/donations/<int:id>/report-safety', methods=['POST'])
@login_required
def report_safety(id):
    user = get_current_user()
    reason = request.form.get('reason', 'Suspected Spoilage')
    details = request.form.get('details', '').strip()

    if not details:
        flash("Please provide specific details regarding the food safety concern.", "danger")
        return redirect(url_for('view_donation', id=id))

    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO safety_reports (donation_id, reported_by_user_id, reason, details, status)
        VALUES (?, ?, ?, ?, 'PENDING')
    """, (id, user['id'], reason, details))

    # Notify administrators
    c.execute("SELECT id FROM users WHERE role = 'admin'")
    admins = c.fetchall()
    for a in admins:
        add_notification(conn, a['id'], id, "Food Safety Alert Flagged", f"Safety report filed for donation #{id}: '{reason}'. Review required.", "/admin/safety-reports")

    conn.commit()
    conn.close()

    flash("Food safety report submitted to administrators for inspection. Thank you for maintaining safety standards.", "warning")
    return redirect(url_for('view_donation', id=id))

# -------------------------------------------------------------
# NOTIFICATIONS MODULE
# -------------------------------------------------------------

@app.route('/notifications')
@login_required
def notifications_page():
    user = get_current_user()
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM notifications 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    """, (user['id'],))
    all_notifications = c.fetchall()
    conn.close()
    return render_template('notifications.html', notifications=all_notifications)

@app.route('/notifications/<int:id>/read', methods=['POST'])
@login_required
def mark_notification_read(id):
    user = get_current_user()
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE notifications SET is_read = 1 WHERE id = ? AND user_id = ?", (id, user['id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    user = get_current_user()
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE notifications SET is_read = 1 WHERE user_id = ?", (user['id'],))
    conn.commit()
    conn.close()
    flash("All notifications marked as read.", "info")
    return redirect(url_for('notifications_page'))

# -------------------------------------------------------------
# ADMINISTRATOR MODULE & ANALYTICS
# -------------------------------------------------------------

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    stats = get_system_summary_stats()
    conn = get_db()
    c = conn.cursor()

    # Pending NGO verification count
    c.execute("SELECT COUNT(*) FROM users WHERE role IN ('ngo', 'volunteer') AND is_verified = 0")
    pending_verifications = c.fetchone()[0]

    # Pending Safety Reports count
    c.execute("SELECT COUNT(*) FROM safety_reports WHERE status = 'PENDING'")
    pending_safety = c.fetchone()[0]

    # Recent safety concerns
    c.execute("""
        SELECT sr.*, d.food_name, u.name as reporter_name
        FROM safety_reports sr
        JOIN donations d ON sr.donation_id = d.id
        JOIN users u ON sr.reported_by_user_id = u.id
        ORDER BY sr.created_at DESC LIMIT 5
    """)
    recent_safety = c.fetchall()

    # Recent donations
    c.execute("""
        SELECT d.*, u.name as donor_name, u.org_name as donor_org
        FROM donations d
        JOIN users u ON d.donor_id = u.id
        ORDER BY d.created_at DESC LIMIT 6
    """)
    recent_donations = c.fetchall()

    conn.close()

    return render_template(
        'admin/dashboard.html',
        stats=stats,
        pending_verifications=pending_verifications,
        pending_safety=pending_safety,
        recent_safety=recent_safety,
        recent_donations=recent_donations
    )

@app.route('/admin/users')
@admin_required
def admin_users():
    role_filter = request.args.get('role', 'ALL')
    search_q = request.args.get('search', '').strip()

    conn = get_db()
    c = conn.cursor()

    query = "SELECT * FROM users WHERE 1=1"
    params = []

    if role_filter and role_filter != 'ALL':
        query += " AND role = ?"
        params.append(role_filter)

    if search_q:
        query += " AND (name LIKE ? OR email LIKE ? OR org_name LIKE ? OR city LIKE ?)"
        wildcard = f"%{search_q}%"
        params.extend([wildcard, wildcard, wildcard, wildcard])

    query += " ORDER BY created_at DESC"
    c.execute(query, params)
    users = c.fetchall()
    conn.close()

    return render_template('admin/users.html', users=users, current_role=role_filter, search_q=search_q)

@app.route('/admin/users/<int:id>/verify', methods=['POST'])
@admin_required
def admin_verify_user(id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name, email, role FROM users WHERE id = ?", (id,))
    u = c.fetchone()
    if u:
        c.execute("UPDATE users SET is_verified = 1 WHERE id = ?", (id,))
        add_notification(conn, id, None, "Account Verified!", "An administrator has verified your organization. You are now authorized to accept and collect food donations.", "/available-food")
        conn.commit()
        flash(f"User '{u['name']}' has been officially verified.", "success")
    conn.close()
    return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:id>/toggle-active', methods=['POST'])
@admin_required
def admin_toggle_user(id):
    user = get_current_user()
    if id == user['id']:
        flash("You cannot deactivate your own administrator account.", "danger")
        return redirect(url_for('admin_users'))

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT name, is_active FROM users WHERE id = ?", (id,))
    u = c.fetchone()
    if u:
        new_val = 0 if u['is_active'] else 1
        c.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_val, id))
        conn.commit()
        status_label = "activated" if new_val else "deactivated"
        flash(f"Account '{u['name']}' has been {status_label}.", "info")
    conn.close()
    return redirect(url_for('admin_users'))

@app.route('/admin/donations')
@admin_required
def admin_donations():
    status_filter = request.args.get('status', 'ALL')
    category_filter = request.args.get('category', 'ALL')
    search_q = request.args.get('search', '').strip()

    conn = get_db()
    c = conn.cursor()

    query = """
        SELECT d.*, 
               u_d.name as donor_name, u_d.org_name as donor_org,
               u_r.name as recipient_name, u_r.org_name as recipient_org
        FROM donations d
        JOIN users u_d ON d.donor_id = u_d.id
        LEFT JOIN users u_r ON d.recipient_id = u_r.id
        WHERE 1=1
    """
    params = []

    if status_filter and status_filter != 'ALL':
        query += " AND d.status = ?"
        params.append(status_filter)

    if category_filter and category_filter != 'ALL':
        query += " AND d.category = ?"
        params.append(category_filter)

    if search_q:
        query += " AND (d.food_name LIKE ? OR d.id = ? OR d.city LIKE ?)"
        wildcard = f"%{search_q}%"
        try:
            int_id = int(search_q)
        except ValueError:
            int_id = -1
        params.extend([wildcard, int_id, wildcard])

    query += " ORDER BY d.created_at DESC"
    c.execute(query, params)
    donations = c.fetchall()
    conn.close()

    return render_template(
        'admin/donations.html', 
        donations=donations, 
        current_status=status_filter, 
        current_category=category_filter, 
        search_q=search_q
    )

@app.route('/admin/donations/<int:id>/remove', methods=['POST'])
@admin_required
def admin_remove_donation(id):
    admin = get_current_user()
    reason = request.form.get('reason', 'Removed by administrator due to policy or safety concerns.').strip()
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM donations WHERE id = ?", (id,))
    donation = c.fetchone()

    if donation:
        c.execute("UPDATE donations SET status = 'REJECTED', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (id,))
        log_status_change(conn, id, donation['status'], 'REJECTED', admin['id'], f"Admin Removal: {reason}")
        add_notification(conn, donation['donor_id'], id, "Listing Moderated / Removed", f"Your listing '{donation['food_name']}' was removed by an administrator. Reason: {reason}", f"/donations/{id}")
        conn.commit()
        flash(f"Donation #{id} has been removed/rejected.", "warning")
    conn.close()
    return redirect(url_for('admin_donations'))

@app.route('/admin/safety-reports')
@admin_required
def admin_safety_reports():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT sr.*, d.food_name, d.status as donation_status,
               u_rep.name as reporter_name, u_rep.role as reporter_role,
               u_don.name as donor_name, u_don.org_name as donor_org
        FROM safety_reports sr
        JOIN donations d ON sr.donation_id = d.id
        JOIN users u_rep ON sr.reported_by_user_id = u_rep.id
        JOIN users u_don ON d.donor_id = u_don.id
        ORDER BY sr.created_at DESC
    """)
    reports = c.fetchall()
    conn.close()
    return render_template('admin/safety_reports.html', reports=reports)

@app.route('/admin/safety-reports/<int:id>/resolve', methods=['POST'])
@admin_required
def admin_resolve_safety(id):
    admin = get_current_user()
    action = request.form.get('action', 'DISMISS') # 'DISMISS' or 'REMOVE_LISTING'
    admin_notes = request.form.get('admin_notes', '').strip()

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM safety_reports WHERE id = ?", (id,))
    report = c.fetchone()

    if not report:
        conn.close()
        flash("Report not found.", "danger")
        return redirect(url_for('admin_safety_reports'))

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if action == 'REMOVE_LISTING':
        new_status = 'RESOLVED_REMOVED'
        # Mark donation as REJECTED
        c.execute("UPDATE donations SET status = 'REJECTED', updated_at = ? WHERE id = ?", (now_str, report['donation_id']))
        log_status_change(conn, report['donation_id'], 'ACTIVE', 'REJECTED', admin['id'], f"Removed following safety report #{id}: {admin_notes}")
    else:
        new_status = 'RESOLVED_DISMISSED'

    c.execute("""
        UPDATE safety_reports
        SET status = ?, admin_notes = ?, reviewed_at = ?, reviewed_by_user_id = ?
        WHERE id = ?
    """, (new_status, admin_notes, now_str, admin['id'], id))

    conn.commit()
    conn.close()

    flash("Safety report resolution recorded successfully.", "success")
    return redirect(url_for('admin_safety_reports'))

@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    stats = get_system_summary_stats()
    ml_metadata = get_ml_model_metadata()
    return render_template('admin/analytics.html', stats=stats, ml_metadata=ml_metadata)

@app.route('/api/analytics-data')
@admin_required
def api_analytics_data():
    """Provides structured JSON data for Chart.js renders."""
    conn = get_db()
    c = conn.cursor()

    # 1. Status Distribution
    c.execute("SELECT status, COUNT(*) as count FROM donations GROUP BY status")
    status_rows = c.fetchall()
    status_data = {r['status']: r['count'] for r in status_rows}

    # 2. Food Category Breakdown
    c.execute("SELECT category, COUNT(*) as count FROM donations GROUP BY category")
    category_rows = c.fetchall()
    category_data = {r['category']: r['count'] for r in category_rows}

    # 3. Geographic Distribution
    c.execute("SELECT city, COUNT(*) as count FROM donations GROUP BY city")
    city_rows = c.fetchall()
    city_data = {r['city']: r['count'] for r in city_rows}

    # 4. Unit-wise quantities (kg, servings, packages)
    c.execute("""
        SELECT quantity_unit,
               SUM(quantity) as total_listed,
               SUM(CASE WHEN status = 'DELIVERED' THEN quantity ELSE 0 END) as total_delivered
        FROM donations
        WHERE status != 'CANCELLED'
        GROUP BY quantity_unit
    """)
    unit_rows = c.fetchall()
    unit_comparison = []
    for r in unit_rows:
        unit_comparison.append({
            'unit': r['quantity_unit'],
            'listed': round(r['total_listed'] or 0, 1),
            'delivered': round(r['total_delivered'] or 0, 1)
        })

    conn.close()

    return jsonify({
        'status_data': status_data,
        'category_data': category_data,
        'city_data': city_data,
        'unit_comparison': unit_comparison
    })

# -------------------------------------------------------------
# ERROR HANDLERS
# -------------------------------------------------------------

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

# -------------------------------------------------------------
# AUTO-INITIALIZE DATABASE IF NOT PRESENT (FOR CLOUD DEPLOYMENTS)
# -------------------------------------------------------------
from database import DB_PATH, init_db
if not os.path.exists(DB_PATH):
    init_db()
    try:
        from seed_data import seed_all
        seed_all()
    except Exception as e:
        print(f"Warning during auto-seeding: {e}")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)
