# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SubscriptionLine(models.Model):
    _name = 'subscription.line'
    _description = 'Subscription Line'
    _order = 'id asc'

    subscription_id = fields.Many2one(
        'subscription.subscription',
        string='Subscription',
        required=True,
        ondelete='cascade',
        index=True
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        domain="[('sale_ok', '=', True)]"
    )
    name = fields.Text(string='Description', required=True)
    quantity = fields.Float(string='Quantity', default=1.0, required=True)
    price_unit = fields.Monetary(string='Unit Price', required=True, default=0.0)
    discount = fields.Float(string='Discount (%)', default=0.0)
    tax_ids = fields.Many2many(
        'account.tax',
        string='Taxes',
        domain="[('type_tax_use', '=', 'sale')]"
    )
    currency_id = fields.Many2one(
        related='subscription_id.currency_id',
        string='Currency',
        store=True
    )
    company_id = fields.Many2one(
        related='subscription_id.company_id',
        string='Company',
        store=True
    )
    price_subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_amounts',
        store=True
    )
    price_tax = fields.Monetary(
        string='Tax',
        compute='_compute_amounts',
        store=True
    )
    price_total = fields.Monetary(
        string='Total',
        compute='_compute_amounts',
        store=True
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if not self.product_id:
            return
        company = self.company_id or self.env.company
        self.name = self.product_id.display_name
        # If subscription plan price is defined and greater than 0, default to plan price
        if self.subscription_id and self.subscription_id.plan_id and self.subscription_id.plan_id.price > 0:
            self.price_unit = self.subscription_id.plan_id.price
        else:
            self.price_unit = self.product_id.list_price
        taxes = self.product_id.taxes_id.filtered(lambda t: t.company_id == company)
        self.tax_ids = [(6, 0, taxes.ids)]

    @api.depends('quantity', 'price_unit', 'discount', 'tax_ids', 'currency_id')
    def _compute_amounts(self):
        for line in self:
            price = line.price_unit * (1.0 - (line.discount or 0.0) / 100.0)
            if line.tax_ids:
                taxes = line.tax_ids.compute_all(
                    price,
                    currency=line.currency_id,
                    quantity=line.quantity,
                    product=line.product_id,
                    partner=line.subscription_id.partner_id
                )
                line.price_subtotal = taxes['total_excluded']
                line.price_tax = taxes['total_included'] - taxes['total_excluded']
                line.price_total = taxes['total_included']
            else:
                subtotal = line.quantity * price
                line.price_subtotal = subtotal
                line.price_tax = 0.0
                line.price_total = subtotal

    @api.constrains('quantity')
    def _check_quantity(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(_('Line quantity must be strictly greater than 0.'))
            if line.subscription_id and line.subscription_id.plan_id:
                min_qty = line.subscription_id.plan_id.min_quantity
                if min_qty > 0 and line.quantity < min_qty:
                    raise ValidationError(_('Quantity (%(qty)s) is less than the plan minimum required volume (%(min_qty)s).') % {
                        'qty': line.quantity,
                        'min_qty': min_qty
                    })

    @api.constrains('price_unit')
    def _check_price_unit(self):
        for line in self:
            if line.price_unit < 0:
                raise ValidationError(_('Unit price cannot be negative.'))

    @api.constrains('discount')
    def _check_discount(self):
        for line in self:
            if line.discount < 0 or line.discount > 100:
                raise ValidationError(_('Line discount percentage must be between 0 and 100.'))
