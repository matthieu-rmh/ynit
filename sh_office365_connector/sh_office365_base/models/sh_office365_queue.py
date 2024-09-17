# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
from odoo import fields, models


class OfficeQueue(models.Model):
    _name = 'sh.office.queue'
    _description = 'Helps you to add incoming req in queue'
    _order = 'id desc'

    queue_type = fields.Selection([('contact', 'Contact'), ('calendar', 'Calendar')])
    sh_contact_id = fields.Char("Contacts")
    sh_queue_name = fields.Char("Name")
    sh_calendar_id = fields.Char("Calendar")
    queue_sync_date = fields.Datetime("Sync Date-Time")
    sh_current_config = fields.Many2one('sh.office365.base.config')
    sh_current_state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], string="State")

    def import_office_manually(self):
        active_queue_ids = self.env['sh.office.queue'].browse(self.env.context.get('active_ids'))
        contact_ids = active_queue_ids.filtered(lambda l: l.sh_contact_id != False)
        calendar_ids = active_queue_ids.filtered(lambda l: l.sh_calendar_id != False)
        if contact_ids:
            for data in contact_ids:
                data.sh_current_config.import_contacts(data.sh_contact_id)
        if calendar_ids:
            for data in calendar_ids:
                data.sh_current_config.import_calendar_data(data)

    def _done(self):
        self.write({'sh_current_state': 'done'})
