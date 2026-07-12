# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AssetflowAuditCycle(models.Model):
    _name = 'assetflow.audit.cycle'
    _description = 'Asset Audit Cycle'

    name = fields.Char(string='Name', required=True)
    department_id = fields.Many2one('assetflow.department', string='Department', required=True)
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    auditor_ids = fields.Many2many('res.users', string='Auditors')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('closed', 'Closed')
    ], string='Status', default='draft')
    line_ids = fields.One2many('assetflow.audit.line', 'cycle_id', string='Audit Lines')
    discrepancy_summary = fields.Text(string='Discrepancy Summary', compute='_compute_discrepancy_summary')

    @api.depends('line_ids.result')
    def _compute_discrepancy_summary(self):
        for cycle in self:
            verified = len(cycle.line_ids.filtered(lambda l: l.result == 'verified'))
            missing = len(cycle.line_ids.filtered(lambda l: l.result == 'missing'))
            damaged = len(cycle.line_ids.filtered(lambda l: l.result == 'damaged'))
            unverified = len(cycle.line_ids.filtered(lambda l: not l.result))
            
            summary = f"Total Assets Audited: {len(cycle.line_ids)}\n"
            summary += f"- Verified: {verified}\n"
            summary += f"- Missing: {missing} (Will be marked as 'Lost' on cycle close)\n"
            summary += f"- Damaged: {damaged} (Recommend maintenance request)\n"
            summary += f"- Pending Verification: {unverified}"
            cycle.discrepancy_summary = summary

    def action_start(self):
        for record in self:
            record.write({'state': 'in_progress'})
            if record.department_id and not record.line_ids:
                assets = self.env['assetflow.asset'].search([
                    ('department_id', '=', record.department_id.id),
                    ('state', 'not in', ['retired', 'disposed'])
                ])
                lines = []
                for asset in assets:
                    lines.append((0, 0, {
                        'asset_id': asset.id,
                        'expected_location': asset.location,
                    }))
                record.write({'line_ids': lines})

    def action_close(self):
        for record in self:
            for line in record.line_ids:
                if line.result == 'missing':
                    line.asset_id.write({'state': 'lost'})
            record.write({'state': 'closed'})


class AssetflowAuditLine(models.Model):
    _name = 'assetflow.audit.line'
    _description = 'Asset Audit Line'

    cycle_id = fields.Many2one('assetflow.audit.cycle', string='Audit Cycle', ondelete='cascade', required=True)
    asset_id = fields.Many2one('assetflow.asset', string='Asset', required=True)
    expected_location = fields.Char(string='Expected Location')
    result = fields.Selection([
        ('verified', 'Verified'),
        ('missing', 'Missing'),
        ('damaged', 'Damaged')
    ], string='Verification Result')

    @api.onchange('asset_id')
    def _onchange_asset_id(self):
        if self.asset_id:
            self.expected_location = self.asset_id.location

    def action_set_verified(self):
        for record in self:
            record.write({'result': 'verified'})

    def action_set_missing(self):
        for record in self:
            record.write({'result': 'missing'})

    def action_set_damaged(self):
        for record in self:
            record.write({'result': 'damaged'})
