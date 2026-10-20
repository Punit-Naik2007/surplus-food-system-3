"""
Automated Verification Suite for Surplus Food Redistribution System
Tests all critical workflows, RBAC constraints, transactional safeguards, and ML urgency engine.
"""

import unittest
from datetime import datetime, timedelta
from app import app
from database import get_db, init_db
from seed_data import seed_all

class SurplusFoodSystemTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        seed_all()

    def test_01_public_pages(self):
        """Test home page, available food page, login page render properly."""
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Surplus Food Redistribution', r.data)
        self.assertIn(b'Rescue Surplus Food', r.data)

        r = self.client.get('/available-food')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Browse Available Food', r.data)

        r = self.client.get('/login')
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'System Authentication', r.data)

    def test_02_demo_login_and_rbac(self):
        """Test demo fast login and role-based access control."""
        # Donor login
        r = self.client.get('/demo-login/donor', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Donor Dashboard', r.data)

        # Donor cannot access admin dashboard
        r = self.client.get('/admin/dashboard', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'You do not have permission', r.data)

        # Admin login
        r = self.client.get('/demo-login/admin', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Nirman Administrative Operations', r.data)

    def test_03_donor_donation_workflow(self):
        """Test donor listing new food and urgency score calculation."""
        self.client.get('/demo-login/donor')
        deadline = (datetime.now() + timedelta(hours=3)).strftime('%Y-%m-%d %H:%M')
        
        post_data = {
            'food_name': 'Test Paneer Pulao Batch',
            'description': 'Fresh buffet surplus from wedding lunch',
            'category': 'Cooked Meals',
            'quantity': '65',
            'quantity_unit': 'servings',
            'storage_condition': 'Insulated Container',
            'pickup_address': '100 Feet Road, Indiranagar',
            'city': 'Bengaluru',
            'pickup_deadline': deadline,
            'safety_agreement': '1'
        }
        r = self.client.post('/donor/donations/new', data=post_data, follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Test Paneer Pulao Batch', r.data)

        # Verify in database
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM donations WHERE food_name = 'Test Paneer Pulao Batch'")
        d = c.fetchone()
        self.assertIsNotNone(d)
        self.assertEqual(d['status'], 'AVAILABLE')
        self.assertGreater(d['urgency_score'], 50.0) # High urgency due to cooked meal & 3 hr window
        conn.close()

    def test_04_ngo_acceptance_and_lifecycle(self):
        """Test verified NGO claiming, picking up, and delivering food."""
        # Login as verified NGO (Anna Seva)
        self.client.get('/demo-login/ngo')
        
        # Accept donation #1 (Available in seed data)
        r = self.client.post('/donations/1/accept', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'Successfully accepted donation', r.data)

        # Concurrency safety: Another acceptance attempt should be rejected
        r_second = self.client.post('/donations/1/accept', follow_redirects=True)
        self.assertIn(b'no longer available', r_second.data)

        # Test invalid transition: Cannot DELIVER before PICKED UP
        r_invalid = self.client.post('/donations/1/deliver', follow_redirects=True)
        self.assertIn(b'before it can be marked as', r_invalid.data)

        # Valid transition: Mark PICKED UP
        r_pickup = self.client.post('/donations/1/pickup', data={'notes': 'Picked up hot'}, follow_redirects=True)
        self.assertEqual(r_pickup.status_code, 200)
        self.assertIn(b'PICKED UP', r_pickup.data)

        # Valid transition: Mark DELIVERED
        r_deliver = self.client.post('/donations/1/deliver', data={'notes': 'Delivered to shelter'}, follow_redirects=True)
        self.assertEqual(r_deliver.status_code, 200)
        self.assertIn(b'DELIVERED', r_deliver.data)

    def test_05_unverified_ngo_restriction(self):
        """Test unverified NGO is prevented from accepting food."""
        # Login as unverified NGO (Hope Haven, id=8 in seed data)
        with self.client.session_transaction() as sess:
            sess['user_id'] = 8
            sess['role'] = 'ngo'
            sess['name'] = 'Kavita Deshmukh'

        r = self.client.post('/donations/2/accept', follow_redirects=True)
        self.assertIn(b'pending administrator verification', r.data)

    def test_06_admin_operations_and_analytics(self):
        """Test admin verification, safety reports, and Chart.js analytics API."""
        self.client.get('/demo-login/admin')

        # 1. Verify unverified NGO #8
        r = self.client.post('/admin/users/8/verify', follow_redirects=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn(b'officially verified', r.data)

        # 2. Check Analytics JSON API
        r_api = self.client.get('/api/analytics-data')
        self.assertEqual(r_api.status_code, 200)
        data = r_api.get_json()
        self.assertIn('status_data', data)
        self.assertIn('category_data', data)
        self.assertIn('city_data', data)
        self.assertIn('unit_comparison', data)

        # 3. Check Analytics Page
        r_page = self.client.get('/admin/analytics')
        self.assertEqual(r_page.status_code, 200)
        self.assertIn(b'Delivery Rate', r_page.data)
        self.assertIn(b'Data, Statistics & ML for Real India', r_page.data)

if __name__ == '__main__':
    unittest.main()
