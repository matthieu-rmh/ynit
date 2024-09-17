/** @odoo-module **/

import { AttendeeCalendarController } from "@calendar/views/attendee_calendar/attendee_calendar_controller";
import { FormViewDialog } from "@web/views/view_dialogs/form_view_dialog";
import { _lt, _t } from "@web/core/l10n/translation";

export class FbiCrmAttendeeCalendarController extends AttendeeCalendarController {
    setup() {
        super.setup();
    }

    /**
     * @override
     *
     * Reload on close : Usefull for custom closing actions
     */
     async editRecord(record, context = {}, shouldFetchFormViewId = true) {
        if (this.model.hasEditDialog) {
            return new Promise((resolve) => {
                this.displayDialog(
                    FormViewDialog,
                    {
                        resModel: this.model.resModel,
                        resId: record.id || false,
                        context,
                        title: record.id ? `${_t("[FBI CRM] Open")}: ${record.title}` : _t("[FBI CRM] New Event"),
                        viewId: this.model.formViewId,
                        onRecordSaved: () => this.model.load(),
                    },
                    { onClose: () => { this.model.load(); resolve(); } }
                );
            });
        } else {
            let formViewId = this.model.formViewId;
            if (shouldFetchFormViewId) {
                formViewId = await this.orm.call(
                    this.model.resModel,
                    "get_formview_id",
                    [[record.id]],
                    context
                );
            }
            const action = {
                type: "ir.actions.act_window",
                res_model: this.model.resModel,
                views: [[formViewId || false, "form"]],
                target: "current",
                context,
            };
            if (record.id) {
                action.res_id = record.id;
            }
            this.action.doAction(action);
        }
    }

}
FbiCrmAttendeeCalendarController.template = "calendar.AttendeeCalendarController";
