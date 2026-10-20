"""
Authentication and Role-Based Access Control (RBAC) Module
Supports: Donor, NGO, Volunteer, and Admin roles with secure password hashing.
"""

from functools import wraps
from flask import session, redirect, url_for, flash, abort, g
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db

def hash_password(password):
    return generate_password_hash(password)

def verify_password(stored_hash, password):
    return check_password_hash(stored_hash, password)

def get_current_user():
    """Retrieve current logged in user from session and database."""
    if 'user_id' not in session:
        return None
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT id, name, email, role, org_name, phone, city, address, 
               donor_type, capacity_info, is_verified, is_active, created_at
        FROM users
        WHERE id = ? AND is_active = 1
    """, (session['user_id'],))
    user = c.fetchone()
    conn.close()
    return user

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please log in to continue.", "warning")
                return redirect(url_for('login'))
            user_role = session.get('role')
            if user_role not in allowed_roles:
                flash("You do not have permission to view or execute this action.", "danger")
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def donor_required(f):
    return role_required('donor', 'admin')(f)

def ngo_required(f):
    return role_required('ngo', 'volunteer', 'admin')(f)

def admin_required(f):
    return role_required('admin')(f)
