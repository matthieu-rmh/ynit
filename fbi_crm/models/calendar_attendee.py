# -*- coding: utf-8 -*-

import uuid
import base64
import logging

from collections import defaultdict
from odoo import api, fields, models, _
from odoo.addons.base.models.res_partner import _tz_get
from odoo.exceptions import UserError


class FbiAttendee(models.Model):
    """ Calendar Attendee Information """
    _inherit = 'calendar.attendee'
    
    def _send_mail_to_attendees_dematicall(self):
        ### HERE WE WARN PARTICIPANTS IN APPOINTMENTS GIVEN BY DEMATICALL OF CHANGES IN SCHEDULES
        attendees = self.filtered(lambda a: (a.event_id and a.event_id.opportunity_id and a.event_id.opportunity_id.is_dematicall()))
        ics_files = attendees.mapped('event_id')._get_ics_file()

        for attendee in attendees:
            if attendee.email:
                event_id = attendee.event_id.id
                ics_file = ics_files.get(event_id)
                self.env.ref('fbi_crm.fbi_crm_template_meeting_date_changed_mail').send_mail(attendee.id,
                    email_values={
                        'email_to': attendee.email,
                        'email_cc': ','.join([
                                        user.email for user in(
                                            self.env.ref('fbi_crm.group_fbi_crm_manager').users |
                                            self.env.ref('fbi_crm.group_fbi_crm_dm').users
                                        ) if user.email]),
                        'attachment_ids': [self.env['ir.attachment'].create({
                            'name': 'invitation.ics',
                            'type': 'binary',
                            'mimetype': 'text/calendar',
                            'datas': base64.b64encode(ics_file),
                        }).id]
                    }, force_send=True)
