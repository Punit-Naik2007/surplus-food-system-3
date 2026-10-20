"""
Database Seeding Script for Surplus Food Redistribution System
Provides rich, realistic sample data for Nirman Lab exhibition demonstration.
Calculates realistic timestamps relative to current runtime.
"""

from datetime import datetime, timedelta
from database import get_db, init_db
from auth import hash_password
from urgency_engine import calculate_urgency_score

def seed_all():
    init_db()
    conn = get_db()
    c = conn.cursor()

    # Clear existing data to ensure clean idempotency
    c.execute("DELETE FROM notifications")
    c.execute("DELETE FROM safety_reports")
    c.execute("DELETE FROM donation_status_history")
    c.execute("DELETE FROM donations")
    c.execute("DELETE FROM users")
    conn.commit()

    now = datetime.now()

    # 1. Insert Users
    users = [
        # (id, name, email, password, role, org_name, phone, city, address, donor_type, capacity_info, is_verified)
        (1, "Nirman Lab Administrator", "admin@nirman.edu", hash_password("Admin@123"), "admin",
         "Nirman Engineering Innovation Lab", "+91 99000 11223", "Bengaluru", "Campus Tech Block 4, Electronic City",
         None, None, 1),

        (2, "Chef Anand Verma", "donor.spice@gmail.com", hash_password("Donor@123"), "donor",
         "The Spice Garden Restaurant", "+91 98765 43210", "Bengaluru", "12th Main, Indiranagar, Bengaluru - 560038",
         "Restaurant", None, 1),

        (3, "Vikram Malhotra", "donor.orchid@gmail.com", hash_password("Donor@123"), "donor",
         "Grand Orchid Convention Center", "+91 98765 11223", "Bengaluru", "Bellary Road, Near Hebbal Flyover, Bengaluru",
         "Event Organizer", None, 1),

        (4, "Sunita Rao", "donor.bakery@gmail.com", hash_password("Donor@123"), "donor",
         "Fresh Daily Artisan Bakery", "+91 98765 33445", "Bengaluru", "7th Cross, Koramangala 4th Block, Bengaluru",
         "Canteen", None, 1),

        (5, "Rajesh Singhania", "donor.market@gmail.com", hash_password("Donor@123"), "donor",
         "Green Valley Organic Supermarket", "+91 98765 77889", "Mumbai", "Linking Road, Bandra West, Mumbai - 400050",
         "Other", None, 1),

        (6, "Sister Teresa / Ramesh", "ngo.annaseva@gmail.com", hash_password("Ngo@123"), "ngo",
         "Anna Seva Feeding Foundation", "+91 98450 12345", "Bengaluru", "Koramangala Community Hall Road, Bengaluru",
         None, "Daily capacity: 300 meals / 80 kg", 1),

        (7, "Farhan Merchant", "ngo.rotibank@gmail.com", hash_password("Ngo@123"), "ngo",
         "Roti Bank Foundation Mumbai", "+91 98200 99887", "Mumbai", "Dadar Central Relief Station, Mumbai",
         None, "Daily capacity: 600 meals / 150 kg", 1),

        (8, "Kavita Deshmukh", "ngo.hope@gmail.com", hash_password("Ngo@123"), "ngo",
         "Hope Haven Care Society", "+91 98451 88776", "Bengaluru", "Rajajinagar 3rd Stage, Bengaluru",
         None, "Capacity: 100 meals (Pending verification)", 0), # Unverified sample for admin workflow

        (9, "Rahul Sharma", "rahul.volunteer@gmail.com", hash_password("Volunteer@123"), "volunteer",
         "Youth Food Runner Collective", "+91 97410 55667", "Bengaluru", "BTM Layout 2nd Stage, Bengaluru",
         None, "Two-wheeler with twin 35L insulated delivery carrier", 1),

        (10, "Priya Patel", "priya.volunteer@gmail.com", hash_password("Volunteer@123"), "volunteer",
         "City Hunger Volunteers", "+91 97230 44556", "Mumbai", "Andheri East Logistics Hub, Mumbai",
         None, "Compact van capacity: 150 kg cargo", 1)
    ]

    for u in users:
        c.execute("""
            INSERT INTO users (id, name, email, password_hash, role, org_name, phone, city, address, donor_type, capacity_info, is_verified, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, u)

    # 2. Insert Donations
    # Helper for timestamps
    def fmt(dt): return dt.strftime('%Y-%m-%d %H:%M:%S')

    donations_data = [
        # 1. Urgent Cooked Meal - Available (Deadline in 2.5 hours)
        {
            'id': 1, 'donor_id': 2, 'recipient_id': None,
            'food_name': 'Vegetable Biryani & Paneer Butter Masala',
            'description': 'Surplus banquet lunch buffet prepared for a corporate seminar. Pristine condition, untouched in warming chafing dishes.',
            'category': 'Cooked Meals', 'quantity': 75.0, 'quantity_unit': 'servings',
            'prep': now - timedelta(hours=2),
            'storage': 'Insulated Container',
            'address': 'The Spice Garden, 12th Main, Indiranagar',
            'city': 'Bengaluru',
            'avail': now - timedelta(minutes=45),
            'deadline': now + timedelta(hours=2, minutes=30),
            'allergen': 'Contains Dairy (Paneer, Butter), Cashew nuts',
            'handling': 'Keep sealed until distribution. Best served warm or refrigerated within 2 hours.',
            'status': 'AVAILABLE',
            'image_url': 'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=500&auto=format&fit=crop&q=60'
        },
        # 2. Fresh Bakery Surplus - Available (Deadline in 7 hours)
        {
            'id': 2, 'donor_id': 4, 'recipient_id': None,
            'food_name': 'Artisanal Whole Wheat Loaves & Multigrain Buns',
            'description': 'Fresh morning bake excess from today. Baked at 6:00 AM, hygienically paper-bagged in pairs.',
            'category': 'Bakery Items', 'quantity': 45.0, 'quantity_unit': 'packages',
            'prep': now - timedelta(hours=5),
            'storage': 'Room Temperature',
            'address': 'Fresh Daily Bakery, 7th Cross Koramangala 4th Block',
            'city': 'Bengaluru',
            'avail': now - timedelta(hours=1),
            'deadline': now + timedelta(hours=7),
            'allergen': 'Contains Gluten (Wheat), Sesame Seeds',
            'handling': 'Store in dry ambient room temperature away from direct moisture.',
            'status': 'AVAILABLE',
            'image_url': 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500&auto=format&fit=crop&q=60'
        },
        # 3. Fresh Farm Produce - Available (Deadline tomorrow)
        {
            'id': 3, 'donor_id': 5, 'recipient_id': None,
            'food_name': 'Fresh Seasonal Apples, Oranges & Bananas',
            'description': 'High nutritional quality retail crate surplus. Fruit skins have minor cosmetic marks but flesh is fresh and intact.',
            'category': 'Fruits', 'quantity': 40.0, 'quantity_unit': 'kg',
            'prep': now - timedelta(hours=6),
            'storage': 'Room Temperature',
            'address': 'Green Valley Supermarket, Linking Road, Bandra West',
            'city': 'Mumbai',
            'avail': now - timedelta(hours=2),
            'deadline': now + timedelta(hours=20),
            'allergen': 'None',
            'handling': 'No refrigeration needed. Handle crates carefully to prevent bruising.',
            'status': 'AVAILABLE',
            'image_url': 'https://images.unsplash.com/photo-1619566636858-adf3ef46400b?w=500&auto=format&fit=crop&q=60'
        },
        # 4. Large Wedding Buffet - Accepted (Accepted by Anna Seva, awaiting pickup)
        {
            'id': 4, 'donor_id': 3, 'recipient_id': 6,
            'food_name': 'Grand Royal Dinner Feast (Pulao, Dal Makhani, Mixed Veg)',
            'description': 'Wedding reception excess prepared under high sanitary standards in hotel kitchen. Packed in food-grade foil containers.',
            'category': 'Cooked Meals', 'quantity': 140.0, 'quantity_unit': 'servings',
            'prep': now - timedelta(hours=3),
            'storage': 'Insulated Container',
            'address': 'Grand Orchid Convention Center, Bellary Road, Hebbal',
            'city': 'Bengaluru',
            'avail': now - timedelta(hours=2),
            'deadline': now + timedelta(hours=3),
            'allergen': 'Dairy, Mustard',
            'handling': 'Volunteer or NGO vehicle should have thermal boxes. Rapid transit recommended.',
            'status': 'ACCEPTED',
            'accepted_at': now - timedelta(minutes=40),
            'image_url': 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=500&auto=format&fit=crop&q=60'
        },
        # 5. Vegetables in Transit - Picked Up (Rahul Sharma picked up, en route)
        {
            'id': 5, 'donor_id': 2, 'recipient_id': 9,
            'food_name': 'Assorted Crate Vegetables (Tomatoes, Capsicum, Potatoes)',
            'description': 'Cleaned, pre-sorted vegetable prep excess from restaurant kitchen inventory turnover.',
            'category': 'Vegetables', 'quantity': 35.0, 'quantity_unit': 'kg',
            'prep': now - timedelta(hours=8),
            'storage': 'Refrigerated',
            'address': 'The Spice Garden, Indiranagar',
            'city': 'Bengaluru',
            'avail': now - timedelta(hours=4),
            'deadline': now + timedelta(hours=14),
            'allergen': 'None',
            'handling': 'Wash before cooking. Transfer directly to community shelter kitchen.',
            'status': 'PICKED_UP',
            'accepted_at': now - timedelta(hours=2),
            'picked_up_at': now - timedelta(minutes=30),
            'image_url': 'https://images.unsplash.com/photo-1540420773420-3366772f4999?w=500&auto=format&fit=crop&q=60'
        },
        # 6. Delivered Successfully - Completed
        {
            'id': 6, 'donor_id': 3, 'recipient_id': 6,
            'food_name': 'Steamed Idli, Vada & Sambar Breakfast Bar',
            'description': 'Early morning conference breakfast surplus. Distributed to 110 children and staff at Ashraya Shishu Bhavan.',
            'category': 'Cooked Meals', 'quantity': 110.0, 'quantity_unit': 'servings',
            'prep': now - timedelta(days=1, hours=4),
            'storage': 'Insulated Container',
            'address': 'Grand Orchid Convention Center, Hebbal',
            'city': 'Bengaluru',
            'avail': now - timedelta(days=1, hours=3),
            'deadline': now - timedelta(days=1),
            'allergen': 'Lentils, Mustard seeds',
            'handling': 'Maintain above 60°C until serving.',
            'status': 'DELIVERED',
            'accepted_at': now - timedelta(days=1, hours=2, minutes=45),
            'picked_up_at': now - timedelta(days=1, hours=2),
            'delivered_at': now - timedelta(days=1, hours=1),
            'image_url': 'https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=500&auto=format&fit=crop&q=60'
        },
        # 7. Delivered Successfully - Mumbai
        {
            'id': 7, 'donor_id': 5, 'recipient_id': 7,
            'food_name': 'Packaged Dry Provisions (Lentils, Biscuits, Rice Bags)',
            'description': 'Retail packaged grocery items close to shelf display rotation date but within manufacturer shelf life.',
            'category': 'Packaged Food', 'quantity': 80.0, 'quantity_unit': 'packages',
            'prep': now - timedelta(days=2),
            'storage': 'Room Temperature',
            'address': 'Green Valley Supermarket, Linking Road, Bandra',
            'city': 'Mumbai',
            'avail': now - timedelta(days=2, hours=5),
            'deadline': now - timedelta(days=1, hours=10),
            'allergen': 'See factory packaging labels',
            'handling': 'Inspect dry seals before shelter distribution.',
            'status': 'DELIVERED',
            'accepted_at': now - timedelta(days=2, hours=4),
            'picked_up_at': now - timedelta(days=2, hours=2),
            'delivered_at': now - timedelta(days=2, hours=1),
            'image_url': 'https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=500&auto=format&fit=crop&q=60'
        },
        # 8. Cancelled Listing Sample
        {
            'id': 8, 'donor_id': 4, 'recipient_id': None,
            'food_name': 'Assorted Fresh Fruit Cream Tarts',
            'description': 'Delicate cream pastries. Donor cancelled listing after small refrigeration malfunction was detected.',
            'category': 'Bakery Items', 'quantity': 25.0, 'quantity_unit': 'servings',
            'prep': now - timedelta(days=1),
            'storage': 'Refrigerated',
            'address': 'Fresh Daily Bakery, Koramangala',
            'city': 'Bengaluru',
            'avail': now - timedelta(days=1, hours=4),
            'deadline': now - timedelta(days=1, hours=1),
            'allergen': 'Dairy, Egg, Wheat',
            'handling': 'Discarded per safety protocol.',
            'status': 'CANCELLED',
            'cancelled_at': now - timedelta(days=1, hours=3),
            'image_url': 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500&auto=format&fit=crop&q=60'
        },
        # 9. Expired Listing Sample
        {
            'id': 9, 'donor_id': 2, 'recipient_id': None,
            'food_name': 'Executive Lunch Box Thali Meals',
            'description': 'Leftover thali boxes from corporate training day that surpassed safety pickup deadline before any NGO could reach.',
            'category': 'Cooked Meals', 'quantity': 30.0, 'quantity_unit': 'servings',
            'prep': now - timedelta(days=2, hours=8),
            'storage': 'Room Temperature',
            'address': 'The Spice Garden, Indiranagar',
            'city': 'Bengaluru',
            'avail': now - timedelta(days=2, hours=6),
            'deadline': now - timedelta(days=2, hours=2),
            'allergen': 'Mustard, Dairy',
            'handling': 'Automated expiry due to window closure.',
            'status': 'EXPIRED',
            'image_url': 'https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=500&auto=format&fit=crop&q=60'
        }
    ]

    for d in donations_data:
        # Calculate urgency score
        score, level, _ = calculate_urgency_score(
            d['category'], d['storage'], fmt(d['deadline']), d['quantity'], d['quantity_unit']
        )
        c.execute("""
            INSERT INTO donations (
                id, donor_id, recipient_id, food_name, description, category, quantity, quantity_unit,
                preparation_time, storage_condition, pickup_address, city, available_from, pickup_deadline,
                allergen_info, handling_instructions, image_url, donor_contact_shared, safety_agreement,
                status, urgency_score, urgency_level, accepted_at, picked_up_at, delivered_at, cancelled_at,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            d['id'], d['donor_id'], d.get('recipient_id'), d['food_name'], d['description'], d['category'],
            d['quantity'], d['quantity_unit'], fmt(d['prep']), d['storage'], d['address'], d['city'],
            fmt(d['avail']), fmt(d['deadline']), d['allergen'], d['handling'], d['image_url'],
            d['status'], score, level,
            fmt(d['accepted_at']) if d.get('accepted_at') else None,
            fmt(d['picked_up_at']) if d.get('picked_up_at') else None,
            fmt(d['delivered_at']) if d.get('delivered_at') else None,
            fmt(d['cancelled_at']) if d.get('cancelled_at') else None,
            fmt(d['avail']),
            fmt(d.get('delivered_at') or d.get('picked_up_at') or d.get('accepted_at') or d['avail'])
        ))

    # 3. Status Change Audit Logs
    status_logs = [
        # Donation 1 (Available)
        (1, None, 'AVAILABLE', 2, 'Donation listing published with safety certification.', fmt(now - timedelta(minutes=45))),
        
        # Donation 2 (Available)
        (2, None, 'AVAILABLE', 4, 'Bakery surplus posted for NGO redistribution.', fmt(now - timedelta(hours=1))),

        # Donation 3 (Available)
        (3, None, 'AVAILABLE', 5, 'Supermarket fruit crate surplus published.', fmt(now - timedelta(hours=2))),

        # Donation 4 (Accepted)
        (4, None, 'AVAILABLE', 3, 'Wedding feast excess listed by banquet manager.', fmt(now - timedelta(hours=2))),
        (4, 'AVAILABLE', 'ACCEPTED', 6, 'Anna Seva Foundation accepted donation. Dispatching relief team.', fmt(now - timedelta(minutes=40))),

        # Donation 5 (Picked Up)
        (5, None, 'AVAILABLE', 2, 'Surplus vegetables listed.', fmt(now - timedelta(hours=4))),
        (5, 'AVAILABLE', 'ACCEPTED', 9, 'Volunteer Rahul Sharma accepted pickup assignment.', fmt(now - timedelta(hours=2))),
        (5, 'ACCEPTED', 'PICKED_UP', 9, 'Rahul Sharma verified physical condition and loaded crates onto carrier vehicle.', fmt(now - timedelta(minutes=30))),

        # Donation 6 (Delivered)
        (6, None, 'AVAILABLE', 3, 'Breakfast bar items listed.', fmt(now - timedelta(days=1, hours=3))),
        (6, 'AVAILABLE', 'ACCEPTED', 6, 'Anna Seva Foundation claimed donation.', fmt(now - timedelta(days=1, hours=2, minutes=45))),
        (6, 'ACCEPTED', 'PICKED_UP', 6, 'Collected from Grand Orchid kitchen dock.', fmt(now - timedelta(days=1, hours=2))),
        (6, 'PICKED_UP', 'DELIVERED', 6, 'Delivered and served warm at Ashraya Shishu Bhavan.', fmt(now - timedelta(days=1, hours=1))),

        # Donation 7 (Delivered)
        (7, None, 'AVAILABLE', 5, 'Dry provisions listed.', fmt(now - timedelta(days=2, hours=5))),
        (7, 'AVAILABLE', 'ACCEPTED', 7, 'Roti Bank Mumbai claimed listing.', fmt(now - timedelta(days=2, hours=4))),
        (7, 'ACCEPTED', 'PICKED_UP', 7, 'Loaded into NGO relief van.', fmt(now - timedelta(days=2, hours=2))),
        (7, 'PICKED_UP', 'DELIVERED', 7, 'Received at Dadar Central shelter distribution point.', fmt(now - timedelta(days=2, hours=1))),

        # Donation 8 (Cancelled)
        (8, None, 'AVAILABLE', 4, 'Pastries listed.', fmt(now - timedelta(days=1, hours=4))),
        (8, 'AVAILABLE', 'CANCELLED', 4, 'Cancelled by donor: chiller temperature fluctuation reported.', fmt(now - timedelta(days=1, hours=3))),

        # Donation 9 (Expired)
        (9, None, 'AVAILABLE', 2, 'Corporate lunch boxes listed.', fmt(now - timedelta(days=2, hours=6))),
        (9, 'AVAILABLE', 'EXPIRED', 2, 'Automated system expiry: Pickup deadline passed without collector claim.', fmt(now - timedelta(days=2, hours=2)))
    ]

    for log in status_logs:
        c.execute("""
            INSERT INTO donation_status_history (donation_id, from_status, to_status, changed_by_user_id, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, log)

    # 4. Food Safety Report
    c.execute("""
        INSERT INTO safety_reports (
            donation_id, reported_by_user_id, reason, details, status, admin_notes, created_at, reviewed_at, reviewed_by_user_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        4, 6, "Improper Storage",
        "Upon arriving at the kitchen dock, the containers were held in insulated boxes, but outer packaging was exposed to hot sunlight. Advised banquet team to place in shaded corridor.",
        "INVESTIGATING",
        "Admin verified with donor. Banquet manager relocated staging area to climate-controlled ante-room. Safe to proceed with thermal transport.",
        fmt(now - timedelta(minutes=25)),
        fmt(now - timedelta(minutes=15)),
        1
    ))

    # 5. Notifications
    sample_notifications = [
        (2, 1, "Listing Published", "Your donation 'Vegetable Biryani & Paneer Butter Masala' is active and visible to verified NGOs.", 0, "/donations/1", fmt(now - timedelta(minutes=45))),
        (3, 4, "Donation Accepted", "Anna Seva Feeding Foundation has accepted your donation 'Grand Royal Dinner Feast'.", 0, "/donations/4", fmt(now - timedelta(minutes=40))),
        (6, 4, "Pickup Reminder", "Please complete pickup for 'Grand Royal Dinner Feast' before deadline.", 0, "/donations/4", fmt(now - timedelta(minutes=35))),
        (9, 5, "Delivery in Progress", "You have picked up 'Assorted Crate Vegetables'. Please confirm delivery once dropped off.", 0, "/donations/5", fmt(now - timedelta(minutes=29))),
        (1, 4, "Safety Flag Review Required", "A storage observation was logged for donation #4. Admin review action recommended.", 0, "/admin/safety-reports", fmt(now - timedelta(minutes=24)))
    ]

    for n in sample_notifications:
        c.execute("""
            INSERT INTO notifications (user_id, donation_id, title, message, is_read, link, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, n)

    conn.commit()
    conn.close()
    print("Database successfully initialized and seeded with realistic sample data!")

if __name__ == '__main__':
    seed_all()
