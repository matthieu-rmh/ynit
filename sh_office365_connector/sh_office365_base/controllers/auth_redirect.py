from odoo import http, _
from odoo.http import request
import werkzeug
import werkzeug.utils
from odoo.exceptions import UserError


class Redirects(http.Controller):

    @http.route("/sh_office365_base/redirect", auth="public")
    def get_code(self, **kwargs):
        if 'code' in kwargs:
            code = kwargs.get('code')
            rec_id = kwargs.get('state')
            rec_id_int = int(rec_id)
            config = request.env['sh.office365.base.config'].search([('id', '=', rec_id_int)], limit=1)
            if config:
                config.write({'code': code})
                config.generate_token()
            return werkzeug.utils.redirect("/")
        else:
            raise UserError(_("Could not receive code, check credentials"))
