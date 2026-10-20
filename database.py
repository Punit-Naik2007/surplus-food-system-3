import sqlite3
import os
from datetime import datetime

DATABASE_NAME = 'surplus_food.db'
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATABASE_NAME)

def get_db():
    """Establish and return a SQLite database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    """Initialize the SQLite database using schema.sql."""
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')
    with get_db() as conn:
        with open(schema_path, mode='r', encoding='utf-8') as f:
            conn.cursor().executescript(f.read())
        conn.commit()

def check_and_expire_listings():
    """
    Automated safety check: Mark any AVAILABLE donations whose pickup_deadline
    has passed as EXPIRED, with audit history and donor notification.
    """
    conn = get_db()
    cursor = conn.cursor()
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Find expired available listings
    cursor.execute("""
        SELECT id, donor_id, food_name, pickup_deadline
        FROM donations
        WHERE status = 'AVAILABLE' AND pickup_deadline < ?
    """, (now_str,))
    expired_items = cursor.fetchall()

    for item in expired_items:
        # Update donation status
        cursor.execute("""
            UPDATE donations
            SET status = 'EXPIRED', updated_at = ?
            WHERE id = ?
        """, (now_str, item['id']))
        
        # Log to status history (system automated change: changed_by donor or system 1)
        cursor.execute("""
            INSERT INTO donation_status_history (donation_id, from_status, to_status, changed_by_user_id, notes)
            VALUES (?, 'AVAILABLE', 'EXPIRED', ?, 'Automated system expiry: Pickup deadline passed.')
        """, (item['id'], item['donor_id']))
        
        # Notify donor
        cursor.execute("""
            INSERT INTO notifications (user_id, donation_id, title, message, link)
            VALUES (?, ?, 'Listing Expired', ?, ?)
        """, (
            item['donor_id'],
            item['id'],
            f"Your donation listing '{item['food_name']}' expired as the pickup deadline passed.",
            f"/donations/{item['id']}"
        ))

    conn.commit()
    conn.close()

def log_status_change(conn, donation_id, from_status, to_status, user_id, notes=""):
    """Insert a recorded audit entry into donation_status_history."""
    conn.execute("""
        INSERT INTO donation_status_history (donation_id, from_status, to_status, changed_by_user_id, notes)
        VALUES (?, ?, ?, ?, ?)
    """, (donation_id, from_status, to_status, user_id, notes))

def add_notification(conn, user_id, donation_id, title, message, link=None):
    """Create an in-app notification for a user."""
    conn.execute("""
        INSERT INTO notifications (user_id, donation_id, title, message, link)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, donation_id, title, message, link))

def get_system_summary_stats():
    """
    Compute rigorous system statistics.
    Units are separated to avoid invalid mathematical additions of kg and servings.
    Delivery rate: (Delivered / (Total Listed - Cancelled - Expired)) * 100
    or standard: (Delivered / Total Listed) * 100 with clear formula documented.
    """
    check_and_expire_listings()
    conn = get_db()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM donations")
    total_listed = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM donations WHERE status = 'AVAILABLE'")
    total_available = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM donations WHERE status = 'ACCEPTED'")
    total_accepted = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM donations WHERE status = 'PICKED_UP'")
    total_picked_up = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM donations WHERE status = 'DELIVERED'")
    total_delivered = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM donations WHERE status = 'CANCELLED'")
    total_cancelled = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM donations WHERE status = 'EXPIRED'")
    total_expired = c.fetchone()[0]

    # Quantity totals broken down strictly by unit to ensure scientific integrity
    c.execute("""
        SELECT quantity_unit, 
               SUM(quantity) as listed_qty,
               SUM(CASE WHEN status = 'DELIVERED' THEN quantity ELSE 0 END) as delivered_qty
        FROM donations
        WHERE status != 'CANCELLED'
        GROUP BY quantity_unit
    """)
    unit_rows = c.fetchall()
    unit_stats = {}
    for r in unit_rows:
        unit_stats[r['quantity_unit']] = {
            'listed': round(r['listed_qty'] or 0, 1),
            'delivered': round(r['delivered_qty'] or 0, 1)
        }

    # Users counts
    c.execute("SELECT COUNT(*) FROM users WHERE role = 'donor'")
    total_donors = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM users WHERE role IN ('ngo', 'volunteer')")
    total_ngos_volunteers = c.fetchone()[0]

    # Verified vs unverified NGOs
    c.execute("SELECT COUNT(*) FROM users WHERE role IN ('ngo', 'volunteer') AND is_verified = 1")
    verified_ngos = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM users WHERE role IN ('ngo', 'volunteer') AND is_verified = 0")
    pending_ngos = c.fetchone()[0]

    # Delivery Rate calculation:
    # Formula: (Delivered donations / Total Eligible non-cancelled/non-expired listed) * 100
    # Also calculate overall delivery rate: (Delivered / Total listed) * 100
    completed_or_in_progress = total_accepted + total_picked_up + total_delivered
    eligible_active_or_completed = total_listed - total_cancelled
    
    if eligible_active_or_completed > 0:
        delivery_rate = round((total_delivered / eligible_active_or_completed) * 100, 1)
    else:
        delivery_rate = 0.0

    conn.close()

    return {
        'total_listed': total_listed,
        'total_available': total_available,
        'total_accepted': total_accepted,
        'total_picked_up': total_picked_up,
        'total_delivered': total_delivered,
        'total_cancelled': total_cancelled,
        'total_expired': total_expired,
        'total_donors': total_donors,
        'total_ngos_volunteers': total_ngos_volunteers,
        'verified_ngos': verified_ngos,
        'pending_ngos': pending_ngos,
        'delivery_rate': delivery_rate,
        'unit_stats': unit_stats
    }
