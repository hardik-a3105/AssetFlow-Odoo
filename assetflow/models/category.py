# -*- coding: utf-8 -*-
from odoo import models, fields

class AssetflowCategory(models.Model):
    _name = 'assetflow.category'
    _description = 'Asset Category'

    name = fields.Char(string='Name', required=True)
    warranty_period = fields.Integer(string='Warranty Period (months)')
    setup_id = fields.Many2one('assetflow.org.setup', string='Org Setup')

