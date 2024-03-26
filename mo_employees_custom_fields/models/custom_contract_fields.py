from datetime import timedelta
import logging
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class InheretCustom(models.Model):
    _inherit = 'hr.contract.type'

class CustomContractFields(models.Model):
    """Adding custom contract
       functionality fields"""
    _inherit = 'hr.contract.history'

    @api.model
    def check_90_days_employment(self):
        today = fields.Date.today()
        ninety_days = today - timedelta(days=90)

        employees = self.search([('date_hired', '!=', False),
                                 ('date_hired', '=', ninety_days)])

        for employee in employees:
            self.days_90_completion_email(employee)

    def days_90_completion_email(self, employee):
        template = self.env.ref('mo_employees_custom_fields.'
                                'email_template_90_days_completion')
        company_email = (employee.company_id.email or
                         self.env.user.company_id.email)

        group_hr_user = self.env.ref('hr.group_hr_user')
        hr_users = group_hr_user.users

        if template:
            template.email_from = company_email

            for user in hr_users:
                if user.email:
                    template.email_to = user.email
                    template.send_mail(employee.id, force_send=True,
                                       email_values={'email_to': user.email})


class CustomContract(models.Model):
    """Adding custom address
       fields"""
    _inherit = 'hr.contract'

    state = fields.Selection([
        ('draft', 'New'),
        ('probation', 'Probation'),
        ('open', 'Running'),
        ('close', 'Expired'),
        ('cancel', 'Cancelled')
    ], string='Status', group_expand='_expand_states', copy=False,
        tracking=True, help='Status of the contract', default='draft')
    probation_selection = [(f'{i} month', f'{i} month') for i in range(13)]
    contract_type_id = fields.Many2one('hr.contract.type',
                                       "Employee Category", required=True)
    probation_period = fields.Selection(
        probation_selection,
        string='Probation Period ',
        default='0 month',
        required=True,
        help='Probation period in months'
    )

    probation_end_date = fields.Date(
        string='Probation End Date ',
        compute='_compute_probation_end_date',
        store=True,
        help='Date when the probation period ends'
    )

    @api.depends('date_start', 'probation_period')
    def _compute_probation_end_date(self):
        for record in self:
            if record.date_start and record.probation_period:
                probation_months = int(record.probation_period.split()[0])
                record.probation_end_date = (record.date_start +
                                             relativedelta(months=probation_months))
            else:
                record.probation_end_date = False

    @api.constrains('employee_id',
                    'state',
                    'kanban_state',
                    'date_start',
                    'date_end')
    def _check_current_contract(self):
        """ Ensure contracts in 'open', 'close',
        'probation', and specific 'draft' states do not overlap. """
        for contract in self:
            if contract.state not in ['draft', 'cancel'] or (
                    contract.state == 'draft' and
                    contract.kanban_state == 'done'):
                domain = [
                    ('id', '!=', contract.id),
                    ('employee_id', '=', contract.employee_id.id),
                    ('company_id', '=', contract.company_id.id),
                    '|',
                    ('state', 'in', ['open', 'close', 'probation']),
                    '&',
                    ('state', '=', 'draft'),
                    ('kanban_state', '=', 'done'),
                ]

                if not contract.date_end:
                    date_domain = ['|', ('date_end', '>=',
                                         contract.date_start),
                                   ('date_end', '=', False)]
                else:
                    date_domain = ['&', ('date_start', '<=',
                                         contract.date_end),
                                   '|',
                                   ('date_end', '>=', contract.date_start),
                                   ('date_end', '=', False)]

                domain += date_domain

                if self.search_count(domain) > 0:
                    raise ValidationError(
                        _('An employee can only have one contract'
                          'in an "open", "close", "probation", or specific '
                          '"draft" state at the same time.'
                          'Please check the contract '
                          'dates and states to'
                          ' avoid '
                          'overlap.\n\n'
                          'Employee: %s') % contract.employee_id.name
                    )

    def update_probation_status(self):
        from_cron = 'from_cron' in self.env.context
        today = fields.Date.today()

        contracts_to_check = self.search([('state', 'in',
                                           ['probation', 'draft']),
                                          ('date_start', '!=', False)])

        for contract in contracts_to_check:
            probation_months = int(contract.probation_period.split()[0])
            probation_end_date = (contract.date_start +
                                  relativedelta(months=probation_months))

            if (contract.state == 'draft' and
                    contract.date_start <= today < probation_end_date):
                contract._safe_write_for_cron({'state': 'probation'},
                                              from_cron)
            elif contract.state == 'probation' and today >= probation_end_date:
                contract._safe_write_for_cron({'state': 'open'}, from_cron)
                self.send_probation_end_email(contract)

    def update_probation_create(self):

        today = fields.Date.today()
        if self.date_start and self.probation_period:
            probation_months = int(self.probation_period.split()[0])
            probation_end_date = (self.date_start +
                                  relativedelta(months=probation_months))

            if probation_months > 0 and today < probation_end_date:
                self.state = 'probation'
            elif today >= probation_end_date:
                self.state = 'open'

    @api.model
    def check_probation_period_notifications(self):
        today = fields.Date.today()
        notification_days = [60, 30, 15, 5, 1]
        self.update_probation_status()

        contracts = self.search([('date_start', '!=', False),
                                 ('state', '=', 'probation')])

        for contract in contracts:
            probation_months = int(contract.probation_period.split()[0])
            probation_end_date = (contract.date_start +
                                  relativedelta(months=probation_months))
            days_left = (probation_end_date - today).days
            if days_left in notification_days:
                self.send_probation_notification_email(contract, days_left)

            if days_left <= 0:
                self.send_probation_end_email(contract)

    def send_probation_notification_email(self, contract, days_left):
        template = self.env.ref('mo_employees_custom_fields.'
                                'email_template_probation_reminder')
        company_email = (contract.employee_id.company_id.email or
                         self.env.user.company_id.email)
        group_hr_user = self.env.ref('hr.group_hr_user')
        hr_users = group_hr_user.users
        if template:
            template.email_from = company_email
            email_subject = (f"Probation Period Reminder - "
                             f"{days_left} Days Left")
            for user in hr_users:
                if user.email:
                    template.send_mail(contract.employee_id.id,
                                       force_send=True,
                                       email_values={'email_to': user.email,
                                                     'subject': email_subject})

    def send_probation_end_email(self, contract):
        template = self.env.ref('mo_employees_custom_fields.'
                                'email_template_probation_end')
        company_email = (contract.employee_id.company_id.email or
                         self.env.user.company_id.email)
        group_hr_user = self.env.ref('hr.group_hr_user')
        hr_users = group_hr_user.users
        if template:
            template.email_from = company_email
            email_subject = "Probation Period Ended"
            for user in hr_users:
                if user.email:
                    template.send_mail(contract.employee_id.id,
                                       force_send=True,
                                       email_values={'email_to': user.email,
                                                     'subject': email_subject})

    @api.model
    def create(self, vals):

        contract = super(CustomContract, self).create(vals)
        contract.update_probation_create()
        return contract

    def write(self, vals):

        res = super(CustomContract, self).write(vals)
        for record in self:
            record.update_probation_status()
        return res


class CustomJob(models.Model):
    """Adding custom job
       fields"""
    _inherit = 'hr.job'

    contract_type_id = fields.Many2one('hr.contract.type',
                                       string='Employee Category',
                                       required=True,)
