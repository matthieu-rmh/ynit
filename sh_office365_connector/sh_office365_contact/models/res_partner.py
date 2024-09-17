# Part of Softhealer Technologies.
from odoo import fields, models


class ExportOfficeContact(models.Model):
    _inherit = 'res.partner'

    def export_office365_contact(self):
        active_ids = self.env['res.partner'].browse(self.env.context.get('active_ids'))       
        domain = [('user_id', '=', self.env.user.id)]        
        find_config = self.env['sh.office365.base.config'].search(domain)        
        find_config.export_multi_contact(active_ids)
