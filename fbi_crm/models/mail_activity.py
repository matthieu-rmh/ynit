# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import UserError

class FbiMailActivity(models.Model):
    _inherit = 'mail.activity'

    def _action_done(self, feedback=False, attachment_ids=False):
        ### MARK DONE
        if self.res_id and self.res_model == 'crm.lead':
            lead = self.env[self.res_model].sudo().browse(int(self.res_id))
            activity_type_id = lead._get_res_id('fbi_crm.mail_activity_type_rappel_72h')
            if lead.is_dematicall() and self.activity_type_id and self.activity_type_id.id == activity_type_id:
                lead.stage_id = lead._get_res_id('fbi_crm.stage_controle_qualite')
                lead.rdv_72_confirmation = True
            activity_type_id_j7 = lead._get_res_id('fbi_crm.mail_activity_type_rappel_J7')
            if lead.is_dematicall() and self.activity_type_id and self.activity_type_id.id == activity_type_id_j7:
                lead.stage_id = lead._get_res_id('fbi_crm.stage_envoi_et_archive')

        return super()._action_done(feedback=feedback, attachment_ids=attachment_ids)
    
    ### FEAT : DATE DEADLINE UPDATE 28/03/2024
    def write(self, vals):
        if 'date_deadline' in vals:
            for activity in self:
                if activity.res_model and activity.res_model == 'crm.lead' and activity.res_id > 0:
                    lead = self.env['crm.lead'].browse(activity.res_id)
                    line = [(0, 0, {
                        'lead_id': int(activity.res_id),
                        'name': '%s - %s' % (str(activity.activity_type_id and activity.activity_type_id.name or '/'), str(vals['date_deadline'])),
                        'user_id': self.env.user.id or False,
                        'date_change': str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) or False,
                        'old_date_activity': activity.date_deadline
                    })]
                    
                    lead.lead_date_dealine_line = line

        return super().write(vals)