# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AssetflowOrgSetup(models.Model):
    _name = 'assetflow.org.setup'
    _description = 'Organization Setup Settings'

    name = fields.Char(string='Name', default='Organization Setup Settings')
    department_ids = fields.One2many('assetflow.department', 'setup_id', string='Departments')
    category_ids = fields.One2many('assetflow.category', 'setup_id', string='Categories')
    employee_ids = fields.Many2many('res.users', compute='_compute_employee_ids', string='Employees')

    def _compute_employee_ids(self):
        for record in self:
            record.employee_ids = self.env['res.users'].search([('share', '=', False)])

    @api.model
    def action_open_setup(self):
        setup = self.search([], limit=1)
        if not setup:
            setup = self.create({'name': 'Organization Setup Settings'})
        
        # Auto-link any existing departments/categories that are not linked
        depts = self.env['assetflow.department'].search([('setup_id', '=', False)])
        if depts:
            depts.write({'setup_id': setup.id})
        cats = self.env['assetflow.category'].search([('setup_id', '=', False)])
        if cats:
            cats.write({'setup_id': setup.id})
            
        return {
            'type': 'ir.actions.act_window',
            'name': 'Organization Setup',
            'res_model': 'assetflow.org.setup',
            'res_id': setup.id,
            'view_mode': 'form',
            'views': [[False, 'form']],
            'target': 'current',
        }
