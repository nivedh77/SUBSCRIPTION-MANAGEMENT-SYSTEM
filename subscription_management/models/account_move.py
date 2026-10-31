# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    subscription_id = fields.Many2one(
        'subscription.subscription',
        string='Subscription',
        copy=False,
        index=True,
        help='The subscription order that generated this recurring invoice.'
    )
    subscription_billing_date = fields.Date(
        string='Subscription Billing Period',
        copy=False,
        help='Target billing date for the subscription recurring period.'
    )
