# Part of Softhealer Technologies.
from odoo import fields, models , _
import requests
import datetime
from odoo.exceptions import UserError


class MailConfig(models.Model):
    _inherit = 'sh.office365.base.config'

    import_mail = fields.Boolean("Import Mail")
    auto_schedule_mail = fields.Boolean("Auto Schedule Mails")
    manage_log_mail = fields.Boolean("Manage Log History Mail")

    def mail_log(self, error, state='error', operation='import'):
        if self.manage_log_mail:
            self._log(error, 'mail', state, operation)

    def mail_import(self):
        if not self.auth_token:
            raise UserError(_("Generate the creds first !"))
        if not self.import_mail:
            raise UserError(_("Select Import to import mails"))
        self.RefreshToken()

        try:
            get_mail_folders = "https://graph.microsoft.com/v1.0/me/messages?$select=bodyPreview,hasAttachments,receivedDateTime,sender,subject&$top=1000"
            headers = {
                "Authorization": self.auth_token,
                "Content-Type": "application/json"
            }
            response = requests.get(url=get_mail_folders, headers=headers)
            res_json = response.json()
            values = res_json['value']
            for data in values:
                sender_name = False
                sender_email = False
                if data.get('sender', False):
                    sender_name = data['sender']['emailAddress']['name']
                    sender_email = data['sender']['emailAddress']['address']
                subject = data['subject']
                body = data['bodyPreview']
                unique_id = data['id']
                attachment = data['hasAttachments']
                received_date = data['receivedDateTime']
                dates = datetime.datetime.strptime(received_date, "%Y-%m-%dT%H:%M:%SZ")
                domain = [('email', '=', sender_email)]
                find_sender = self.env['res.partner'].search(domain, limit=1)
                vals = {
                    'model': 'res.partner',
                    'subject': subject,
                    'body': body,
                    'unique_id': unique_id,
                    'date': dates,
                    'message_type': 'email'
                }
                if attachment:
                    get_attachment = 'https://graph.microsoft.com/v1.0/me/messages/%s/attachments' % (unique_id)
                    resp_attachment = requests.get(url=get_attachment, headers=headers)
                    res_json_attachment = resp_attachment.json()
                    data = res_json_attachment['value']
                    for x in data:
                        if 'contentBytes' in x and x['contentBytes']:
                            attach_bytes = x['contentBytes']
                            name = x['name']
                            content_type = x['contentType']
                            attach_id = x['id']
                            base64_bytes = attach_bytes.encode()
                            ir_vals = {
                                'name': name,
                                'type': 'binary',
                                'datas': base64_bytes,
                                'res_model': 'res.partner',
                                'attachment_id': attach_id
                            }
                            if find_sender:
                                vals['author_id'] = find_sender.id
                                vals['res_id'] = find_sender.id
                                ir_vals['res_id'] = find_sender.id
                            else:
                                create_vals = {
                                    'name': sender_name,
                                    'email': sender_email
                                }
                                create_instant_sender = self.env['res.partner'].create(create_vals)
                                vals['author_id'] = create_instant_sender.id
                                vals['res_id'] = create_instant_sender.id
                                ir_vals['res_id'] = create_instant_sender.id
                                domain = [('attachment_id', '=', attach_id)]
                                find_attachments = self.env['ir.attachment'].search(domain)
                                if find_attachments:
                                    vals['attachment_ids'] = [(6, 0, [find_attachments .id])]
                                else:
                                    upload_attachment = self.env['ir.attachment'].create(ir_vals)
                                    vals['attachment_ids'] = [(6, 0, [upload_attachment.id])]
                            domain = [('unique_id', '=', unique_id)]
                            find_mails = self.env['mail.message'].search(domain, limit=1)
                            if find_mails:
                                find_mails.write(vals)
                            else:
                                self.env['mail.message'].create(vals)
                else:
                    if find_sender:
                        vals['author_id'] = find_sender.id
                        vals['res_id'] = find_sender.id
                    elif sender_name:
                        create_instant_sender = self.env['res.partner'].create({
                            'name': sender_name,
                            'email': sender_email
                        })
                        vals['author_id'] = create_instant_sender.id
                        vals['res_id'] = create_instant_sender.id
                    domain = [('unique_id', '=', unique_id)]
                    find_mails = self.env['mail.message'].search(domain, limit=1)
                    if find_mails:
                        find_mails.write(vals)
                    else:
                        check = self.env['mail.message'].create(vals)
            self.mail_log("Successully Done", "success")
        except Exception as e:
            self.mail_log(e)

    def _office365_mail_cron(self):
        all_creds = self.env['sh.office365.base.config'].search([])
        for creds in all_creds:
            if creds.auto_schedule_mail:
                creds.mail_import()
