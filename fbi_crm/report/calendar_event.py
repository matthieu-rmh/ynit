# -*- coding: utf-8 -*-

from odoo import fields, models, tools, api


class FbiCalendarEventReport(models.Model):
    _name = 'crm.fbi.calendar.report'
    _auto = False
    _description = "RDV Activity Analysis"
    _rec_name = 'id'
    
    create_date = fields.Date('Date de prise de RDV', readonly=True)
    day_date = fields.Char('Jour prise de RDV', readonly=True)
    telemarketer_id = fields.Many2one('res.users', string="Télépro", readonly=True)
    commercial_annonce_id = fields.Many2one('crm.commercial_annonce', string="Prête Nom", readonly=True)
    campaign_id = fields.Many2one('utm.campaign', string="Nom de Campagne", readonly=True)
    user_id = fields.Many2one('res.users', string='Nom du Commercial', readonly=True)
    partner_name = fields.Char('RAISON SOCIALE', readonly=True)
    company_siret = fields.Char('SIRET', readonly=True)
    city = fields.Char('VILLE', readonly=True)
    contact_name = fields.Char("NOM DE L'INTERLOCUTEUR", readonly=True)
    function = fields.Char("FONCTION", readonly=True)
    meeting_date = fields.Date('Date de RDV', readonly=True)
    meeting_hour = fields.Char("Heure", readonly=True)
    company_id = fields.Many2one('res.company', 'Société', readonly=True)
    
    def _select(self):
        return """
            SELECT
                ev.id,
                ev.create_date::date,
                to_char(ev.create_date, 'TMDay') AS day_date,
                l.telemarketer_id,
                l.commercial_annonce_id,
                l.campaign_id,
                l.user_id,
                l.partner_name,
                l.company_siret,
                l.city,
                l.contact_name,
                l.function,
                ev.start::date AS meeting_date,
                ev.start::time AS meeting_hour,
                l.company_id
        """
        
    def _from(self):
        return """
            FROM calendar_event AS ev
        """
        
    def _join(self):
        return """
            JOIN crm_lead AS l ON ev.res_id = l.id
        """
        
    def _where(self):
        disccusion_subtype = self.env.ref('mail.mt_comment')
        return """
            WHERE
                ev.res_model = 'crm.lead' AND ev.active = true
        """
        
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                %s
                %s
                %s
            )
        """ % (self._table, self._select(), self._from(), self._join(), self._where())
        )