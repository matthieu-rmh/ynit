# -*- coding: utf-8 -*-

{
    'name': "Ynov'IT Brandboard",
    'summary': "Customize Odoo for Ynov'IT Group",
    'description': """
        Brandboard - CSS - LOGO - FAVICON
    """,
    'author': "Ynov'IT Group",
    'website': "https://ynit.fr",
    'category': 'Extra Tools',
    'version': '16.0.0.1',
    'depends': ['base', 'web', 'base_setup', 'web_editor', 'website'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'data': [
        'views/templates.xml',
        'views/res_config.xml',
        'views/website_layout.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'https://fonts.googleapis.com/css?family=Mulish',
            'ynov_it_brandboard/static/src/css/custom.css',
            'ynov_it_brandboard/static/src/js/web_window_title.js',
        ],
        'web.assets_frontend': [
            'https://fonts.googleapis.com/css?family=Mulish',
            'ynov_it_brandboard/static/src/css/frontend.css',
        ],
        'web._assets_primary_variables': [
            'ynov_it_brandboard/static/src/scss/color_picker.scss',
        ]
    },
    'license': 'LGPL-3',
}
