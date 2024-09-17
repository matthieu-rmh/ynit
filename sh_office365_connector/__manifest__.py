# Part of Softhealer Technologies.
{
    'name' : 'Office 365 - Odoo Connector',

    "author": "Softhealer Technologies",

    "license": "OPL-1",

    "website": "https://www.softhealer.com",

    "support": "support@softhealer.com",

    "version": "16.0.6",

    "category": "Extra Tools",

    # "summary": "Odoo Office 365 Connector Office 365 Connectors Office 365 with Odoo integration Odoo Office 365 Email Odoo Office 365 Connector API Office 365 Task Office 365 Mail Office 365 Contact Office 365 Calendar Office 365 Base Odoo Microsoft office 365 Connector Microsoft office 365 Connectors Microsoft office 365 Integration Microsoft office 365 Odoo Connector MS Office Connector MS Office Odoo Connector MS Office 365 Connector MS Office 365 Odoo Connector MS Office 365 Integration Office 365 Sync MS Office 365 Sync Microsoft Office 365 Sync Manage Office365 from Odoo excel odoo connector Calendar Connector Calendar Connectors Office 365 Calendar Connector MS Office 365 Calendar Connector Microsoft Office 365 Calendar Connector Office Calendar Connector Microsoft Office Calendar Connector MS Office Calendar Connector Calendar Integration Office 365 Calendar Integration MS Office 365 Calendar Integration Microsoft Office 365 Calendar Integration Office Calendar Integration MS Office Calendar Integration Microsoft Office Calendar Integration Office 365 Calendar Sync MS Office 365 Calendar Sync Microsoft Office 365 Calendar Sync Office Calendar Sync Microsoft Office Calendar Sync MS Office Calendar Sync Contact Connector Contact Connectors Office 365 Contact Connector MS Office 365 Contact Connector Microsoft Office 365 Contact Connector Office Contact Connector Microsoft Office Contact Connector MS Office Contact Connector Contact Integration Office 365 Contact Integration MS Office 365 Contact Integration Microsoft Office 365 Contact Integration Office Contact Integration MS Office Contact Integration Microsoft Office Contact Integration Office 365 Contact Sync MS Office 365 Contact Sync Microsoft Office 365 Contact Sync  Office Contact Sync Microsoft Office Contact Sync  MS Office Contact Sync Contacts Connector Task Connector Task Connectors Office 365 Task Connector MS Office 365 Task Connector Microsoft Office 365 Task Connector  Office Task Connector Microsoft Office Task Connector MS Office Task Connector Task Integration Office 365 Task Integration MS Office 365 Task Integration Microsoft Office 365 Task Integration Office Task Integration MS Office Task Integration Microsoft Office Task Integration Office 365 Task Sync MS Office 365 Task Sync Microsoft Office 365 Task Sync Office Task Sync Microsoft Office Task Sync MS Office Task Sync Tasks Connector Mail Connector Mail Connectors Office 365 Mail Connector MS Office 365 Mail Connector Microsoft Office 365 Mail Connector Office Mail Connector Microsoft Office Mail Connector MS Office Mail Connector Mail Integration Office 365 Mail Integration MS Office 365 Mail Integration Microsoft Office 365 Mail Integration Office Mail Integration MS Office Mail Integration Microsoft Office Mail Integration Office 365 Mail Sync MS Office 365 Mail Sync Microsoft Office 365 Mail Sync Office Mail Sync Microsoft Office Mail Sync MS Office Mail Sync Mails Connector Email Connector Email Connectors Office 365 Email Connector MS Office 365 Email Connector Microsoft Office 365 Email Connector Office Email Connector Microsoft Office Email Connector  MS Office Email Connector Email Integration Office 365 Email Integration MS Office 365 Email Integration Microsoft Office 365 Email Integration Office Email Integration MS Office Email Integration Microsoft Office Email Integration Office 365 Email Sync MS Office 365 Email Sync Microsoft Office 365 Email Sync Office Email Sync Microsoft Office Email Sync MS Office Email Sync Emails Connector",
    #
    # "description": """Nowadays, Office 365 is a widely used cloud-based application. Here in odoo there are no options to sync your office-365 calendar, mails, contacts, and task. Using this application you can easily sync your office-365 stuff with odoo in just one click. Just setup once and import calendar, task, contacts, mails from one place.""",
    
    "summary": "Odoo Office 365 Connector",

    "description": """Office-365 calendar, mails, contacts, and task.""",
    
    'depends' : ['base_setup','contacts','calendar'],
    
    'data' : [
        'sh_office365_base/security/ir.model.access.csv',
        'sh_office365_base/security/sh_office365_groups.xml',
        'sh_office365_base/security/sh_office365_rules.xml',
        'sh_office365_base/data/sh_office365_queue_data.xml',
        'sh_office365_base/views/sh_office365_base_config_views.xml',
        'sh_office365_base/views/sh_office365_base_log_views.xml',
        'sh_office365_base/views/sh_office365_queue_views.xml',

        'sh_office365_calendar/data/calendar_event_data.xml',
        'sh_office365_calendar/data/sh_office365_config_data.xml',
        'sh_office365_calendar/views/sh_calendar_config_views.xml',
        'sh_office365_calendar/views/calendar_event_views.xml',
        'sh_office365_calendar/views/sh_calendar_queue_views.xml',

        'sh_office365_contact/data/res_partner_data.xml',
        'sh_office365_contact/data/sh_office365_config_data.xml',
        # 'sh_office365_contact/views/sh_office365_contact_views.xml',
        'sh_office365_contact/views/sh_office_contact_queue.xml',
        # 'sh_office365_contact/views/res_partner_views.xml',

        'sh_office365_mail/data/sh_office365_config_data.xml',
        # 'sh_office365_mail/views/sh_office365_config_views.xml',

        'sh_office365_tasks/data/sh_office365_config_data.xml',
        # 'sh_office365_tasks/views/sh_office365_task_config_views.xml',
        
        'security/ir_rules.xml'
    ],
    
    'demo' : [],
    'installation': True,
    'application' : True,
    'auto_install' : False,
    "images": ["static/description/background.png", ],
    "price": "100",
    "currency": "EUR"
}
