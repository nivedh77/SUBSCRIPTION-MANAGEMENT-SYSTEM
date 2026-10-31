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
A native Odoo 19 Community module built for the Odoo Makeathon / Hackathon 2026.

Features:
---------
* Subscription Plan Management (Daily, Weekly, Monthly, Yearly intervals)
* Role-based access control (Admin, Staff, Customer/Portal)
* Contract quotations, activations, pause, renewal, and cancellation
* Automated recurring invoice generation via daily cron
* Real-time MRR and ARR revenue analytics with Pivot & Graph views
* Customer self-service portal (/my/subscriptions) with cancellation requests
* Churn and cancellation tracking reasons
    """,
    'author': 'Team STRANGERS (Nivedh M, Rashmi Krishna P)',
    'website': 'https://github.com/nivedh77/SUBSCRIPTION-MANAGEMENT-SYSTEM',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'product',
        'account',
        'portal',
    ],
    'data': [
        'security/subscription_security.xml',
        'security/ir.model.access.csv',
        'data/subscription_sequence.xml',
        'data/subscription_cron.xml',
        'data/subscription_close_reason_data.xml',
        'data/subscription_plan_data.xml',
        'views/subscription_views.xml',
        'views/subscription_plan_views.xml',
        'views/subscription_close_reason_views.xml',
        'views/subscription_product_views.xml',
        'views/portal_subscription_templates.xml',
        'views/subscription_menus.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
}
