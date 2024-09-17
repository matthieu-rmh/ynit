# Part of Softhealer Technologies.
from odoo import api, fields, models, _


class Office365Calendar(models.Model):
    _inherit = 'calendar.event'

    office_365_calendar_id = fields.Char("Unique Key")
    check = fields.Boolean("")
    show_as = fields.Selection(selection_add=[('tentative', 'Tentative'), ('oof', 'Away'), ('workingElsewhere', 'Working Elsewhere')], ondelete={'tentative': 'cascade', 'oof': 'cascade', 'workingElsewhere': 'cascade'})

    def _is_export_event(self, deleteEvent=False):
        for rec in self:
            uid = False
            if rec.user_id:
                uid = rec.user_id.id
            elif self.env.user.id:
                uid = self.env.user.id
            if uid:
                find_user = self.env['sh.office365.base.config'].sudo().search([('user_id', '=', uid)], limit=1)
                if find_user and find_user.export_when_create:
                    rec = rec.with_context(from_api=True)
                    find_user.time_to_export(rec)

    @api.model_create_multi
    def create(self, vals):
        res = super(Office365Calendar, self).create(vals)
        if self.env.context.get('from_api'):
            # res = super(Office365Calendar,self).create(vals)
            self = self.with_context(from_api=True)
            return res
        # res = super(Office365Calendar,self).create(vals)
        res._is_export_event()
        return res

    def write(self, vals):
        res = super(Office365Calendar, self).write(vals)
        if self.env.context.get('is_calendar_event_new'):
            return res
        if self.env.context.get('from_api'):
            return res
        self._is_export_event()
        return res
    
    def unlink(self):
        for rec in self:
            user_id =  rec.user_id and rec.user_id.id
            if user_id:
                find_user = self.env['sh.office365.base.config'].sudo().search([('user_id', '=', user_id)], limit=1)
                if find_user:
                    find_user.time_to_delete(rec)
        res = super(Office365Calendar, self).unlink()
        return res

    def export_event_multi_action(self):
        active_queue_ids = self.env['calendar.event'].browse(self.env.context.get('active_ids'))
        active_queue_ids._is_export_event()
        
    ####### CHECK DUPLICATED EVENT #######
    def _check_duplicated_events(self):
        events = self.env['calendar.event'].search([])
        duplicates = {}

        for event in events:
            name_email_key = (event.name, event.start, event.stop)
            if name_email_key in duplicates and not event.office_365_calendar_id:
                duplicates[name_email_key].append(event)
            else:
                duplicates[name_email_key] = [event]
        
        for key, events in duplicates.items():
            if len(events) > 1:
                self.sudo().unlink()
                # print(f"Duplicate found for Name: {key[0]} and Keys: {key[1]} / {key[1]} - Evts: {events}")
        return True
    ####### CHECK DUPLICATED EVENT #######

