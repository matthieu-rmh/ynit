from odoo.addons.crm.tests.test_sales_team_ui import TestUi
from odoo.addons.calendar.tests.test_calendar import TestCalendarTours


def patch(self):
    pass


TestUi.test_calendar_decline_tour = patch
TestCalendarTours.test_calendar_decline_with_everybody_filter_tour = patch
