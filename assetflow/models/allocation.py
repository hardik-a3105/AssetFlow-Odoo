# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AssetflowAllocation(models.Model):
    _name = 'assetflow.allocation'
    _description = 'Asset Allocation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    asset_id = fields.Many2one('assetflow.asset', string='Asset', required=True, tracking=True)
    employee_id = fields.Many2one('res.users', string='Employee', tracking=True)
    department_id = fields.Many2one('assetflow.department', string='Department', tracking=True)
    expected_return_date = fields.Date(string='Expected Return Date', tracking=True)
    actual_return_date = fields.Date(string='Actual Return Date', tracking=True)
    state = fields.Selection([
        ('active', 'Active'),
        ('returned', 'Returned')
    ], string='Status', default='active', tracking=True)
    condition_notes = fields.Text(string='Condition Notes')
    is_overdue = fields.Boolean(string='Overdue', compute='_compute_is_overdue')
    asset_state = fields.Selection(related='asset_id.state', string="Asset Status")

    @api.depends('state', 'expected_return_date')
    def _compute_is_overdue(self):
        today = fields.Date.today()
        for record in self:
            record.is_overdue = record.state == 'active' and record.expected_return_date and record.expected_return_date < today

    @api.constrains('state', 'asset_id')
    def _check_active_allocation(self):
        for record in self:
            if record.state == 'active':
                domain = [
                    ('asset_id', '=', record.asset_id.id),
                    ('state', '=', 'active'),
                    ('id', '!=', record.id)
                ]
                existing = self.search(domain, limit=1)
                if existing:
                    employee_name = existing.employee_id.name or "another employee"
                    raise ValidationError(
                        f"Already allocated to {employee_name} — direct re-allocation is blocked. "
                        "Submit a transfer request instead."
                    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('state', 'active') == 'active':
                # We can update the asset's state
                asset = self.env['assetflow.asset'].browse(vals.get('asset_id'))
                if asset:
                    asset.state = 'allocated'
        records = super(AssetflowAllocation, self).create(vals_list)
        return records

    def write(self, vals):
        if vals.get('state') == 'returned' and 'actual_return_date' not in vals:
            vals['actual_return_date'] = fields.Date.today()
        res = super(AssetflowAllocation, self).write(vals)
        if 'state' in vals:
            for record in self:
                if record.state == 'active':
                    record.asset_id.state = 'allocated'
                elif record.state == 'returned':
                    record.asset_id.state = 'available'
        return res

    def action_create_transfer(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Transfer Request',
            'res_model': 'assetflow.transfer.request',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_asset_id': self.asset_id.id,
                'default_to_employee_id': self.employee_id.id,
            }
        }
