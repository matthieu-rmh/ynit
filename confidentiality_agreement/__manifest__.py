# -*- coding: utf-8 -*-


{
    'name': "confidentiality_agreement",
    'license': 'LGPL-3',
    'summary': "",
    'description': "",
    'author': "Ynov'IT Group",
    'website': "https://groupefbi.com/",
    'category': 'other',
    'version': '16.14.0.0.1',
    'depends': ['base'],
    'data': [
        'report/reports.xml',
        'report/ynit_confidentiality_agreement_report.xml',
        'views/views.xml',
    ],
    'assets': {
        'web.report_assets_common': [
            'confidentiality_agreement/static/src/css/fonts.css',
            'confidentiality_agreement/static/src/css/custom.css',
        ],
        
    },
    'application': True,
    'auto_install': False
}
