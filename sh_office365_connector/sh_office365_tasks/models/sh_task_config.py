# Part of Softhealer Technologies.
from odoo import fields, models, _
import requests
from datetime import datetime
import json
from odoo.exceptions import UserError
import re


class OfficeTask(models.Model):
    _inherit = 'sh.office365.base.config'

    list_created = fields.Boolean("List Created", default=True)
    once_created_ids = fields.Char("Once Created")
    import_task = fields.Boolean("Import Tasks")
    export_task = fields.Boolean("Export Tasks")
    auto_schedule_task = fields.Boolean("Auto Schedule Tasks")
    manage_log_task = fields.Boolean("Manage Log History Tasks")

    def sh_get_tasks(self):
        self.RefreshToken()
        if self.auth_token:
            try:
                task_list_url = "https://graph.microsoft.com/v1.0/me/todo/lists"
                headers = {
                            "Authorization": self.auth_token,
                            "Content-Type": "application/json"
                        }
                response = requests.get(url=task_list_url, headers=headers)
                res_json = response.json()
                list_ids = [x['id'] for x in res_json['value']]
                json_value_list = []
                for ids in list_ids:
                    tasks_url = "https://graph.microsoft.com/v1.0/me/todo/lists/%s/tasks" % (ids)
                    response_tasks = requests.get(url=tasks_url, headers=headers)
                    res_jsons = response_tasks.json()
                    json_value_list.append(res_jsons)
                return json_value_list
            except:
                raise UserError(_("Plz Generate Token and Try Again"))

    def task_import(self):
        json_list = self.sh_get_tasks()
        return_vals = []
        title_list = []
        domain = [('model', '=', 'res.partner')]
        res_model_id = self.env['ir.model'].search(domain, limit=1)
        if json_list:
            try:
                for res_json in json_list:
                    email_link = res_json['@odata.context']
                    emails = re.findall(r"[a-z0-9\.\-+_]+%40[a-z0-9\.\-+_]+\.[a-z]+", email_link)
                    if len(emails) > 1:
                        final_emails = emails[0].replace("%40", "@")
                        domain = [('login', '=', final_emails)]
                        find_users = self.env['res.users'].search(domain, limit=1)
                        if not find_users:
                            raise UserError(_("No User found with regisered mail"))
                        user_id = find_users.id
                    else:
                        user_id = self.env.user
                    partner_id = user_id.partner_id.id
                    for values in res_json['value']:
                        status = values['status'] if 'status' in values else False
                        if status == 'notStarted':
                            duedate = values['dueDateTime'] if 'dueDateTime' in values else False
                            sh_date = duedate['dateTime'] if 'dateTime' in values else False
                            title = values['title'] if 'title' in values else False
                            ids = values['id'] if 'id' in values else False
                            title_list.append(title)
                            description = values['body'] if 'body' in values else False
                            note = description['content'] if 'content' in values else False
                            vals = {
                                'user_id': user_id.id,
                                'date_deadline': sh_date,
                                'summary': title,
                                'note': note,
                                'activity_type_id':self.env.ref('mail.mail_activity_data_todo').id,
                                'res_id': partner_id,
                                'res_model': 'res.partner',
                                'res_model_id':res_model_id.id,
                                'sh_tasks_id': ids
                            }
                            domain = [('sh_tasks_id', '=', ids)]
                            already_created = self.env['mail.activity'].search(domain, limit=1)
                            if already_created and self.import_task:
                                self.env['mail.activity'].sudo().write(vals)
                            elif self.import_task:
                                self.env['mail.activity'].sudo().create(vals)
                if self.manage_log_task and self.import_task:
                    vals = {
                            "name": self.name,
                            "state": "success",
                            "error": "Successully Done",
                            "base_config_id": self.id,
                            "datetime": datetime.now(),
                            "field_type": "task",
                            "operation": "import"
                        }
                    self.env['sh.office365.base.log'].create(vals)
            except Exception as e:
                if self.manage_log_task and self.import_task:
                    vals = {
                            "name": self.name,
                            "state": "error",
                            "error": e,
                            "base_config_id": self.id,
                            "datetime": datetime.now(),
                            "field_type": "task",
                            "operation": "import"
                        }
                    self.env['sh.office365.base.log'].create(vals)
            # dict for reusing data
            if title_list:
                vals = {
                    'partner_id': partner_id,
                    'res_model_id': res_model_id.id,
                    'summary': title_list,
                    'user_id':user_id
                }
                return_vals.append(vals)
            return return_vals
        else:
            if self.manage_log_task:
                vals = {
                        "name": self.name,
                        "state": "error",
                        "error": "Failure",
                        "base_config_id": self.id,
                        "datetime": datetime.now(),
                        "field_type": "task",
                        "operation": "import"
                    }
                self.env['sh.office365.base.log'].create(vals)

    def task_export(self):
        if self.import_task:
            self.task_import()
        if self.export_task:
            json_list = self.task_import()
            list_task = []
            partner_id_list = []
            user_id_list = []
            res_model_id_list = []
            for values in json_list:
                partner_id_list.append(values['partner_id'])
                res_model_id_list.append(values['res_model_id'])
                user_id_list.append(values['user_id'])
                task_list = values['summary']
                for x in task_list:
                    list_task.append(x)
            if res_model_id_list and partner_id_list:
                domain = [('res_model_id', '=', res_model_id_list[0]), ('res_id', '=', partner_id_list[0])]
                all_task = self.env['mail.activity'].search(domain)
                headers = {
                            "Authorization": self.auth_token,
                            "Content-Type": "application/json"
                        }
                try:
                    for tasks in all_task:
                        if tasks.summary in list_task:
                            continue
                        elif tasks.activity_type_id.id == self.env.ref('mail.mail_activity_data_todo').id and tasks.user_id.id == user_id_list[0]:
                            if self.list_created:
                                self.list_created = False
                                create_list_url = "https://graph.microsoft.com/v1.0/me/todo/lists"
                                payload = {
                                    'displayName': 'Odoo Task'
                                }
                                create_list_response = requests.post(url=create_list_url, headers=headers, data=json.dumps(payload))
                                self.once_created_ids = create_list_response.json()['id']
                            create_task_url = "https://graph.microsoft.com/v1.0/me/todo/lists/%s/tasks" % (self.once_created_ids)
                            payload = {
                                "title": tasks.summary,
                                "body": {
                                    "content": tasks.note
                                },
                                "dueDateTime": {
                                    "dateTime": tasks.date_deadline,
                                    "timeZone": "UTC"
                                }
                            }
                            res = requests.post(url=create_task_url, headers=headers, data=json.dumps(payload, indent=4, sort_keys=True, default=str))
                            data_load = res.text
                            valss = {
                                'sh_tasks_id': data_load['id']
                            }
                            tasks.write(valss)
                    if self.manage_log_task:
                        vals = {
                            "name": self.name,
                            "state": "success",
                            "error": "Successully Done",
                            "base_config_id": self.id,
                            "datetime": datetime.now(),
                            "field_type": "task",
                            "operation": "export"
                        }
                        self.env['sh.office365.base.log'].create(vals)
                except Exception as e:
                    if self.manage_log_task:
                        vals = {
                            "name": self.name,
                            "state": "error",
                            "error": e,
                            "base_config_id": self.id,
                            "datetime": datetime.now(),
                            "field_type": "task",
                            "operation": "export"
                        }
                        self.env['sh.office365.base.log'].create(vals)
        elif not self.import_task:
            raise UserError(_("Plz Select Either Import or Export"))

    def _office365_task_cron(self):
        domain = []
        all_creds = self.env['sh.office365.base.config'].search(domain)
        for creds in all_creds:
            if creds.auto_schedule_task:
                creds.task_export()
