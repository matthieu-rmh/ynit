
import io
import csv
import base64
import uuid

from odoo import models, fields, api
from odoo.exceptions import AccessError, UserError
from odoo.tools.translate import _
from odoo import modules, tools


class FbiMeeting(models.Model):
    _inherit = "calendar.event"
    
    ###### CSV - ATTACH EVENTS TO CRM
    def _attach_lead_meeting(self):
        meeting_name = tools.misc.file_path('fbi_crm/data/meeting.csv')
        with open(meeting_name, 'r', encoding = 'utf8') as ppfile:
            csvreader = csv.reader(ppfile, delimiter=';')
            no_lead = []
            for row in csvreader:
                meetings = self.search([('name', 'like', row[0].strip() + '%')])
                if meetings:
                    for m in meetings:
                        leads = self.env['crm.lead'].sudo().search([('company_siret', 'like', row[1].strip() + '%')])
                        for lead in leads:
                            meet = self.browse(m.id)
                            meet.res_id = lead.id
                            meet.res_model = 'crm.lead'
                else:
                    no_lead.append([row[0].strip(), row[1].strip()])
            if no_lead:
                csv_buffer = io.StringIO()
                csv_writer = csv.writer(csv_buffer, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                csv_writer.writerows(no_lead)
                csv_buffer.seek(0)
                attachment = self.env['ir.attachment'].sudo().create({
                    'name': 'no_lead_events.csv',
                    'type': 'binary',
                    'datas': base64.b64encode(csv_buffer.getvalue().encode()),
                })
        return True
    
    @api.model
    def default_get(self, fields):
        defaults = super(FbiMeeting, self).default_get(fields)
        if defaults.get('opportunity_id'):
            lead = self.env['crm.lead'].browse(int(defaults['opportunity_id']))
            if lead.user_id:
                defaults['user_id'] = lead.user_id and lead.user_id.id or False
                defaults['telemarketer_id'] = lead.telemarketer_id and lead.telemarketer_id.id or False
                defaults['partner_ids'] = [lead.user_id and lead.user_id.partner_id and lead.user_id.partner_id.id or False]
                # defaults['partner_ids'] = [lead.user_id and lead.user_id.partner_id and lead.user_id.partner_id.id or False]
        return defaults

    # region Fields
    state = fields.Selection([('draft', 'Brouillon'),
                              ('validation_manager', 'Validation par manager'),
                              ('validation_dm', 'Validation par DM'),
                              ('validated', 'Validé')],
                             required=True,
                             default='draft')
    telemarketer_id = fields.Many2one('res.users', string="Organisateur ", default=lambda self: self.env.user,
                                      domain=lambda self: [('groups_id', 'in',
                                                            self.env.ref('fbi_crm.group_fbi_crm_telemarketer').id)])
    
    #### FIND LEAD
    def find_lead_event(self):
        self.ensure_one()
        if self.res_id and self.res_model == 'crm.lead':
            return self.env['crm.lead'].browse(self.res_id)

    # endregion
    
    @api.onchange('videocall_location')
    def _onchange_videocall_location(self):
        for event in self:
            if event.videocall_location:
                event.write({
                    'description': '%s\n\nLIEN VISIO : %s' % (event.description or '', event.videocall_location)
                })
    # region CRUD
    
    #### FEAT REMOVE PARTICIPANTS RDV
    def remove_participants(self):
        self.sudo().partner_ids = False
        if self.opportunity_id:
            lead = self.sudo().opportunity_id
            lead.stage_id = lead._get_res_id('fbi_crm.stage_annule_client')
            lead.event_customer_decline = True
        
    @api.model_create_multi
    def create(self, vals_list):
        """ create(vals_list) -> records

         Surcharge pour gérer la double validation des RDV pris par les télé-vendeurs.
         Si on a une opportunité liée, c'est qu'on vient de CRM et du coup :
          - On considère qu'on est télé-vendeur, on force le statut à "VALIDATION PAR MANAGER"
          - On retire le client des invités pour qu'il ne reçoive pas de mail à ce moment-là
          - On envoie un mail de demande de validation au manager

         Creates new records for the model.

         The new records are initialized using the values from the list of dicts
         ``vals_list``, and if necessary those from :meth:`~.default_get`.

         :param Union[list[dict], dict] vals_list:
             values for the model's fields, as a list of dictionaries::

                 [{'field_name': field_value, ...}, ...]

             For backward compatibility, ``vals_list`` may be a dictionary.
             It is treated as a singleton list ``[vals]``, and a single record
             is returned.

             see :meth:`~.write` for details

         :return: the created records
         :raise AccessError: if the current user is not allowed to create records of the specified model or
                             ``self.env.context.get('default_opportunity_id')`` is set and user isn't in group
                             ``'fbi_crm.group_fbi_crm_telemarketer'``
         :raise ValidationError: if user tries to enter invalid value for a selection field
         :raise ValueError: if a field name specified in the create values does not exist.
         :raise UserError: if a loop would be created in a hierarchy of objects a result of the operation
           (such as setting an object as its own parent)
         """
        # On ne redéfinit le comportment que si l'on provient de CRM
        # Dans ce cas, default_opportunity_id est défini
        default_opportunity_id = self.env.context.get('default_opportunity_id')

        if default_opportunity_id:
            if not self.env.user.has_group('fbi_crm.group_fbi_crm_telemarketer'):
                raise AccessError(_("Vous n'avez pas les droits de créer un évènement à partir de CRM"))

            # Par sécurité, on refait ici ce qui est écrit dans le fichier crm_lead.py
            default_partner_ids = self.env.context.get('default_partner_ids')
            opportunity_id = self.env['crm.lead'].browse(default_opportunity_id)
            partner_id_to_remove = opportunity_id.partner_id
            
            
            ##### FEAT TEST IF RDV EXIST AND NOT DECLINE
            meeting_lead = self.env['calendar.event'].sudo().search([
                                                        ('res_id', '=', opportunity_id.id), 
                                                        ('res_model', '=', 'crm.lead')
                                                    ], order='id DESC', limit=1)
            rdv_declined = False
            for att in meeting_lead.attendee_ids:
                if att.state == 'declined':
                    rdv_declined = True

            if opportunity_id.calendar_event_count > 0 and not rdv_declined:
                raise UserError(_("Un RDV est déjà pris pour cette opportunité"))

            if opportunity_id.stage_id.id != self.env['ir.model.data'].sudo()._xmlid_to_res_id('fbi_crm.stage_rdv'):
                raise UserError(_("L'opportunité doit être à l'état RDV pour qu'un RDV puisse être pris"))

            # Suppression du partenaire pour qu'il ne soit pas dans la liste des participants
            if partner_id_to_remove.id in default_partner_ids:
                default_partner_ids.remove(partner_id_to_remove.id)

            # On considère qu'on est télé-vendeur, on force le statut à "VALIDATION PAR MANAGER"
            for vals in vals_list:
                vals.update({'state': 'validation_manager'})
            
            #### FIX 04/03/2024
            ## SET VISION IF URL EXIST
            if opportunity_id and isinstance(vals_list, list) and vals_list[0].get('videocall_location') and vals_list[0]['videocall_location']:
                opportunity_id.rdv_visio = True
                opportunity_id.email_template_confirm_choice = 'generic_visio'

        # Super 
        event = super().create(vals_list)
        if default_opportunity_id:
            # Envoi mail de validation si nécessaire
            for sub_event in event:
                ##### FIX STATUT RESTE SUR RDV #####
                # sub_event._change_opportunity_stage('fbi_crm.stage_validation_manager')
                sub_event._send_validation_mail()
                
                ### DEMANDE APRES MISE EN PROD 10/04/2024
                # sub_event._send_prise_rdv_vendeur()
                ### DEMANDE APRES MISE EN PROD 10/04/2024
                
            # On remet le partenaire dans le contexte
            default_partner_ids.append(partner_id_to_remove.id)
        return event

    def write(self, vals):
        # On ne fait aucun contrôle/traitement si on est en train de synchroniser les évènements avec Outlook
        if 'need_sync_m' not in vals:
            # Si on a à faire qu'à une seule valeur
            if len(self) == 1:
                self._check_access_modify_or_delete()
                if self.state == 'draft':
                    vals.update({'state': 'validation_manager'})
            # Sinon
            else:
                for record in self:
                    record._check_access_modify_or_delete()
        
        #### FIX : UPDATE DATE RDV
        previous_attendees = self.attendee_ids
        event = super().write(vals)
        current_attendees = self.filtered('active').attendee_ids
        if not self.env.context.get('is_calendar_event_new') and 'start' in vals:
            start_date = fields.Datetime.to_datetime(vals.get('start'))
            # Only notify on future events
            # if start_date and start_date >= fields.Datetime.now():
            #     (current_attendees & previous_attendees)._send_mail_to_attendees_dematicall()
        #### FIX : UPDATE DATE RDV
        return event
        # return super().write(vals)

    def unlink(self):
        for record in self:
            if record.opportunity_id and record.opportunity_id.is_dematicall():
                record._check_access_modify_or_delete()
                ###### SEND CANCEL RDV
                record._send_cancellation_to_attendees()

        return super().unlink()
    # endregion

    # region Actions
    def action_validate(self):
        is_dm = self.env.user.has_group('fbi_crm.group_fbi_crm_dm')
        is_manager = self.env.user.has_group('fbi_crm.group_fbi_crm_manager')
        for event in self:
            if is_dm:
                # Si le meeting est validé, alors on s'assure que le lead fait partie des participants
                event.partner_ids |= event.opportunity_id.partner_id
                event.state = 'validated'
                event._change_opportunity_stage('fbi_crm.stage_valide')

            elif is_manager and event.state in ['draft', 'validation_manager']:
                # Si le meeting n'est pas validé, alors on s'assure que le lead ne fait pas partie des
                # participants
                event.partner_ids -= event.opportunity_id.partner_id
                event.state = 'validation_dm'
                event._change_opportunity_stage('fbi_crm.stage_validation_dm')

            else:
                raise AccessError(_("Vous ne pouvez pas valider cet évènement"))

            # Envoi du mail de validation si nécessaire
            event._send_validation_mail()

        return True

    def action_reject(self):
        is_dm = self.env.user.has_group('fbi_crm.group_fbi_crm_dm')

        for event in self:
            if is_dm and event.state != 'validated':
                # S'il n'y a plus d'évènement lié à l'opportunité, on repasse cette dernière à l'état RDV
                if event.opportunity_id.calendar_event_count < 2:
                    event._change_opportunity_stage('fbi_crm.stage_rdv')
                event.unlink()
            else:
                raise AccessError(_("Vous ne pouvez pas refuser cet évènement"))
        return True
    # endregion

    # region Protected Functions
    def _check_access_modify_or_delete(self):
        if not self.env.user.has_group('fbi_crm.group_fbi_crm_dm') and not self.env.is_superuser():
            if self.env.user.has_group('fbi_crm.group_fbi_crm_manager'):
                for event in self:
                    if event.state == 'validated' or event.state == 'validation_dm':
                        raise AccessError(_("Vous ne pouvez pas modifier/supprimer les évènements à l'état validé ou en"
                                            " validation par DM"))
            elif self.env.user.has_group('fbi_crm.group_fbi_crm_telemarketer'):
                for event in self:
                    if event.state != 'draft':
                        raise AccessError(_("Vous ne pouvez pas modifier/supprimer les évènements dans un autre état "
                                            "que brouillon"))
            else:
                raise AccessError(_("Vous ne pouvez pas modifier/supprimer les évènements issus de CRM"))

    ##### FIX : SEND EMAIL AFTER CANCEL RDV
    def _send_cancellation_to_attendees(self):
        for attendee in self.attendee_ids:
            to_emails = self.opportunity_id and self.opportunity_id.user_id and self.opportunity_id.user_id.email or False
            for rdvTo in self.env['fbi.crm.lead.emails.to'].sudo().search([('name', '=', 'RDV_CANCEL')]):
                to_emails_rdv_join = rdvTo.add_to
                to_emails_rdv_join = to_emails_rdv_join.split(',')
                to_emails += ',' + ',' .join(str(x) for x in to_emails_rdv_join)
                
            self.env.ref('fbi_crm.fbi_crm_template_meeting_cancelled_mail').send_mail(
                attendee.id,
                email_values={
                    'email_to': to_emails
                }, force_send=True)
            break
    
    ##### FIX : SEND EMAIL TO USER_ID
    def _send_prise_rdv_vendeur(self):
        if self.state == 'validation_manager':
            #### FIX : Mail sur nouveau meeting au statut "validation par manager" pour Commercial
            if self.res_id and self.res_model == 'crm.lead':
                opportunity_id = self.env['crm.lead'].browse(self.res_id)
                for attendee in self.attendee_ids:
                    self.env.ref('fbi_crm.fbi_crm_template_meeting_vendor_invitation_mail').send_mail(attendee.id, 
                                                                                            email_values={
                                                                                                'email_to': opportunity_id.user_id and opportunity_id.user_id.email or False,
                                                                                            }, force_send=True)
                    break
    
    def _send_validation_mail(self):
        if self.state == 'validation_manager':
            # 1er mail sur nouveau meeting au statut "validation par manager" au manager pour qu'il valide
            self.env.ref('fbi_crm.fbi_crm_template_meeting_need_validation_manager_mail').send_mail(
                self.id,
                email_values={
                    'email_to': ','.join([user.email for user in
                                          (self.env.ref('fbi_crm.group_fbi_crm_manager').users |
                                           self.env.ref('fbi_crm.group_fbi_crm_mail_copy').users)]),
                },
                force_send=True,
            )
        elif self.state == 'validation_dm':
            # 2ᵉ mail au groupe DM pour validation DM
            self.env.ref('fbi_crm.fbi_crm_template_meeting_need_validation_dm_mail').send_mail(
                self.id,
                email_values={
                    'email_to': ','.join([user.email for user in
                                          (self.env.ref('fbi_crm.group_fbi_crm_dm').users |
                                           self.env.ref('fbi_crm.group_fbi_crm_mail_copy').users)]),
                },
                force_send=True,
            )

    def _change_opportunity_stage(self, stage_xmlid):
        if self.opportunity_id:
            stage = self.env['ir.model.data'].sudo()._xmlid_to_res_id(stage_xmlid)

            if stage:
                self.with_context(from_event=True).opportunity_id.stage_id = stage
    # endregion
