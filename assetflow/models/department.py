# -*- coding: utf-8 -*-
from odoo import models, fields

class AssetflowDepartment(models.Model):
    _name = 'assetflow.department'
    _description = 'Department'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code')
    head_id = fields.Many2one('res.users', string='Department Head')
    parent_id = fields.Many2one('assetflow.department', string='Parent Department')
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], string='Status', default='active', required=True)
    setup_id = fields.Many2one('assetflow.org.setup', string='Org Setup')

