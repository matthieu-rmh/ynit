# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import odoo.http as http

from odoo.http import request
from odoo.addons.calendar.controllers.main import CalendarController

class FBICalendarController(CalendarController):
    
    @http.route('/calendar/meeting/decline', type='http', auth="calendar")
    def decline_meeting(self, token, id, **kwargs):
        attendee = request.env['calendar.attendee'].sudo().search([
            ('access_token', '=', token),
            ('state', '!=', 'declined')])
        attendee.event_id and attendee.event_id.remove_participants()
        attendee.do_decline()
        return self.view_meeting(token, id)