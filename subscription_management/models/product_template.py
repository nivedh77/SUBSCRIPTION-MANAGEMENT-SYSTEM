# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_subscription = fields.Boolean(
        string='Is Subscription Product',
        default=False,
        help='Check this box if this product is sold as a recurring subscription.'
    )
    subscription_plan_id = fields.Many2one(
        'subscription.plan',
        string='Default Subscription Plan',
        help='Default plan used when selling this product as a subscription.'
    )
