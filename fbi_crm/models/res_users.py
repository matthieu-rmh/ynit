
from odoo import api, fields, models


class FbiCrmResUsers(models.Model):
    _inherit = "res.users"

    default_commercial_annonce_id = fields.Many2one('crm.commercial_annonce', string='Commercial annoncé par défaut')
    vendor_ms_calendar_url = fields.Char(string="URL de calendrier du vendeur")
