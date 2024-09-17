# -*- coding: utf-8 -*-

{
    'name': 'Hide Menu on Multi Company for Users',
    "author": "Ynov'iT Group",
    'version': '16.0.1.0',
    "images":['static/description/main_screenshot.png'],
    'summary': "",
    'description': """   """,
    "license" : "OPL-1",
    'depends': ['base'],
    'data': [
            'security/hide_menu_security.xml',
            'security/ir.model.access.csv',
            'views/view_main_hide.xml',
            ],
    'installable': True,
    'auto_install': False,
    'price': 10,
    'currency': "EUR",
    'category': 'Extra Tools',
    
}
