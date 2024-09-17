from odoo import models, fields, api


class FbiCrmCommercialAnnonce(models.Model):
    _name = 'crm.commercial_annonce'
    _description = "Nom du commercial annoncé au prospect"

    name = fields.Char('Name', required=True, translate=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Advertised commercial name already exists !"),
    ]
