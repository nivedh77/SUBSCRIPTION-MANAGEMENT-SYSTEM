# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Subscription Management System',
    'version': '19.0.1.0.0',
    'category': 'Sales/Subscription',
    'summary': 'Complete Subscription Lifecycle Management for Odoo 19 Community',
    'description': """
Subscription Management System
==============================
A native Odoo 19 Community module built for the Odoo Makeathon 2026.

Features:
---------
* Subscription Plan Management (Daily, Weekly, Monthly, Yearly intervals)
* Role-based access control (Admin, Staff, Customer/Portal)
* Contract quotations, activations, pause, renewal, and cancellation
* Automated recurring invoice generation and tax calculation
* Discount management (fixed and percentage)
* Customer self-service portal
* Revenue analytics (MRR, ARR, active subscriber stats)
    """,
    'author': 'Nivedh M',
    'website': 'https://github.com/nivedh77/SUBSCRIPTION-MANAGEMENT-SYSTEM',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'product',
        'account',
        'portal',
    ],
    'data': [
        'security/subscription_security.xml',
        'security/ir.model.access.csv',
        'data/subscription_plan_data.xml',
        'views/subscription_plan_views.xml',
        'views/subscription_menus.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
