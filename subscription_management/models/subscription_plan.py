# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SubscriptionPlan(models.Model):
    _name = 'subscription.plan'
    _description = 'Subscription Plan'
    _order = 'name'

    name = fields.Char(string='Plan Name', required=True, translate=True)
    code = fields.Char(string='Code', index=True, copy=False)
    active = fields.Boolean(string='Active', default=True)
    billing_interval = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ], string='Billing Frequency', default='monthly', required=True)
    billing_interval_count = fields.Integer(
        string='Repeat Every',
        default=1,
        required=True,
        help='Frequency interval count, e.g. every 1 month or every 3 months.'
    )
    trial_period_days = fields.Integer(
        string='Trial Period (Days)',
        default=0,
        help='Optional free trial period before first recurring invoice is generated.'
    )
    auto_renew = fields.Boolean(
        string='Auto Renew',
        default=True,
        help='If checked, subscription renews automatically upon reaching period end.'
    )
    description = fields.Html(string='Terms & Description')
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )

    @api.constrains('billing_interval_count')
    def _check_billing_interval_count(self):
        for plan in self:
            if plan.billing_interval_count <= 0:
                raise ValidationError('The billing interval count must be greater than 0.')

    @api.constrains('trial_period_days')
    def _check_trial_period_days(self):
        for plan in self:
            if plan.trial_period_days < 0:
                raise ValidationError('The trial period cannot be negative.')
