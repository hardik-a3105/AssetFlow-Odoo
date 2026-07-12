# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    department_id = fields.Many2one('assetflow.department', string='Department')
    role = fields.Selection([
        ('employee', 'Employee'),
        ('dept_head', 'Department Head'),
        ('manager', 'Asset Manager'),
        ('admin', 'Admin')
    ], string='Role', compute='_compute_role')

    @api.depends('groups_id')
    def _compute_role(self):
        for user in self:
            if user.has_group('assetflow.group_assetflow_admin'):
                user.role = 'admin'
            elif user.has_group('assetflow.group_assetflow_manager'):
                user.role = 'manager'
            elif user.has_group('assetflow.group_assetflow_dept_head'):
                user.role = 'dept_head'
            elif user.has_group('assetflow.group_assetflow_employee'):
                user.role = 'employee'
            else:
                user.role = False

    def action_promote_manager(self):
        manager_group = self.env.ref('assetflow.group_assetflow_manager')
        for user in self:
            if manager_group and manager_group not in user.groups_id:
                user.write({'groups_id': [(4, manager_group.id)]})

    def action_promote_dept_head(self):
        dept_head_group = self.env.ref('assetflow.group_assetflow_dept_head')
        for user in self:
            if dept_head_group and dept_head_group not in user.groups_id:
                user.write({'groups_id': [(4, dept_head_group.id)]})


    @api.model
    def signup(self, values, token=None):
        """ Override signup to automatically assign new users to the AssetFlow Employee group """
        login, password = super(ResUsers, self).signup(values, token=token)
        if login:
            user = self.search([('login', '=', login)], limit=1)
            if user:
                employee_group = self.env.ref('assetflow.group_assetflow_employee', raise_if_not_found=False)
                if employee_group and employee_group not in user.groups_id:
                    user.write({'groups_id': [(4, employee_group.id)]})
        return login, password
