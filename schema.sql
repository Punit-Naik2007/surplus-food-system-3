-- Surplus Food Redistribution and Donation Management System
-- Database Schema for SQLite

PRAGMA foreign_keys = ON;

-- Users Table (Donors, NGOs, Volunteers, Admins)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('donor', 'ngo', 'volunteer', 'admin')),
    org_name TEXT,
    phone TEXT NOT NULL,
    city TEXT NOT NULL,
    address TEXT,
    donor_type TEXT CHECK(donor_type IN ('Restaurant', 'Hotel', 'Canteen', 'Event Organizer', 'Household', 'Other', NULL)),
    capacity_info TEXT, -- e.g. "50-100 kg / 200 meals capacity"
    is_verified INTEGER NOT NULL DEFAULT 1, -- NGOs/volunteers start 0, Admin approves to 1
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Donations Table
CREATE TABLE IF NOT EXISTS donations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_id INTEGER NOT NULL,
    recipient_id INTEGER,
    food_name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL CHECK(category IN ('Cooked Meals', 'Fruits', 'Vegetables', 'Bakery Items', 'Packaged Food', 'Other')),
    quantity REAL NOT NULL CHECK(quantity > 0),
    quantity_unit TEXT NOT NULL CHECK(quantity_unit IN ('kg', 'servings', 'packages')),
    preparation_time TIMESTAMP,
    storage_condition TEXT NOT NULL CHECK(storage_condition IN ('Room Temperature', 'Refrigerated', 'Frozen', 'Insulated Container')),
    pickup_address TEXT NOT NULL,
    city TEXT NOT NULL,
    available_from TIMESTAMP NOT NULL,
    pickup_deadline TIMESTAMP NOT NULL,
    allergen_info TEXT,
    handling_instructions TEXT,
    image_url TEXT,
    donor_contact_shared INTEGER NOT NULL DEFAULT 1,
    safety_agreement INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'AVAILABLE' CHECK(status IN ('AVAILABLE', 'ACCEPTED', 'PICKED_UP', 'DELIVERED', 'CANCELLED', 'EXPIRED', 'REJECTED')),
    urgency_score REAL DEFAULT 0.0,
    urgency_level TEXT DEFAULT 'MODERATE',
    accepted_at TIMESTAMP,
    picked_up_at TIMESTAMP,
    delivered_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (donor_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (recipient_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Audit / Lifecycle Status History Table
CREATE TABLE IF NOT EXISTS donation_status_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donation_id INTEGER NOT NULL,
    from_status TEXT,
    to_status TEXT NOT NULL,
    changed_by_user_id INTEGER NOT NULL,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (donation_id) REFERENCES donations(id) ON DELETE CASCADE,
    FOREIGN KEY (changed_by_user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Food Safety Reports / Moderation Table
CREATE TABLE IF NOT EXISTS safety_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    donation_id INTEGER NOT NULL,
    reported_by_user_id INTEGER NOT NULL,
    reason TEXT NOT NULL CHECK(reason IN ('Suspected Spoilage', 'Improper Storage', 'Unsealed Package', 'Expired Before Pickup', 'Hygiene Concern', 'Other')),
    details TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING', 'INVESTIGATING', 'RESOLVED_REMOVED', 'RESOLVED_DISMISSED')),
    admin_notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    reviewed_by_user_id INTEGER,
    FOREIGN KEY (donation_id) REFERENCES donations(id) ON DELETE CASCADE,
    FOREIGN KEY (reported_by_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (reviewed_by_user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- In-App Notifications Table
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    donation_id INTEGER,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    is_read INTEGER NOT NULL DEFAULT 0,
    link TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (donation_id) REFERENCES donations(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_donations_status ON donations(status);
CREATE INDEX IF NOT EXISTS idx_donations_donor ON donations(donor_id);
CREATE INDEX IF NOT EXISTS idx_donations_recipient ON donations(recipient_id);
CREATE INDEX IF NOT EXISTS idx_donations_city ON donations(city);
CREATE INDEX IF NOT EXISTS idx_donations_deadline ON donations(pickup_deadline);
CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON notifications(user_id, is_read);
