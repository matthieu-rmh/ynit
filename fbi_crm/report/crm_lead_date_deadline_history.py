# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools, api


class leadDateDealineActivityReport(models.Model):
    """ CRM Lead Date Deadline Analysis """

    _name = "crm.date.deadline.activity.report"
    _auto = False
    _description = "CRM Lead Date Deadline Analysis"
    _rec_name = 'id'

    date_change = fields.Datetime('Date de changement', readonly=True)
    lead_create_date = fields.Datetime('Date de création de la fiche', readonly=True)
    user_id = fields.Many2one('res.users', 'Commercial', readonly=True)
    telemarketer_id = fields.Many2one('res.users', 'TelPro', readonly=True)
    potential_logiciel_comptable = fields.Char(string='Logiciel Comptable', readonly=True)
    code_relance_id = fields.Many2one('crm.code_relance', 'Code Relance', readonly=True)
    activity_date_deadline = fields.Date("Date limite de l'activité à venir", readonly=True)
    campaign_id = fields.Many2one('utm.campaign', "Campagne", readonly=True)
    stage_id = fields.Many2one('crm.stage', "Etape", readonly=True)
    crm_lead_id = fields.Many2one('crm.lead', "Opportunité", readonly=True)
    partner_id = fields.Many2one('res.partner', 'Partenaire', readonly=True)
    active = fields.Boolean('Active', readonly=True)

    def _select(self):
        return """
            SELECT
                m.id,
                m.date_change,
                l.create_date AS lead_create_date,
                l.user_id,
                l.telemarketer_id,
                l.potential_logiciel_comptable,
                l.code_relance_id,
                (SELECT date_deadline FROM mail_activity WHERE res_id = l.id AND res_model = 'crm.lead' ORDER BY date_deadline DESC LIMIT 1) AS activity_date_deadline,
                l.campaign_id,
                l.stage_id,
                l.id as crm_lead_id,
                l.partner_id,
                l.active
        """

    def _from(self):
        return """
            FROM crm_lead_date_dealine_history AS m
        """

    def _join(self):
        return """
            JOIN crm_lead AS l ON m.lead_id = l.id
        """

    def _where(self):
        return """
            WHERE True
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
