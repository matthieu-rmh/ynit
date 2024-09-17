from odoo import models, fields, api


class FbiCrmCodeRelance(models.Model):
    _name = 'crm.code.naf.family'
    _description = "Famille des codes NAF"
    _order = 'code ASC'

    code = fields.Char(string='Code', required=True)
    label = fields.Char(string='Label')
    name = fields.Char(string='Nom', compute="_compute_name", store=True, readonly=True)

    @api.depends('code', 'label')
    def _compute_name(self):
        for record in self:
            record.name = str(record.code) + ' - ' + record.label if record.code and record.label else ""