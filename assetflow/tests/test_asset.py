# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from odoo import fields
from datetime import timedelta

class TestAssetFlow(TransactionCase):

    def setUp(self):
        super(TestAssetFlow, self).setUp()
        
        # 1. Create a Department
        self.dept_engineering = self.env['assetflow.department'].create({
            'name': 'Engineering Department',
            'code': 'ENG',
            'status': 'active',
        })
        
        # 2. Create a Category
        self.cat_laptops = self.env['assetflow.category'].create({
            'name': 'Laptops & Computers',
            'warranty_period': 12,
            'maintenance_interval': 6,  # 6 months
        })
        
        # 3. Create Demo Users
        self.user_employee = self.env['res.users'].create({
            'name': 'Test Employee',
            'login': 'test_employee@example.com',
            'email': 'test_employee@example.com',
            'department_id': self.dept_engineering.id,
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id, self.env.ref('assetflow.group_assetflow_employee').id])],
        })
        
        # 4. Create an Asset
        self.asset_laptop = self.env['assetflow.asset'].create({
            'name': 'Lenovo ThinkPad Test',
            'category_id': self.cat_laptops.id,
            'serial_no': 'SN-TEST-1234',
            'acquisition_date': fields.Date.today() - timedelta(days=365),  # 1 year ago
            'acquisition_cost': 1200.0,
            'salvage_value': 200.0,
            'depreciation_years': 5,
            'condition': 'good',
            'location': 'Office Alpha',
            'is_bookable': True,
            'department_id': self.dept_engineering.id,
            'state': 'available',
        })

    def test_01_asset_creation(self):
        """ Test that asset creation generates a tag sequence correctly """
        self.assertTrue(self.asset_laptop.tag)
        self.assertNotEqual(self.asset_laptop.tag, 'New')
        self.assertEqual(self.asset_laptop.state, 'available')

    def test_02_asset_depreciation(self):
        """ Test depreciation & book value calculations """
        self.assertEqual(self.asset_laptop.depreciation_years, 5)
        # 1 year has elapsed
        # depreciable base = 1200 - 200 = 1000
        # annual depreciation = 1000 / 5 = 200
        self.assertAlmostEqual(self.asset_laptop.accumulated_depreciation, 200.0, delta=1.0)
        self.assertAlmostEqual(self.asset_laptop.book_value, 1000.0, delta=1.0)

    def test_03_asset_allocation_workflow(self):
        """ Test allocation lifecycle and state transition of asset """
        # Create active allocation
        allocation = self.env['assetflow.allocation'].create({
            'asset_id': self.asset_laptop.id,
            'employee_id': self.user_employee.id,
            'expected_return_date': fields.Date.today() + timedelta(days=30),
            'state': 'active',
        })
        
        # Asset state should automatically change to 'allocated'
        self.assertEqual(self.asset_laptop.state, 'allocated')
        self.assertEqual(allocation.state, 'active')
        
        # Test double-allocation prevention (constrains rule)
        with self.assertRaises(ValidationError):
            self.env['assetflow.allocation'].create({
                'asset_id': self.asset_laptop.id,
                'employee_id': self.user_employee.id,
                'state': 'active',
            })
            
        # Return asset
        allocation.write({
            'state': 'returned',
            'condition_notes': 'Returned in perfect condition',
        })
        
        # Asset state should revert to 'available'
        self.assertEqual(self.asset_laptop.state, 'available')
        self.assertEqual(allocation.state, 'returned')
        self.assertTrue(allocation.actual_return_date)

    def test_04_booking_overlaps(self):
        """ Test booking slot overlay/overlap validations """
        today = fields.Datetime.now()
        
        # Successful Booking 1: 09:00 to 10:00
        self.env['assetflow.booking'].create({
            'resource_id': self.asset_laptop.id,
            'employee_id': self.user_employee.id,
            'start_datetime': today.replace(hour=9, minute=0, second=0),
            'end_datetime': today.replace(hour=10, minute=0, second=0),
            'state': 'upcoming',
        })
        
        # Overlapping Booking 2 (starts during booking 1): 09:30 to 10:30 (should raise ValidationError)
        with self.assertRaises(ValidationError):
            self.env['assetflow.booking'].create({
                'resource_id': self.asset_laptop.id,
                'employee_id': self.user_employee.id,
                'start_datetime': today.replace(hour=9, minute=30, second=0),
                'end_datetime': today.replace(hour=10, minute=30, second=0),
                'state': 'upcoming',
            })

        # Non-overlapping Booking 3 (starts right after): 10:00 to 11:00 (should succeed)
        booking3 = self.env['assetflow.booking'].create({
            'resource_id': self.asset_laptop.id,
            'employee_id': self.user_employee.id,
            'start_datetime': today.replace(hour=10, minute=0, second=0),
            'end_datetime': today.replace(hour=11, minute=0, second=0),
            'state': 'upcoming',
        })
        self.assertTrue(booking3.id)

    def test_05_predictive_maintenance_cron(self):
        """ Test that predictive maintenance cron auto-creates requests for aging categories """
        # Set acquisition_date to 12 months ago
        # maintenance interval is 6 months, so it is overdue for maintenance check
        self.asset_laptop.write({
            'acquisition_date': fields.Date.today() - timedelta(days=365),
        })
        
        # Run cron method
        self.env['assetflow.asset']._run_predictive_maintenance_cron()
        
        # Verify a maintenance ticket was created
        ticket = self.env['assetflow.maintenance'].search([
            ('asset_id', '=', self.asset_laptop.id),
            ('state', '=', 'pending')
        ], limit=1)
        
        self.assertTrue(ticket.id)
        self.assertIn("Automated Routine Maintenance check", ticket.issue)
