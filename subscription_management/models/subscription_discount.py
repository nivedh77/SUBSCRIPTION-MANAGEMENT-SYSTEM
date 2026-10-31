# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SubscriptionDiscount(models.Model):
    _name = 'subscription.discount'
    _description = 'Subscription Discount'
    _order = 'name'

    name = fields.Char(string='Discount Name', required=True, translate=True)
    code = fields.Char(string='Coupon / Discount Code', required=True, index=True, copy=False)
    active = fields.Boolean(string='Active', default=True)
    discount_type = fields.Selection([
        ('percentage', 'Percentage (%)'),
        ('fixed', 'Fixed Amount'),
    ], string='Discount Type', default='percentage', required=True)
    discount_value = fields.Float(
        string='Discount Value',
        required=True,
        digits='Product Price',
        help='Percentage value (e.g. 15 for 15%) or fixed amount (e.g. 50).'
    )
    start_date = fields.Date(string='Start Date', help='First day discount is applicable.')
    end_date = fields.Date(string='End Date', help='Last day discount is applicable.')
    min_purchase_amount = fields.Float(
        string='Minimum Purchase Amount',
        default=0.0,
        digits='Product Price',
        help='Minimum subscription subtotal required to apply this discount.'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    description = fields.Text(string='Terms & Conditions')

    _sql_constraints = [
        ('code_company_uniq', 'unique(code, company_id)', 'Discount code must be unique per company!'),
    ]

    @api.constrains('discount_type', 'discount_value')
    def _check_discount_value(self):
        for discount in self:
            if discount.discount_value <= 0:
                raise ValidationError(_('Discount value must be strictly positive.'))
            if discount.discount_type == 'percentage' and discount.discount_value > 100:
                raise ValidationError(_('Percentage discount value cannot exceed 100%.'))

    @api.constrains('min_purchase_amount')
    def _check_min_purchase_amount(self):
        for discount in self:
            if discount.min_purchase_amount < 0:
                raise ValidationError(_('Minimum purchase amount cannot be negative.'))

    @api.constrains('start_date', 'end_date')
    def _check_validity_dates(self):
        for discount in self:
            if discount.start_date and discount.end_date and discount.end_date < discount.start_date:
                raise ValidationError(_('Discount End Date must be greater than or equal to Start Date.'))

    def is_eligible(self, subtotal, check_date=None):
        """Check if discount is currently active, within valid dates and subtotal meets minimum."""
        self.ensure_one()
        if not self.active:
            return False
        check_date = check_date or fields.Date.context_today(self)
        if self.start_date and check_date < self.start_date:
            return False
        if self.end_date and check_date > self.end_date:
            return False
        if subtotal < self.min_purchase_amount:
            return False
        return True

    def calculate_discount_amount(self, subtotal):
        """Calculate and return the monetary discount amount on a given subtotal."""
        self.ensure_one()
        if subtotal <= 0:
            return 0.0
        if self.discount_type == 'percentage':
            return round((subtotal * self.discount_value) / 100.0, 2)
        elif self.discount_type == 'fixed':
            return min(subtotal, round(self.discount_value, 2))
        return 0.0
