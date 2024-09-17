# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import fields, models, _
import requests
from odoo.exceptions import UserError
from datetime import datetime


class Authorize(models.Model):
    _name = 'sh.office365.base.config'
    _description = 'Authorize your credentials'

    name = fields.Char("Name")
    user_id = fields.Many2one('res.users', string='User', required=True, default=lambda self: self.env.user)
    client_id = fields.Char("Client ID")
    client_secret = fields.Char("Client Secret")
    redirect_url = fields.Char("Redirect Url")
    code = fields.Char("Code")
    access_token = fields.Char("Access Token")
    auth_token = fields.Char("Auth Token")
    refresh_token = fields.Char("Refresh Token")
    from_office365 = fields.Boolean("Imported from Office365")
    auto_schedule = fields.Boolean("Auto Schedule")
    manage_log = fields.Boolean("Manage Log History")
    sh_queue_ids = fields.One2many("sh.office.queue", 'sh_current_config')
    log_historys = fields.One2many('sh.office365.base.log', 'base_config_id', string="Log History")
    with_mobile = fields.Boolean("Phone Number")
    with_email = fields.Boolean("Email Address")

    # ------------------------------------------------------
    #  Create Log Method
    # ------------------------------------------------------

    def _log(self, error, field_type, state, operation):
        self.env['sh.office365.base.log'].create({
            "name": self.name,
            "datetime": datetime.now(),
            "base_config_id": self.id,
            "state": state,
            "error": error,
            "field_type": field_type,
            "operation": operation
        })

    def AuthorizeCreds(self):
        try:
            if self.client_id and self.redirect_url:
                self_id = str(self.id)
                scope = "Contacts.ReadWrite Tasks.ReadWrite offline_access Mail.ReadWrite Mail.Send Mail.Send.Shared"
                values = (self.client_id, "code", self.redirect_url, scope, "query", self_id)
                auth_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=%s&response_type=%s&redirect_url=%s&scope=%s&response_mode=%s&state=%s" % values
                return {
                    'type': 'ir.actions.act_url',
                    'target': '_blank',
                    'url': auth_url
                }
            else:
                raise UserError("Plz enter Credentials and Try again")
        except Exception as e:
            raise UserError(e)

    def generate_token(self):
        try:
            token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
            scope = "Contacts.ReadWrite Tasks.ReadWrite offline_access Mail.ReadWrite Mail.Send Mail.Send.Shared"
            payload = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_url": self.redirect_url,
                "code": self.code,
                "scope": scope,
                "grant_type": "authorization_code"
            }
            response = requests.post(url=token_url, data=payload)
            res = response.json()
            if "access_token" in res:
                self.access_token = res['access_token']
                token_type = res['token_type']
                self.refresh_token = res['refresh_token']
                self.auth_token = token_type + " " + self.access_token
            else:
                vals = {
                    "name": self.name,
                    "base_config_id": self.id,
                    "state": "error",
                    "error": response.text,
                    "datetime": datetime.now()
                }
                self.env['sh.office365.base.log'].create(vals)
                raise UserError(res['error_description'])
        except Exception as e:
            raise UserError(e)

    def RefreshToken(self):
        if self.client_id and self.client_secret and self.redirect_url:
            refresh_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
            scope = "Contacts.ReadWrite Tasks.ReadWrite offline_access Mail.ReadWrite Mail.Send Mail.Send.Shared"
            payload = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_url": self.redirect_url,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
                "scope": scope,
            }
            try:
                response = requests.post(url=refresh_url, data=payload)
                res_json = response.json()
                if "access_token" in res_json:
                    self.access_token = res_json['access_token']
                    token_type = res_json['token_type']
                    self.refresh_token = res_json['refresh_token']
                    self.auth_token = token_type + " " + self.access_token
                else:
                    raise UserError(_(res_json['error_description']))
            except Exception as ex:
                raise UserError(ex)
        else:
            raise UserError("Enter credentials Frist")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    contacts_imported = fields.Boolean("Imported")
    contacts_exported = fields.Boolean("Exported")
    office365_id = fields.Char("Office365 Ids")
