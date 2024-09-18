
from odoo import models, fields, api
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    legal_entity_name = fields.Char(string="Legal entity name")
    entity_type = fields.Char(string="Entity type")
    capital = fields.Char(string="Capital")
    registration = fields.Char(string="Registration")
    entity_number = fields.Char(string="Entity number")
    head_office = fields.Char(string="Head office")
    representative_title = fields.Char(string="Representative title")
    representative = fields.Char(string="Representative name")
    representative_function = fields.Char(string="Representative function")

    current_partner = fields.Many2one('res.partner', compute='_compute_current_partner', store=False)

    def _compute_current_partner(self):
        for rec in self:
            rec.current_partner = self.env['res.partner'].sudo().search([('name', '=', "Ynov'iT Services")])[0]

