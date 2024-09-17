from odoo import models, fields, api


class FbiCrmCodeRelance(models.Model):
    _name = 'crm.code_relance'
    _description = "Code de relance associé à l'opportunité"
    _order = 'code ASC'

    # region Fields
    code = fields.Integer(required=True)
    name = fields.Char(compute="_compute_name", store=True, readonly=True)
    label = fields.Char(required=True)
    state = fields.Selection([('en_cours', 'En cours'),
                              ('non_exploitable', 'Non exploitable'),
                              ('rdv', 'RDV')],
                             required=True,
                             default='rdv')

    # endregion

    # region Functions

    @api.depends('code', 'label')
    def _compute_name(self):
        for record in self:
            record.name = str(record.code) + ' - ' + record.label if record.code and record.label else ""

    # endregion
