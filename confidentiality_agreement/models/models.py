
from odoo import models, fields, api
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    current_company = fields.Many2one('res.company', compute='_compute_current_company', store=False)

    def _compute_current_company(self):
        for rec in self:
            rec.current_company = self.env.company

    # def write(self, vals):
    #     raise UserError(str(self.current_company))
