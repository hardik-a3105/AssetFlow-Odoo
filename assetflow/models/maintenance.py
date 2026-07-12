# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AssetflowMaintenance(models.Model):
    _name = 'assetflow.maintenance'
    _description = 'Asset Maintenance'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    asset_id = fields.Many2one('assetflow.asset', string='Asset', required=True, tracking=True)
    issue = fields.Text(string='Issue Description', required=True)
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ], string='Priority', default='medium')
    technician_id = fields.Many2one('res.users', string='Technician', tracking=True)
    state = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('assigned', 'Technician Assigned'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected')
    ], string='Status', default='pending', tracking=True)

    def action_approve(self):
        for record in self:
            record.write({'state': 'approved'})
            if record.asset_id:
                record.asset_id.state = 'maintenance'

    def action_assign_technician(self):
        for record in self:
            record.write({'state': 'assigned'})

    def action_start(self):
        for record in self:
            record.write({'state': 'in_progress'})

    def action_resolve(self):
        for record in self:
            record.write({'state': 'resolved'})
            if record.asset_id:
                record.asset_id.state = 'available'

    def action_reject(self):
        for record in self:
            record.write({'state': 'rejected'})
