/** @odoo-module **/

import { registry } from "@web/core/registry";
import { calendarView } from "@web/views/calendar/calendar_view";
import { FbiCrmAttendeeCalendarController } from "@fbi_crm/views/fbi_crm_attendee_calendar/attendee_calendar_controller";
import { AttendeeCalendarModel } from "@calendar/views/attendee_calendar/attendee_calendar_model";
import { AttendeeCalendarRenderer } from "@calendar/views/attendee_calendar/attendee_calendar_renderer";

export const fbiCrmAttendeeCalendarView = {
    ...calendarView,
    Controller: FbiCrmAttendeeCalendarController,
    Model: AttendeeCalendarModel,
    Renderer: AttendeeCalendarRenderer,
    buttonTemplate: "calendar.AttendeeCalendarController.controlButtons",
};

registry.category("views").add("fbi_crm_attendee_calendar", fbiCrmAttendeeCalendarView);
