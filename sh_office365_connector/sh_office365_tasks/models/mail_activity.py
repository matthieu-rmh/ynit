# Part of Softhealer Technologies.
from odoo import fields, models, _


class AddField(models.Model):
    _inherit = 'mail.activity'
    
    sh_tasks_id = fields.Char("Task ID")
