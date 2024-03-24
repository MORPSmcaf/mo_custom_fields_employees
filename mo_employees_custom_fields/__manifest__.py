{
    'name': "HR Employee Custom Fields",
    'summary': "Custom HR Employee Information",
    'version': '16.0.1.0.0',
    'website': "https://mcaf.nb.ca/en/",
    'author': "MCAF",
    'category': "HR",
    'license': 'OPL-1',
    "application": True,
    "installable": True,
    'depends': ['base', 'hr', 'om_hr_payroll', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'data/kron_data.xml',
        'views/hr_employee_views.xml',
        'views/hr_contract_views.xml',
        'data/employee_birthday_template.xml',
        'data/employee_90_days_confirm_template.xml',
        'data/employee_end_probation.xml',
        'data/employee_reminder_probation.xml',
        'data/employee_tier_update.xml',
    ],

    'assets': {
        'web.assets_backend': [
            '/mo_employees_custom_fields/static/src/css/test.css',
            'mo_employees_custom_fields/static/src/js/test.js',
            'mo_employees_custom_fields/static/src/xml/bold.xml',
        ],

    },
}
