# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AssetflowBooking(models.Model):
    _name = 'assetflow.booking'
    _description = 'Resource Booking'

    resource_id = fields.Many2one('assetflow.asset', string='Resource', domain="[('is_bookable', '=', True)]", required=True)
    employee_id = fields.Many2one('res.users', string='Employee', required=True)
    start_datetime = fields.Datetime(string='Start Time', required=True)
    end_datetime = fields.Datetime(string='End Time', required=True)
    state = fields.Selection([
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='upcoming')

    @api.constrains('resource_id', 'start_datetime', 'end_datetime', 'state')
    def _check_booking_overlap(self):
        for record in self:
            if record.state != 'cancelled' and record.resource_id and record.start_datetime and record.end_datetime:
                if record.end_datetime <= record.start_datetime:
                    raise ValidationError("Booking End Date/Time must be after Start Date/Time.")
                
                domain = [
                    ('resource_id', '=', record.resource_id.id),
                    ('state', '!=', 'cancelled'),
                    ('start_datetime', '<', record.end_datetime),
                    ('end_datetime', '>', record.start_datetime),
                    ('id', '!=', record.id)
                ]
                overlapping = self.search(domain, limit=1)
                if overlapping:
                    raise ValidationError("Requested slot conflicts with an existing booking — slot is unavailable.")
