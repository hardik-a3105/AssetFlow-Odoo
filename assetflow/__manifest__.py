# -*- coding: utf-8 -*-
{
    'name': 'AssetFlow',
    'version': '1.0',
    'summary': 'Enterprise Asset & Resource Management System',
    'description': """
        AssetFlow is an Enterprise Asset & Resource Management System for Odoo.
    """,
    'category': 'Operations',
    'author': 'Antigravity',
    'depends': ['base', 'mail', 'auth_signup'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/dashboard_views.xml',
        'views/org_setup_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'assetflow/static/src/dashboard/dashboard.js',
            'assetflow/static/src/dashboard/dashboard.xml',
            'assetflow/static/src/dashboard/dashboard.css',
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
