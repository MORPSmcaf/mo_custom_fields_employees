/** @odoo-module **/

import { registry } from "@web/core/registry";
import { CharField } from "@web/views/fields/char/char_field";

export class CustomBoldWidget extends CharField {

}

CustomBoldWidget.template = "BoldTextField.CharField";

registry.category("fields").add("custom_bold", CustomBoldWidget);