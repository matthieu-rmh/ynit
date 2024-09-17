# -*- coding: utf-8 -*-

from odoo import fields, models, tools, api

class FbiActivityReport(models.Model):
    _inherit = 'crm.activity.report'
    
    write_date = fields.Datetime('Activités entre le ', readonly=True)
    
    def _select(self):
        res = super(FbiActivityReport, self)._select()
        res += ', m.write_date'
        return res
        
    def _where(self):
        disccusion_subtype = self.env.ref('mail.mt_comment')
        return """
            WHERE
                m.model = 'crm.lead' 
        """