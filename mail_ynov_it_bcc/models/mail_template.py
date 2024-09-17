from odoo import fields, models, tools

CC_BCC_FIELDS = {
    "email_cc": "partner_cc_ids",
    "email_bcc": "partner_bcc_ids",
}

class MailTemplate(models.Model):
    _inherit = "mail.template"

    email_bcc = fields.Char("Bcc", help="Blind cc recipients (placeholders may be used here)")
    
    
    def generate_email(self, res_ids, fields):
        if 'email_bcc' not in fields:
            fields.append('email_bcc')
        return super().generate_email(res_ids, fields)