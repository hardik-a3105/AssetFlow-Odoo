# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AssetflowTransferRequest(models.Model):
    _name = 'assetflow.transfer.request'
    _description = 'Asset Transfer Request'

    asset_id = fields.Many2one('assetflow.asset', string='Asset', required=True)
    from_employee_id = fields.Many2one('res.users', string='From Employee', compute='_compute_from_employee_id', store=True, readonly=False)
    to_employee_id = fields.Many2one('res.users', string='To Employee', required=True)
    reason = fields.Text(string='Reason')
    state = fields.Selection([
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('reallocated', 'Reallocated')
    ], string='Status', default='requested')

    @api.depends('asset_id')
    def _compute_from_employee_id(self):
        for record in self:
            if record.asset_id:
                active_alloc = self.env['assetflow.allocation'].search([
                    ('asset_id', '=', record.asset_id.id),
                    ('state', '=', 'active')
                ], limit=1)
                record.from_employee_id = active_alloc.employee_id.id if active_alloc else False
            else:
                record.from_employee_id = False

    def action_approve(self):
        for record in self:
            # 1. Close current active allocations
            active_allocations = self.env['assetflow.allocation'].search([
                ('asset_id', '=', record.asset_id.id),
                ('state', '=', 'active')
            ])
            for alloc in active_allocations:
                alloc.write({
                    'state': 'returned',
                    'actual_return_date': fields.Date.today()
                })
            
            # 2. Create new allocation
            self.env['assetflow.allocation'].create({
                'asset_id': record.asset_id.id,
                'employee_id': record.to_employee_id.id,
                'state': 'active',
            })
            
            # 3. Mark transfer as reallocated
            record.write({'state': 'reallocated'})

    def action_reject(self):
        for record in self:
            record.write({'state': 'rejected'})

    @api.model_create_multi
    def create(self, vals_list):
        records = super(AssetflowTransferRequest, self).create(vals_list)
        template = self.env.ref('assetflow.email_template_transfer_requested', raise_if_not_found=False)
        if template:
            for record in records:
                try:
                    template.send_mail(record.id, force_send=True)
                except Exception:
                    pass
        return records
