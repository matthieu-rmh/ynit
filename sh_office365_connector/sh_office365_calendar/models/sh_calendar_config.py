# Part of Softhealer Technologies.

import logging

from odoo import api, fields, models, _
import requests
from datetime import datetime
import json
from dateutil.relativedelta import relativedelta
import pytz
from dateutil.parser import parse
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CalendarConfig(models.Model):
    _inherit = 'sh.office365.base.config'

    import_calendar = fields.Boolean("Import Events")
    auto_schedule_calendar = fields.Boolean("Auto Schedule ")
    manage_log_calendar = fields.Boolean("Manage Log History ")
    last_sync_calendar_import = fields.Datetime("Last Sync Date Import")
    calendar_import_between_dates = fields.Boolean("Import Between Dates")
    calendar_import_from = fields.Datetime("Calendar Import From")
    calendar_import_to = fields.Datetime("Calendar Import To")
    export_when_create = fields.Boolean("Export Directly When Create/Edit")
    next_calendar_link = fields.Char("Next Calendar link")

    def calendar_log(self, message, state='success', operation='import', field_type='calender'):
        if self.manage_log_calendar:
            self._log(message, field_type, state, operation)

    def calendar_importing(self):
        if self.import_calendar or self.calendar_import_between_dates:
            self.calendar_import_main()

    def reset_calendar(self):
        self.last_sync_calendar_import = False

    def calendar_import_main(self):
        if not self.auth_token:
            raise UserError(_("Plz Generate Token and try again"))
        self.RefreshToken()
        print(self.auth_token)
        try:
            import_event_url = ''
            if self.next_calendar_link:
                import_event_url = self.next_calendar_link
            elif self.calendar_import_between_dates:
                import_event_url = "https://graph.microsoft.com/v1.0/me/calendar/calendarView?startDateTime=%s&endDateTime=%s" % (self.calendar_import_from, self.calendar_import_to)
                # import_event_url = "https://graph.microsoft.com/v1.0/me/calendar/events?startDateTime=%s&endDateTime=%s" %(self.calendar_import_from,self.calendar_import_to)
            elif self.last_sync_calendar_import:
                import_event_url = "https://graph.microsoft.com/v1.0/me/calendar/events?$filter=(lastModifiedDateTime ge %sZ)" % (self.last_sync_calendar_import.isoformat())
            else:
                import_event_url = "https://graph.microsoft.com/v1.0/me/calendar/events?$top=10000"
            headers = {
                "Authorization": self.auth_token,
                "Content-Type": "application/json"
            }
            created = 0
            reset_to_draft = 0
            counter = 0
            while True:
                counter += 1
                if counter == 6:
                    if not (reset_to_draft or created):
                        self.calendar_log(f"Their is no data to import")
                        break
                response_get_events = requests.get(url=import_event_url, headers=headers)
                res_json = response_get_events.json()
                if 'value' not in res_json:
                    if 'error' in res_json:
                        self.calendar_log(f"Error: {res_json['error']['message']}", 'error')
                    elif not created:
                        self.calendar_log(f"Their is no data to import")
                    break
                if not res_json.get('value'):
                    self.calendar_log(f"Their is no data to import")
                for rec in res_json['value']:
                    find_in_queue = self.env['sh.office.queue'].search([
                        ('sh_calendar_id', '=', rec['id'])])
                    if not find_in_queue:
                        created += 1
                        self.env['sh.office.queue'].create({
                            'sh_queue_name': rec['subject'],
                            'sh_calendar_id': rec['id'],
                            'queue_sync_date': datetime.now(),
                            'sh_current_config': self.id,
                            'sh_current_state': 'draft',
                            'queue_type': 'calendar',
                        })
                    else:
                        reset_to_draft += 1
                        find_in_queue.write({'sh_current_state':'draft'})
                if res_json.get('@odata.nextLink'):
                    import_event_url = res_json['@odata.nextLink']
                else:
                    break
            if reset_to_draft:
                self.calendar_log(f"{reset_to_draft} Event reset to draft in the queue")
            if created:
                self.calendar_log(f"{created} Event added to the queue")
            if reset_to_draft or created:
                self.last_sync_calendar_import = datetime.now()
        except Exception as e:
            self.calendar_log(f'Error: {e}', 'error')

    def import_calendar_data(self, queue):
        calendar_id = queue.sh_calendar_id
        self.RefreshToken()
        import_event_url_id = "https://graph.microsoft.com/v1.0/me/calendar/events/%s" % (calendar_id)
        headers = {
            "Authorization": self.auth_token,
            "Content-Type": "application/json"
        }
        response_get_events = requests.get(url=import_event_url_id, headers=headers)
        res_json = response_get_events.json()
        values = res_json
        if not values:
            self.calendar_log("No New Events To Import")
            return
        vals = self.generate_calendar_vals(values)
        if not vals:
            self.calendar_log("No Proper Data Found", 'error')
            return
        if queue.sh_current_config.user_id:
            vals['user_id'] = queue.sh_current_config.user_id.id
        odoo_event = self.env['calendar.event'].search([
            ('office_365_calendar_id', '=', calendar_id)], limit=1)
        if odoo_event:
            odoo_event.with_context(from_api=True).write(vals)
        else:
            odoo_event = self.env['calendar.event'].with_context(from_api=True).create(vals)
        queue._done()
        self.calendar_log(f"'{odoo_event.name}' successfully created/edited")

    def import_from_queue_calendar(self):
        _logger.info('================== ///// ====================')
        find_calendar_event = self.env['sh.office.queue'].search([
            ('sh_calendar_id', '!=', False),
            ('sh_current_state', '=', 'draft')
        ], limit=20)
        if not find_calendar_event:
            return
        for value in find_calendar_event:
            if value.sh_calendar_id:
                value.sh_current_config.import_calendar_data(value)

    def generate_calendar_vals(self, rec):
        showas = False
        if 'showAs' in rec:
            showas = rec['showAs']
        if 'subject' in rec:
            subject = rec['subject'] if rec['subject'] else '(null)'
        else:
            subject = '(null)'
        is_all_day = rec['isAllDay'] if 'isAllDay' in rec else False
        remainder_on = rec['isReminderOn'] if 'isReminderOn' in rec else False
        if remainder_on:
            mins = rec['reminderMinutesBeforeStart'] if 'reminderMinutesBeforeStart' in rec else 0
        if 'start' not in rec:
            return False
        start_date = rec['start']['dateTime'].split('T')[0]
        start_time = rec['start']['dateTime'].split('T')[1].split('.')[0]
        sh_start_time = start_date + " " + start_time
        final_start = datetime.strptime(sh_start_time, '%Y-%m-%d %H:%M:%S')
        # end_date = rec['end']['dateTime'].split('T')[0]
        # end_time = rec['end']['dateTime'].split('T')[1].split('.')[0]
        timeZone_stop = pytz.timezone(rec['end']['timeZone'])
        if is_all_day:
            stop = parse(rec['end']['dateTime']).astimezone(timeZone_stop).replace(tzinfo=None) - relativedelta(days=1)
        else:
            stop = parse(rec['end']['dateTime']).astimezone(timeZone_stop).replace(tzinfo=None)
        # remainder_before = rec['reminderMinutesBeforeStart'] if 'reminderMinutesBeforeStart' in rec else 0
        location_address = ''
        if rec['location']:
            location_address = rec['location']['displayName']
        unique_id = rec['id']
        recurrence = rec['recurrence'] if 'recurrence' in rec else False
        description = rec['bodyPreview'] if 'bodyPreview' in rec else ''
        attend_name = []
        attend_email = []
        attendees = rec['attendees'] if 'attendees' in rec else False
        organizer = rec['organizer'] if 'organizer' in rec else False
        if attendees:
            for valuess in attendees:
                attend_name.append(valuess['emailAddress']['name'])
                attend_email.append(valuess['emailAddress']['address'].lower())
        if organizer:
            attend_name.append(organizer['emailAddress']['name'])
            attend_email.append(organizer['emailAddress']['address'].lower())
        dictionary_check = dict(zip(attend_email, attend_name))
        _logger.info('================== ///// ====================')
        _logger.info(unique_id)
        _logger.info('================== ///// ====================')
        if recurrence:
            interval = rec['recurrence']['pattern']['interval']
            mile_type = rec['recurrence']['pattern']['type']
            if mile_type == 'weekly':
                days = rec['recurrence']['pattern']['daysOfWeek']
            if mile_type == 'absoluteMonthly':
                day_of_month = rec['recurrence']['pattern']['dayOfMonth']
                # inter = rec['recurrence']['pattern']['interval']
            if mile_type == 'relativeMonthly':
                days_of_week = rec['recurrence']['pattern']['daysOfWeek']
                index = rec['recurrence']['pattern']['index']
            end_type = rec['recurrence']['range']['type']
            if end_type == 'endDate':
                enddate = rec['recurrence']['range']['endDate']
            if end_type == 'numbered':
                count = rec['recurrence']['range']['numberOfOccurrences']
        vals = {
            'name': subject,
            'allday': is_all_day,
            'location': location_address,
            'description': description,
            'show_as': showas,
            'office_365_calendar_id': unique_id,
        }
        if dictionary_check:
            partner_idss = []
            for mails, name in dictionary_check.items():
                domain = [('email', '=', mails)]
                find_attende = self.env['res.partner'].search(domain, limit=1)
                if find_attende:
                    partner_idss.append(find_attende.id)
                else:
                    create_vals = {
                        'name': name,
                        'email': mails
                    }
                    instant_create_partner = self.env['res.partner'].create(create_vals)
                    partner_idss.append(instant_create_partner.id)
            partner_idss = list(set(partner_idss))
            vals['partner_ids'] = [(6, 0, partner_idss)] if partner_idss else None
        if remainder_on:
            domain = [('duration_minutes', '=', mins)]
            alarm_id = self.env['calendar.alarm'].search(domain, limit=1)
            if not alarm_id:
                day_time = int(mins / (60 * 24))
                if day_time > 0:
                    day_vals = {
                        "name": str(day_time) + " Day(s)",
                        "interval": "days",
                        "duration": day_time
                    }
                    self.env['calendar.alarm'].create(day_vals)
                else:
                    hours_time = int(mins / (60))
                    if hours_time > 0:
                        hour_vals = {
                            "name": str(hours_time) + " Hour(s)",
                            "interval": "hours",
                            "duration": hours_time
                        }
                        self.env['calendar.alarm'].create(hour_vals)
            alarm_id = self.env['calendar.alarm'].search(domain, limit=1)
            vals['alarm_ids'] = alarm_id.ids
        vals['start'] = final_start
        vals['stop'] = stop
        if not recurrence:
            return vals
        vals['recurrency'] = recurrence
        vals['interval'] = interval
        if end_type == 'endDate':
            vals['end_type'] = 'end_date'
            vals['until'] = enddate
        elif end_type == 'numbered':
            vals['end_type'] = 'count'
            vals['count'] = count
        else:
            vals['end_type'] = 'forever'

        if mile_type == 'weekly':
            vals['rrule_type'] = 'weekly'
            if "monday" in days:
                vals['mon'] = True
            if "tuesday" in days:
                vals['tue'] = True
            if "wednesday" in days:
                vals['wed'] = True
            if "thursday" in days:
                vals['thu'] = True
            if "friday" in days:
                vals['fri'] = True
            if "saturday" in days:
                vals['sat'] = True
            if "sunday" in days:
                vals['sun'] = True
        elif mile_type == 'absoluteMonthly' or mile_type == 'relativeMonthly':
            vals['rrule_type'] = 'monthly'
            if mile_type == 'absoluteMonthly':
                vals['month_by'] = 'date'
                vals['day'] = day_of_month
            elif mile_type == 'relativeMonthly':
                vals['month_by'] = 'day'
                if "monday" in days_of_week:
                    vals['weekday'] = 'MON'
                if "tuesday" in days_of_week:
                    vals['weekday'] = 'TUE'
                if "wednesday" in days_of_week:
                    vals['weekday'] = 'WED'
                if "thursday" in days_of_week:
                    vals['weekday'] = 'THU'
                if "friday" in days_of_week:
                    vals['weekday'] = 'FRI'
                if "saturday" in days_of_week:
                    vals['weekday'] = 'SAT'
                if "sunday" in days_of_week:
                    vals['weekday'] = 'SUN'

                if "first" in index:
                    vals['byday'] = '1'
                if "second" in index:
                    vals['byday'] = '2'
                if "third" in index:
                    vals['byday'] = '3'
                if "fourth" in index:
                    vals['byday'] = '4'
                else:
                    vals['byday'] = '-1'
        elif mile_type == 'daily':
            vals['rrule_type'] = 'daily'
        else:
            vals['rrule_type'] = 'yearly'
        return vals

    def export_office365(self):
        domain = [('user_id', '=', self.env.user.id)]
        find_events = self.env['calendar.event'].search(domain)
        for data in find_events:
            self.time_to_export(data)

    def _event_vals(self, rec):
        dayss = rec.start.strftime("%d")
        months = rec.start.strftime("%m")
        payload = {
            'subject': rec.name,
            'isAllDay': rec.allday,
            'showAs': rec.show_as,
            'start': {
                'dateTime': rec.start,
                'timeZone': 'UTC'
            },
            'end': {
                'dateTime': rec.stop,
                'timeZone': 'UTC'
            }
        }
        payload["onlineMeetingProvider"] = "teamsForBusiness"
        attendee_list = []
        for attend in rec.partner_ids:
            if attend.email:
                pat = {
                    'emailAddress':{
                        'address': attend.email,
                        'name': attend.name
                    }
                }
                attendee_list.append(pat)
        payload['attendees'] = attendee_list
        if rec.allday:
            payload['start'] = {'dateTime': rec.start_date.isoformat(), 'timeZone': 'UTC'}
            if rec.stop_date:
                payload['end'] = {'dateTime': rec.stop_date.isoformat(), 'timeZone': 'UTC'}
            else:
                payload['end'] = {'dateTime': (rec.stop_date + relativedelta(days=1)).isoformat(), 'timeZone': 'UTC'}
        if rec.location:
            payload['location'] = {
                'displayName': rec.location
            }
        if rec.description:
            payload['body'] = {
                'contentType': 'html',
                'content': rec.description
            }
        # if not rec.recurrency:
        #     return payload
        return payload
        odoo_week_days = []
        if rec.mon:
            odoo_week_days.append("monday")
        if rec.tue:
            odoo_week_days.append("tuesday")
        if rec.wed:
            odoo_week_days.append("wednesday")
        if rec.thu:
            odoo_week_days.append("thursday")
        if rec.fri:
            odoo_week_days.append("friday")
        if rec.sat:
            odoo_week_days.append("saturday")
        if rec.sun:
            odoo_week_days.append("sunday")

        rrule_type = ""
        if rec.rrule_type == "daily":
            rrule_type = "daily"
            pattern = {
                "type": rrule_type,
                "index": "first",
                "month": 0,
                "interval": rec.interval,
                "firstDayOfWeek": "sunday",
            }
        elif rec.rrule_type == "weekly":
            rrule_type = "weekly"
            pattern = {
                "daysOfWeek": odoo_week_days,
                "type": rrule_type,
                "index": "first",
                "month": 0,
                "interval": rec.interval,
                "firstDayOfWeek": "sunday",
            }

        elif rec.rrule_type == "yearly":
            rrule_type = "absoluteYearly"
            pattern = {
                "dayOfMonth": dayss,
                "type": rrule_type,
                "interval": rec.interval,
                "month": months
            }
        else:
            nyday = ""
            weekdayss = []
            if rec.month_by == "day":
                if rec.byday == '1':
                    nyday = "first"
                if rec.byday == '2':
                    nyday = "second"
                if rec.byday == '3':
                    nyday = "third"
                if rec.byday == '4':
                    nyday = "fourth"
                if rec.byday == '5' or rec.byday == '-1':
                    nyday = "last"

                if rec.week_list == 'MON':
                    weekdayss.append('monday')
                if rec.week_list == 'TUE':
                    weekdayss.append('tuesday')
                if rec.week_list == 'WED':
                    weekdayss.append('wednesday')
                if rec.week_list == 'THU':
                    weekdayss.append('thursday')
                if rec.week_list == 'FRI':
                    weekdayss.append('friday')
                if rec.week_list == 'SAY':
                    weekdayss.append('saturday')
                if rec.week_list == 'SUN':
                    weekdayss.append('sunday')
                rrule_type = 'relativeMonthly'
                pattern = {
                    "daysOfWeek": weekdayss,
                    "dayOfMonth": 0,
                    "type": rrule_type,
                    "index": nyday,
                    "month": 0,
                    "interval": rec.interval,
                    "firstDayOfWeek": "sunday",
                }
            else:
                rrule_type = "absoluteMonthly"
                pattern = {
                    "type": rrule_type,
                    "index": "first",
                    "dayOfMonth": rec.day,
                    "month": 0,
                    "interval": rec.interval,
                    "firstDayOfWeek": "sunday",
                }
        if rec.end_type == 'end_date':
            end_types = 'endDate'
            ranges = {
                "type": end_types,
                "endDate": str(rec.until).split(' ')[0],
                "startDate": str(rec.start).split(' ')[0],
                "numberOfOccurrences": 0,
                "recurrenceTimeZone": 'UTC'
            }
        if rec.end_type == 'count':
            end_types = 'numbered'
            ranges = {
                "type": end_types,
                "startDate": str(rec.start).split(' ')[0],
                "numberOfOccurrences": rec.count,
                "recurrenceTimeZone": 'UTC'
            }
        if rec.end_type == 'forever':
            end_types = 'numbered'
            ranges = {
                "numberOfOccurrences": 720,
                "startDate": str(rec.start).split(' ')[0],
                "type": end_types,
                "recurrenceTimeZone": 'UTC'
                }
        payload["recurrence"] = {
            'pattern': pattern,
            'range': ranges
        }
        return payload
    
    
    def _delete_event(self, rec):
        headers = {
            "Authorization": self.auth_token,
            "Content-Type": "application/json"
        }
        print(headers)
        payload = self._event_vals(rec)
        if rec.office_365_calendar_id:
            # Delete event
            delete_calendar_url = 'https://graph.microsoft.com/v1.0/me/events/%s' % (rec.office_365_calendar_id)
            response = requests.delete(url=delete_calendar_url, headers=headers)
        return True

    def _cu_event(self, rec):
        '''cu: Create Update event'''
        headers = {
            "Authorization": self.auth_token,
            "Content-Type": "application/json"
        }
        payload = self._event_vals(rec)
        if rec.office_365_calendar_id:
            # Write the event
            edit_calendar_url = 'https://graph.microsoft.com/v1.0/me/events/%s' % (rec.office_365_calendar_id)
            response = requests.patch(url=edit_calendar_url, headers=headers, data=json.dumps(payload, indent=4, sort_keys=True, default=str))
            if response.status_code == 200:
                return True
        else:
            # Create the event
            create_event_url = "https://graph.microsoft.com/v1.0/me/events"
            response_create_event = requests.post(url=create_event_url, headers=headers, data=json.dumps(payload, indent=4, sort_keys=True, default=str))
            if response_create_event.status_code == 201:
                res_json = response_create_event.json()
                if res_json['id']:
                    unique_id = res_json['id']
                    rec.with_context(from_api=True).write({
                        'office_365_calendar_id': unique_id
                    })
                    return True
    
    def time_to_delete(self, rec):
        if not self.auth_token:
            raise UserError(_("Plz Generate Token and try again"))
        try:
            self.RefreshToken()
            rec = rec.with_context(from_api=True)
            is_success = False
            if rec.recurrency:
                is_success = self._delete_event(rec)
            elif rec.recurrency == False:
                is_success = self._delete_event(rec)
            else:
                find_all_events = self.env['calendar.event'].search([('active', '=', False)])
                active_false = [xx.id for xx in find_all_events]
                if rec.recurrence_id.base_event_id.id in active_false:
                    is_success = self._delete_event(rec)
            if is_success:
                self.calendar_log("Successfully Deleted", operation="export")
            else:
                self.calendar_log(f"Failed to delete: {rec.name}", operation="export")

        except Exception as e:
            self.calendar_log(f"Error: {e}", "error", "export")
    
    def time_to_export(self, rec):
        if not self.auth_token:
            raise UserError(_("Plz Generate Token and try again"))
        try:
            self.RefreshToken()
            rec = rec.with_context(from_api=True)
            is_success = False
            if rec.recurrency:
                is_success = self._cu_event(rec)
            elif rec.recurrency == False:
                is_success = self._cu_event(rec)
            else:
                find_all_events = self.env['calendar.event'].search([('active', '=', False)])
                active_false = [xx.id for xx in find_all_events]
                if rec.recurrence_id.base_event_id.id in active_false:
                    is_success = self._cu_event(rec)
                self.last_sync_calendar_export = datetime.now()
            if is_success:
                self.calendar_log("Successfully Done", operation="export")
            else:
                self.calendar_log(f"Failed to export: {rec.name}", operation="export")

        except Exception as e:
            self.calendar_log(f"Error: {e}", "error", "export")

    def _office365_calender_cron(self):
        _logger.info('================== ///// ====================')
        all_creds = self.env['sh.office365.base.config'].search([])
        for creds in all_creds:
            if creds.auto_schedule_calendar:
                creds.calendar_importing()
