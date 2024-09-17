# -*- coding: utf-8 -*-


{
    'name': "fbi_crm",
    'license': 'LGPL-3',
    'summary': "",
    'description': "",
    'author': "Ynov'IT Group",
    'website': "https://groupefbi.com/",
    'category': 'other',
    'version': '16.14.0.0.1',
    'depends': ['crm', 'calendar', 'crm_iap_enrich', 'mail_ynov_it_bcc'],
    'data': [
        'security/fbi_crm_security.xml',
        'views/calendar_event_view.xml',
        'views/calendar_views.xml',
        'views/crm_code_relance_views.xml',
        'views/crm_code_naf_family_views.xml',
        'views/crm_commercial_annonce_views.xml',
        'views/crm_lead_views.xml',
        'views/crm_menu_views.xml',
        'views/res_users_views.xml',
        'data/crm_code_relance_data.xml',
        'data/crm_stage_data.xml',
        'data/crm_commercial_annonce_data.xml',
        'data/ir_action_data.xml',
        'data/mail_activity_type_data.xml',
        'data/crm_team_data.xml',
        'data/ir_cron.xml',
        'report/crm_lead_templates.xml',
        'report/crm_lead_reports.xml',
        'report/crm_activity_report.xml',
        'report/calendar_event_views.xml',
        'report/crm_lead_date_deadline_history.xml',
        'data/mail_template_data.xml',
        'security/ir.model.access.csv',
        'wizard/lead_non_exploitable_mass_log.xml',
        'wizard/lead_choice_telemarketer.xml',
        'views/fbi_lead_email_to.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'fbi_crm/static/src/views/**/*',
            'fbi_crm/static/src/css/custom.css',
        ],
    },
    'application': True,
    'auto_install': False
}
