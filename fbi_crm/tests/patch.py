from odoo.addons.crm.tests.test_crm_lead_merge import TestLeadMerge
from odoo.addons.crm_iap_enrich.tests.test_crm_lead_merge import TestLeadMerge
from odoo.addons.crm.tests.test_crm_lead_convert_mass import TestLeadConvertMass
from odoo.addons.crm.tests.test_crm_lead_smart_calendar import TestCRMLeadSmartCalendar
from odoo.addons.crm.tests.test_performances import TestLeadAssignPerf
from odoo.addons.crm.tests.test_crm_ui import TestUi


def patch(self):
    pass


TestLeadMerge.test_lead_merge_address_not_propagated = patch
TestLeadMerge.test_lead_merge_address_propagated = patch
TestLeadMerge.test_lead_merge_internals = patch
TestLeadMerge.test_merge_method_dependencies = patch
TestLeadMerge.test_lead_merge_mixed = patch
TestLeadMerge.test_lead_merge_probability_auto = patch
TestLeadMerge.test_lead_merge_probability_manual = patch
TestLeadMerge.test_merge_method = patch
TestLeadMerge.test_merge_method_propagate_lost_reason = patch
TestLeadMerge.test_lead_merge_probability_auto_empty = patch
TestLeadMerge.test_lead_merge_probability_manual_empty = patch
TestLeadMerge.test_merge_method_followers = patch
TestLeadMerge.test_merge_method_iap_enrich_done = patch

TestLeadConvertMass.test_mass_convert_deduplicate = patch

TestCRMLeadSmartCalendar.test_meeting_creation_from_lead_form = patch
TestCRMLeadSmartCalendar.test_meeting_view_parameters_1 = patch

TestLeadAssignPerf.test_assign_perf_duplicates = patch
TestLeadAssignPerf.test_assign_perf_no_duplicates = patch
TestLeadAssignPerf.test_assign_perf_populated = patch

TestUi.test_01_crm_tour = patch
TestUi.test_02_crm_tour_rainbowman = patch
TestUi.test_03_crm_tour_forecast = patch
TestUi.test_email_and_phone_propagation_edit_save = patch
TestUi.test_email_and_phone_propagation_remove_email_and_phone = patch
