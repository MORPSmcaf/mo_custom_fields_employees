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

    const email = record.data.email__employee;
    const phone = record.data.phone_employee;
    const zipCode = record.data.zip_code_employee;

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const phoneRegex = /^\+?[0-9]{10,15}$/;
    const zipCodeRegex = /^[A-Za-z]\d[A-Za-z] \d[A-Za-z]\d$/;

    if (email && !emailRegex.test(email)) {
        if (this.env && this.env.services && this.env.services.notification) {
            this.env.services.notification.add('Invalid email format.', {
                type: 'danger',
                title: 'Validation Error',
                sticky: false,
            });
        }
        this.enableButtons();
        return false;
    }

    if (phone && !phoneRegex.test(phone)) {
        if (this.env && this.env.services && this.env.services.notification) {
            this.env.services.notification.add('Invalid phone format. Expected format: +1234567890', {
                type: 'danger',
                title: 'Validation Error',
                sticky: false,
            });
        }
        this.enableButtons();
        return false;
    }
    if (zipCode && !zipCodeRegex.test(zipCode)) {
        if (this.env && this.env.services && this.env.services.notification) {
            this.env.services.notification.add('Invalid postal code format. Example: E3B 2A7', {
                type: 'danger',
                title: 'Validation Error',
                sticky: false,
            });
        }
        this.enableButtons();
        return false;
    }

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
