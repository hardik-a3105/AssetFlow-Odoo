# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AssetflowAsset(models.Model):
    _name = 'assetflow.asset'
    _description = 'Asset'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True)
    tag = fields.Char(string='Tag', readonly=True, copy=False, default='New')
    category_id = fields.Many2one('assetflow.category', string='Category', required=True)
    serial_no = fields.Char(string='Serial Number')
    acquisition_date = fields.Date(string='Acquisition Date')
    acquisition_cost = fields.Float(string='Acquisition Cost')
    condition = fields.Selection([
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor')
    ], string='Condition')
    location = fields.Char(string='Location')
    is_bookable = fields.Boolean(string='Shared/Bookable')
    department_id = fields.Many2one('assetflow.department', string='Department')
    state = fields.Selection([
        ('available', 'Available'),
        ('allocated', 'Allocated'),
        ('reserved', 'Reserved'),
        ('maintenance', 'Maintenance'),
        ('lost', 'Lost'),
        ('retired', 'Retired'),
        ('disposed', 'Disposed')
    ], string='Status', default='available', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('tag', 'New') == 'New' or not vals.get('tag'):
                vals['tag'] = self.env['ir.sequence'].next_by_code('assetflow.asset') or 'New'
        return super(AssetflowAsset, self).create(vals_list)

    @api.model
    def get_dashboard_data(self):
        today = fields.Date.today()
        # KPI counts
        available_assets = self.search_count([('state', '=', 'available')])
        allocated_assets = self.search_count([('state', '=', 'allocated')])
        bookable_resources = self.search_count([('is_bookable', '=', True), ('state', '=', 'available')])
        active_bookings = self.env['assetflow.booking'].search_count([('state', 'in', ['upcoming', 'ongoing'])])
        pending_transfers = self.env['assetflow.transfer.request'].search_count([('state', '=', 'requested')])
        
        # Upcoming returns (active allocations returning in the future)
        upcoming_returns = self.env['assetflow.allocation'].search_count([
            ('state', '=', 'active'),
            ('expected_return_date', '>=', today)
        ])
        
        # Overdue returns
        overdue_allocations = self.env['assetflow.allocation'].search([
            ('state', '=', 'active'),
            ('expected_return_date', '<', today)
        ])
        overdue_count = len(overdue_allocations)
        overdue_list = []
        for alloc in overdue_allocations:
            overdue_list.append({
                'id': alloc.id,
                'asset_name': alloc.asset_id.name,
                'employee_name': alloc.employee_id.name or "Unknown",
                'expected_date': fields.Date.to_string(alloc.expected_return_date) if alloc.expected_return_date else "",
            })
            
        # Recent activities from mail.message
        recent_messages = self.env['mail.message'].search([
            ('model', 'in', ['assetflow.allocation', 'assetflow.booking', 'assetflow.maintenance'])
        ], limit=5, order='date desc')
        activities = []
        for msg in recent_messages:
            # Simple text conversion of HTML body if present
            body_text = msg.body or ""
            if body_text.startswith("<p>") and body_text.endswith("</p>"):
                body_text = body_text[3:-4]
            activities.append({
                'id': msg.id,
                'author': msg.author_id.name or "System",
                'body': body_text,
                'date': fields.Datetime.to_string(msg.date),
                'model_name': msg.model,
                'record_name': msg.record_name or "",
            })
            
        return {
            'kpis': {
                'available_assets': available_assets,
                'allocated_assets': allocated_assets,
                'bookable_resources': bookable_resources,
                'active_bookings': active_bookings,
                'pending_transfers': pending_transfers,
                'upcoming_returns': upcoming_returns,
            },
            'overdue': {
                'count': overdue_count,
                'list': overdue_list,
            },
            'activities': activities
        }

