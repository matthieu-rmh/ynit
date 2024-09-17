# Part of Softhealer Technologies.
from odoo import fields, models, _
import requests
from odoo.exceptions import UserError
from datetime import datetime
from datetime import timezone
import json
import re
import base64
import dateutil.parser as parser


class SyncContact(models.Model):
    _inherit = 'sh.office365.base.config'

    import_contact = fields.Boolean("Import Contacts")
    last_sync_date = fields.Datetime("Last Sync Date")
    sync_image = fields.Boolean("Sync Image" , help="It will reduce performance")
    contact_state = fields.Selection([('success', 'Success'), ('error', 'Failed')])

    def sh_image_sync(self , office_id):
        token = self.auth_token
        image_url = "https://graph.microsoft.com/v1.0/me/contacts/%s/photo/$value" % (office_id)
        image_headers = {
            "Authorization": token,
            "Content-Type": "application/json"
        }
        response = requests.get(url=image_url, headers=image_headers)
        if response.status_code == 200:
            image_found = response.content
            encoded = base64.b64encode(image_found)
        else:
            encoded = ''
        return encoded

    def reset_contacts(self):
        self.last_sync_date = False

    def manage_import_contact(self): 
        domain = [('queue_type', '=', 'contact'), ('sh_current_state', '=', 'draft')]
        get_con = self.env['sh.office.queue'].search(domain, order="id asc", limit=50)
        if get_con:
            counter = 0
            for data in get_con:
                counter += 1
                data.sh_current_config.import_contacts(data.sh_contact_id)
            if counter: 
                vals = {
                    "state": "success",
                    "base_config_id": data.sh_current_config.id,
                    "field_type": "contact",
                    "error": "Cron : Imported Successfully %s contacts" % (counter),
                    "datetime": datetime.now(),
                    "operation": "import"
                }
                self.env['sh.office365.base.log'].create(vals)

    def import_contacts(self, import_values): 
        self.RefreshToken()
        if self.auth_token:
            try: 
                one_count = 0
                get_contacts_url = "https://graph.microsoft.com/v1.0/me/contacts/%s" % (import_values)
                headers = {
                    "Authorization": self.auth_token,
                    "Host": "graph.microsoft.com"
                }
                response = requests.get(url=get_contacts_url, headers=headers)
                res_json = response.json()                
                first_name = res_json.get('givenName')
                surname = res_json.get('surname')
                if surname:
                    name = first_name + ' ' + surname
                else:
                    name = first_name
                title = res_json.get('title')
                title_id = False
                if title:
                    domain = [('name', '=', title)]
                    find_title = self.env['res.partner.title'].search(domain, limit=1)
                    if find_title:
                        title_id = find_title.id
                    else:
                        vals = {
                            'name': title
                        }
                        add_title = self.env['res.partner.title'].create(vals)
                        title_id = add_title.id
                url = res_json.get('businessHomePage')
                odoo_id_str = res_json.get('spouseName')
                odoo_id = ''
                if odoo_id_str:
                    odoo_id = int(odoo_id_str)
                office_id = res_json.get('id')
                phonenumber = res_json.get('mobilePhone')
                mobile = res_json.get('businessPhones')
                final_mobile = False
                if mobile:
                    final_mobile = mobile[0]
                emailaddresses = res_json.get('emailAddresses', [])
                if emailaddresses:
                    emailaddresse = emailaddresses[0].get('name')
                else:
                    emailaddresse = False
                addresses = res_json.get('businessAddress', [])
                streetaddress = False
                city = False
                postal = False
                state = False
                if addresses:
                    streetaddress = addresses.get('street')
                    city = addresses.get('city')
                    postal = addresses.get('postalCode')
                    state = addresses.get('state')
                    if state:
                        domain = [('name', '=', state)]
                        state = self.env['res.country.state'].search(domain, limit=1)
                notes = res_json.get('personalNotes')
                company_id = None
                job_pos = res_json.get('jobTitle')
                company_name = res_json.get('companyName')
                if company_name:
                    domain = [('name', '=', company_name)]
                    find_company = self.env['res.partner'].search(domain, limit=1)
                    if find_company:
                        company_id = find_company.id
                    else:
                        vals = {
                            'name': company_name,
                            'company_type': 'company',
                        }
                        add_company = self.env['res.partner'].create(vals)
                        company_id = add_company.id
                domain = [('office365_id', '=', office_id)]
                already_imported = self.env['res.partner'].search(domain)                    
                vals = {
                            'name': name,
                            'function': job_pos,
                            'mobile': final_mobile,
                            'phone': phonenumber if phonenumber else False,
                            'email': emailaddresse,
                            'street': streetaddress,
                            'city': city,
                            'state_id': state.id if state else False,
                            'country_id': state.country_id.id if state and state.country_id else False,
                            'title': title_id if title else False,
                            'zip': postal,
                            'parent_id': company_id,
                            'comment': notes,
                            'office365_id': office_id,
                            'website': url,
                        }
                if self.sync_image:
                    base_image = self.sh_image_sync(office_id)
                    vals['image_1920'] = base_image
                if already_imported:
                    one_count += 1
                    already_imported.write(vals)
                elif self.with_email or self.with_mobile: 
                    domain = []
                    if self.with_mobile:
                        if phonenumber:
                            domain.append(('phone', '=', phonenumber))
                    if self.with_email:
                        if emailaddresse:
                            domain.append(('email', '=', emailaddresse))
                    if domain:
                        match_found = self.env['res.partner'].search(domain, limit=1)
                        if match_found:
                            one_count += 1
                            match_found.write(vals)
                        else:
                            one_count += 1
                            self.env['res.partner'].create(vals)
                    else:
                        one_count += 1
                        self.env['res.partner'].create(vals)
                else:
                    one_count += 1
                    self.env['res.partner'].create(vals)
                if one_count > 0:
                    domain = [('sh_contact_id', '=', import_values), ('queue_type', '=', 'contact')]
                    find_queue = self.env['sh.office.queue'].search(domain)               
                    if find_queue:
                        find_queue.write({
                            'sh_current_state': 'done'
                        })
            except Exception as e:
                if self.manage_log:
                    vals = {
                        "name": self.name,
                        "state": "error",
                        "base_config_id": self.id,
                        "field_type": "contact",
                        "error": e,
                        "datetime": datetime.now(),
                        "operation": "import"
                    }
                    self.env['sh.office365.base.log'].create(vals)
        else:
            if self.manage_log:
                vals = {
                        "name": self.name,
                        "state": "error",
                        "field_type": "contact",
                        "error": "No Token Found, genearte token again",
                        "datetime": datetime.now(),
                        "base_config_id": self.id,
                        "operation": "import"
                    }
                self.env['sh.office365.base.log'].create(vals)
            raise UserError(_("Plz Genearte Token Before Importing"))

    def sync_office_contact(self):
        if self.import_contact:
            self.RefreshToken()
            if self.auth_token:
                if not self.last_sync_date:
                    get_contacts_url = "https://graph.microsoft.com/v1.0/me/contacts?$top=100000"
                else: 
                    get_contacts_url = "https://graph.microsoft.com/v1.0/me/contacts?filter=(lastModifiedDateTime ge %sZ)" % (self.last_sync_date.isoformat())
                headers = {
                    "Authorization": self.auth_token,
                    "Host": "graph.microsoft.com"
                }
                response = requests.get(url=get_contacts_url, headers=headers)
                res_json = response.json()
                if not 'error' in res_json:
                    created = 0
                    for person in res_json['value']:
                        office_id = person.get('id')
                        if 'displayName' in person:
                            final_name = person['displayName']
                        else:
                            final_name = 'No Name'
                        find_in_queue = False
                        domain = [('sh_contact_id', '=', office_id), ('queue_type', '=', 'contact')]
                        find_in_queue = self.env['sh.office.queue'].search(domain)
                        if not find_in_queue:
                            created += 1
                            queue_vals = {
                                'queue_type': 'contact',
                                'queue_sync_date': datetime.now(),
                                'sh_contact_id': office_id,
                                'sh_current_state': 'draft',
                                'sh_queue_name': final_name,
                                'sh_current_config': self.id,
                            }
                            self.env['sh.office.queue'].create(queue_vals)
                        else:
                            created += 1
                            find_in_queue.write({'sh_current_state':'draft'})
                    self.last_sync_date = datetime.now()
                    if created > 0 and self.manage_log:
                        vals = {
                            "name": self.name,
                            "operation": "import",
                            "base_config_id": self.id,
                            "state": "success",
                            "field_type": "contact",
                            "error": "%s contacts Added to the Queue" % (created),
                            "datetime": datetime.now()
                        }
                        self.env['sh.office365.base.log'].create(vals)
                    elif self.manage_log:
                        vals = {
                            "name": self.name,
                            "operation": "import",
                            "base_config_id": self.id,
                            "state": "success",
                            "field_type": "contact",
                            "error": "No Contacts Found",
                            "datetime": datetime.now()
                        }
                        self.env['sh.office365.base.log'].create(vals)
                elif self.manage_log:
                    vals = {
                        "name": self.name,
                        "operation": "import",
                        "base_config_id": self.id,
                        "state": "error",
                        "field_type": "contact",
                        "error": res_json['error'],
                        "datetime": datetime.now()
                    }
                    self.env['sh.office365.base.log'].create(vals)

    def partial_export(self, export_values):
        self.RefreshToken()
        if self.auth_token:
            try:
                export_url = 'https://graph.microsoft.com/v1.0/me/contacts'
                headers = { "Content-Type": "application/json",
                            "Authorization": self.auth_token,
                            "Accept": "text/html, application/json",
                            "Accept-Encoding": "gzip, deflate, br"
                        }
                update_headers = {
                        "Authorization": self.auth_token,
                        "Host": "graph.microsoft.com",
                        "Content-type": "application/json"
                    }
                check_count = 0
                for count_c, partner in export_values.items():
                    check_count += 1
                    if partner.street and partner.street2:
                        streets = '{} {}'.format(partner.street, partner.street2)
                    else:
                        streets = partner.street
                    count = 0
                    payload = {
                        "givenName": partner.name,
                        "surname": None,
                        "mobilePhone": partner.mobile if partner.mobile else None,
                        "businessPhones": [partner.phone if partner.phone else ''],
                        "jobTitle": partner.function if partner.function else None,
                        "companyName": partner.parent_id.name if partner.parent_id.name else None,
                        "businessHomePage": partner.website if partner.website else '',
                        "title": partner.title.name if partner.title else None,
                        "businessAddress":
                            {
                                "street": streets if streets else '',
                                "city": partner.city if partner.city else '',
                                "state": partner.state_id.name if partner.state_id else '',
                                "countryOrRegion": partner.country_id.name if partner.country_id else '',
                                "postalCode": partner.zip if partner.zip else ''
                            }
                    }
                    if partner.comment:
                        remove_html = re.compile('<.*?>')
                        description = re.sub(remove_html, '', partner.comment)
                        payload['personalNotes'] = description
                    if partner.email:
                        payload["emailAddresses"] = [
                            {"address": partner.email}
                        ]
                    if partner.office365_id:
                        count = count + 1
                        update_url = "https://graph.microsoft.com/v1.0/me/contacts/%s" % (partner.office365_id)
                        requests.patch(url=update_url, data=json.dumps(payload), headers=update_headers)
                    else:
                        res = requests.post(url=export_url, data=json.dumps(payload), headers=update_headers)
                        if res.status_code == 201:
                            res_json = res.json()
                            vals = {
                                "office365_id": res_json['id']
                            }
                            partner.write(vals)
                    if count_c == 1:
                        self.contact_state = 'success'
                        vals = {
                            "name": self.name,
                            "base_config_id": self.id,
                            "field_type": "contact",
                            "operation": "export",
                            "state": "success",
                            "error": "Exported Successfully",
                            "datetime": datetime.now()
                        }
                        self.env['sh.office365.base.log'].create(vals)
                        break
            except Exception as e:
                if self.manage_log:
                    self.contact_state = 'error'
                    vals = {
                        "name": self.name,
                        "operation": "export",
                        "base_config_id": self.id,
                        "state": "error",
                        "field_type": "contact",
                        "error": e,
                        "datetime": datetime.now()
                    }
                    self.env['sh.office365.base.log'].create(vals)
        else:
            if self.manage_log:
                vals = {
                        "name": self.name,
                        "base_config_id": self.id,
                        "operation": "export",
                        "state": "error",
                        "field_type": "contact",
                        "error": "No Token Found, genearte token again",
                        "datetime": datetime.now()
                    }
                self.env['sh.office365.base.log'].create(vals)

    def _office365_cantact_cron(self):
        domain = []
        all_creds = self.env['sh.office365.base.config'].search(domain)
        for creds in all_creds:
            if creds.auto_schedule:
                creds.sync_office_contact()

    def export_multi_contact(self, export_list):
        list_export = []
        for data in export_list:
            list_export.append(data)
        exp_length = len(list_export)
        count = []
        for i in range(exp_length, 0, -1):
            count.append(i)
        export_values = dict(zip(count, list_export))
        self.partial_export(export_values)
