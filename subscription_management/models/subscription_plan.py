# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
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
    price = fields.Float(
        string='Price',
        digits='Product Price',
        default=0.0,
        help='Default recurring price for this plan.'
    )
    min_quantity = fields.Float(
        string='Minimum Quantity',
        default=1.0,
        help='Minimum quantity required for subscriptions using this plan.'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
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
    subscription_count = fields.Integer(
        string='Subscriptions Count',
        compute='_compute_subscription_count'
    )

    def _compute_subscription_count(self):
        subscription_data = self.env['subscription.subscription']._read_group(
            domain=[('plan_id', 'in', self.ids)],
            groupby=['plan_id'],
            aggregates=['__count']
        )
        counts = {plan.id: count for plan, count in subscription_data}
        for plan in self:
            plan.subscription_count = counts.get(plan.id, 0)

    def action_view_subscriptions(self):
        self.ensure_one()
        return {
            'name': _('Subscriptions for Plan: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'subscription.subscription',
            'view_mode': 'list,form',
            'domain': [('plan_id', '=', self.id)],
            'context': {'default_plan_id': self.id},
        }

    @api.constrains('billing_interval_count')
    def _check_billing_interval_count(self):
        for plan in self:
            if plan.billing_interval_count <= 0:
                raise ValidationError(_('The billing interval count must be greater than 0.'))

    @api.constrains('trial_period_days')
    def _check_trial_period_days(self):
        for plan in self:
            if plan.trial_period_days < 0:
                raise ValidationError(_('The trial period cannot be negative.'))

    @api.constrains('price')
    def _check_price(self):
        for plan in self:
            if plan.price < 0:
                raise ValidationError(_('The plan price cannot be negative.'))

    @api.constrains('min_quantity')
    def _check_min_quantity(self):
        for plan in self:
            if plan.min_quantity <= 0:
                raise ValidationError(_('The minimum quantity must be greater than 0.'))
