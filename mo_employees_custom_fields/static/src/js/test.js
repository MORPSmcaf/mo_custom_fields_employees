/** @odoo-module **/

import { EmployeeFormController } from '@hr/views/form_view';
import { registry } from '@web/core/registry';
import { formView } from '@web/views/form/form_view';
import { FormRenderer } from '@web/views/form/form_renderer';
import { useOpenChat } from "@mail/views/open_chat_hook";


export class CustomEmployeeFormController extends EmployeeFormController {
    setup() {
        super.setup();
    }

    async saveButtonClicked(params = {}) {

        this.disableButtons();
        const record = this.model.root;
        let saved = false;

        if (this.props.saveRecord) {
            saved = await this.props.saveRecord(record, params);
        } else {
            saved = await record.save();
        }
        this.enableButtons();
        if (saved && this.props.onSave) {
            this.props.onSave(record, params);
        }
        if (saved) {
            if (this.env && this.env.services && this.env.services.notification) {
                this.env.services.notification.add('Custom save notification for HR.', {
                    type: 'info',
                    title: 'HR Custom Module',
                    sticky: false,
                });
            }
        }

        return saved;
    }
}

export class EmployeeFormRenderer extends FormRenderer {
    setup() {
        super.setup();
        this.openChat = useOpenChat(this.props.record.resModel);
    }
}


registry.category('views').add('custom_hr_employee_form', {
    ...formView,
    Controller: CustomEmployeeFormController,
    Renderer: EmployeeFormRenderer,
});
