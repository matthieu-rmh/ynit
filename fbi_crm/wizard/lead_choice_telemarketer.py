# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

class LeadChoiceTelemarketer(models.TransientModel):
    _name = 'crm.lead.choise.telemarketer'
    _description = 'Choice telemarketer for doubt'
    
    @api.model
    def default_get(self, fields):
        defaults = super(LeadChoiceTelemarketer, self).default_get(fields)
        crm_active_ids = self.env.context.get('active_ids')
        for lead in crm_active_ids:
            crm_lead = self.env['crm.lead'].browse(lead)
            if crm_lead.rdv_pour_confirmation:
                defaults['rdv_pour_confirmation'] = "%s" % (crm_lead.rdv_pour_confirmation)
        return defaults

    # telemarketer_id = fields.Many2one('res.users', string="Télévendeur/Commercial", 
    #                                   # default=lambda self: self.env.user, 
    #                                   domain=lambda self: [
    #                                       ('groups_id', 'in', self.env.ref('fbi_crm.group_fbi_crm_telemarketer').id)
    #                                 ])
    
    telemarketer_id = fields.Many2one('res.users', string="Télévendeur/Commercial", default=lambda self: self.env.user)
    rdv_pour_confirmation = fields.Text('RDV à Confirmer')
    
    def wizard_action_direction_pass_to_ctrl_qualite(self):
        crm_active_ids = self.env.context.get('active_ids')
        for lead in crm_active_ids:
            crm_lead = self.env['crm.lead'].browse(lead)
            crm_lead.telemarketer_id = self.telemarketer_id and self.telemarketer_id.id or False
            crm_lead.rdv_pour_confirmation = self.rdv_pour_confirmation
            crm_lead.qualif_fbi_commentaire_si_revision = self.rdv_pour_confirmation
            if self.env.context.get('rappel_j_7') and self.env.context.get('date_deadline'):
                crm_lead.stage_id = crm_lead._get_res_id('fbi_crm.stage_rdv_attente_conf_J_7')
                crm_lead._create_activity_if_not_exists('fbi_crm.mail_activity_type_rappel_J7', date_deadline=self.env.context.get('date_deadline'), notes='Confirmer le RDV SVP avant 7 jours.')
                ### EMAIL VENDEUR SEULEMNT
                
                _logger.info('================== PAR DEFAUT ENVOI VISIO / TELEMARKETER ====================')
                template_mail = 'fbi_crm.fbi_crm_template_meeting_confirmed_mail'
                to_emails = ',' .join([
                        user.email for user in (
                            self.env.ref('fbi_crm.group_fbi_crm_dm').users | 
                            self.env.ref('fbi_crm.group_fbi_crm_manager').users) if user.email
                        ])
                if self.env.context.get('rdv_physique'):
                        _logger.info('================== ENVOI PHYSIQUE / TELEMARKETER ====================')
                        to_emails_physique = self.env['fbi.crm.lead.emails.to'].sudo().search([('name', '=', 'RDV_PHYSIQUE')]).remove_to
                        to_emails_physique_remove = to_emails_physique.split(',')
                        template_mail = 'fbi_crm.fbi_crm_template_meeting_confirmed_mail_presentiel'
                        to_emails = ',' .join([
                                user.email for user in (
                                    self.env.ref('fbi_crm.group_fbi_crm_dm').users | 
                                    self.env.ref('fbi_crm.group_fbi_crm_manager').users) if user.email and user.email not in to_emails_physique_remove
                            ])
                        
                for rdvTo in self.env['fbi.crm.lead.emails.to'].sudo().search([('name', '=', 'RDV')]):
                    rdvUsers = rdvTo.user_ids and rdvTo.user_ids.ids
                    if crm_lead.user_id and crm_lead.user_id.id in rdvUsers:
                        to_emails_rdv_join = rdvTo.add_to
                        to_emails_rdv_join = to_emails_rdv_join.split(',')
                        to_emails += ',' + ',' .join(str(x) for x in to_emails_rdv_join)
                        _logger.info('================== AUTRES DESTINATAIRES / TELEMARKETER ====================')
                        _logger.info(to_emails)
                            
                self.env.ref(template_mail).send_mail(crm_lead.id,
                        email_values={
                            'email_to': crm_lead.user_id.email,
                            'email_cc': to_emails,
                        }, force_send=True)
                
                # self.env.ref('fbi_crm.fbi_crm_template_meeting_confirmed_mail').send_mail(crm_lead.id,
                #     email_values={
                #         'email_to': crm_lead.user_id.email,
                #         'email_cc': ','.join([
                #                             user.email for user in (
                #                                 self.env.ref('fbi_crm.group_fbi_crm_dm').users |
                #                                 self.env.ref('fbi_crm.group_fbi_crm_manager').users
                #                             )
                #                             if user.email
                #                         ]),
                #     }, force_send=True)
                ### EMAIL VENDEUR - PROSPECT
                # crm_lead._send_propsect_mail()
            else:
                crm_lead.stage_id = crm_lead._get_res_id('fbi_crm.stage_rdv_attente_conf_72h')
                crm_lead._create_activity_if_not_exists('fbi_crm.mail_activity_type_rappel_72h')
            break
        return True