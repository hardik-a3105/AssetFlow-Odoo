# -*- coding: utf-8 -*-
import base64
from io import BytesIO
import qrcode
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
    allocation_ids = fields.One2many('assetflow.allocation', 'asset_id', string='Allocations')
    allocation_count = fields.Integer(string='Allocation Count', compute='_compute_allocation_count', store=True)

    # Roadmap Features
    qr_code = fields.Binary(string='QR Code', compute='_compute_qr_code', store=True)
    salvage_value = fields.Float(string='Salvage Value', default=0.0)
    depreciation_years = fields.Integer(string='Depreciation Lifespan (Years)', default=5)
    accumulated_depreciation = fields.Float(string='Accumulated Depreciation', compute='_compute_depreciation')
    book_value = fields.Float(string='Current Book Value', compute='_compute_depreciation')

    @api.depends('allocation_ids')
    def _compute_allocation_count(self):
        for asset in self:
            asset.allocation_count = len(asset.allocation_ids)

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
            'checklist': {
                'has_assets': self.search_count([]) > 0,
                'has_bookings': self.env['assetflow.booking'].search_count([]) > 0,
                'has_maintenances': self.env['assetflow.maintenance'].search_count([]) > 0,
            },
            'overdue': {
                'count': overdue_count,
                'list': overdue_list,
            },
            'activities': activities
        }

    @api.depends('tag')
    def _compute_qr_code(self):
        for asset in self:
            if asset.tag and asset.tag != 'New':
                try:
                    qr = qrcode.QRCode(version=1, box_size=3, border=4)
                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url') or 'http://localhost:8069'
                    asset_url = f"{base_url}/web#id={asset.id}&model=assetflow.asset&view_type=form"
                    qr.add_data(asset_url)
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="black", back_color="white")
                    temp = BytesIO()
                    img.save(temp, format="PNG")
                    asset.qr_code = base64.b64encode(temp.getvalue())
                except Exception:
                    asset.qr_code = False
            else:
                asset.qr_code = False

    @api.depends('acquisition_cost', 'salvage_value', 'acquisition_date', 'depreciation_years')
    def _compute_depreciation(self):
        today = fields.Date.today()
        for asset in self:
            if asset.acquisition_cost and asset.acquisition_date and asset.depreciation_years > 0:
                delta = today - asset.acquisition_date
                years_elapsed = delta.days / 365.25
                years_elapsed = max(0.0, min(years_elapsed, float(asset.depreciation_years)))
                
                depreciable_base = asset.acquisition_cost - asset.salvage_value
                annual_depr = depreciable_base / asset.depreciation_years
                
                accum = annual_depr * years_elapsed
                asset.accumulated_depreciation = accum
                asset.book_value = asset.acquisition_cost - accum
            else:
                asset.accumulated_depreciation = 0.0
                asset.book_value = asset.acquisition_cost

    @api.model
    def _run_predictive_maintenance_cron(self):
        today = fields.Date.today()
        assets = self.search([('state', 'in', ('available', 'allocated'))])
        for asset in assets:
            interval = asset.category_id.maintenance_interval
            if interval > 0 and asset.acquisition_date:
                active_maint = self.env['assetflow.maintenance'].search_count([
                    ('asset_id', '=', asset.id),
                    ('state', 'in', ('pending', 'approved', 'assigned', 'in_progress'))
                ])
                if active_maint > 0:
                    continue
                
                last_maint = self.env['assetflow.maintenance'].search([
                    ('asset_id', '=', asset.id),
                    ('state', '=', 'resolved')
                ], order='write_date desc', limit=1)
                
                base_date = fields.Date.to_date(last_maint.write_date) if last_maint else asset.acquisition_date
                months_elapsed = (today.year - base_date.year) * 12 + (today.month - base_date.month)
                
                if months_elapsed >= interval:
                    self.env['assetflow.maintenance'].create({
                         'asset_id': asset.id,
                         'issue': f'Automated Routine Maintenance check (interval: {interval} months). Last inspection/acquisition date: {base_date}.',
                         'priority': 'medium',
                         'state': 'pending',
                    })
