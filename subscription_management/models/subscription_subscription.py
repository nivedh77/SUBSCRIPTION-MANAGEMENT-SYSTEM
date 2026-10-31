# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from datetime import timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SubscriptionSubscription(models.Model):
    _name = 'subscription.subscription'
    _description = 'Subscription Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True
    )
    plan_id = fields.Many2one(
        'subscription.plan',
        string='Subscription Plan',
        required=True,
        tracking=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )
    user_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        default=lambda self: self.env.user,
        tracking=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('quotation', 'Quotation'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'Active'),
        ('paused', 'Paused'),
        ('closed', 'Closed'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, copy=False, index=True)

    date_start = fields.Date(
        string='Start Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True
    )
    date_end = fields.Date(
        string='End Date',
        help='Optional contract expiration date. Leave blank for ongoing subscriptions.',
        tracking=True
    )
    start_date = fields.Date(
        related='date_start',
        string='Start Date (Alias)',
        readonly=False
    )
    end_date = fields.Date(
        related='date_end',
        string='End Date (Alias)',
        readonly=False
    )
    next_billing_date = fields.Date(
        string='Next Billing Date',
        tracking=True,
        copy=False
    )
    auto_renew = fields.Boolean(
        string='Auto Renew',
        default=True,
        help='Automatically renews and bills on next billing date.'
    )

    line_ids = fields.One2many(
        'subscription.line',
        'subscription_id',
        string='Subscription Lines',
        copy=True
    )

    # Promotional Discount
    discount_id = fields.Many2one(
        'subscription.discount',
        string='Promotional Discount',
        domain="[('active', '=', True)]",
        help='Promotional voucher or discount applied to recurring contract.'
    )
    discount_amount = fields.Monetary(
        string='Discount Amount',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )

    # Computed Totals
    amount_untaxed = fields.Monetary(
        string='Untaxed Amount',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )
    amount_tax = fields.Monetary(
        string='Taxes',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )
    amount_total = fields.Monetary(
        string='Total Recurring Amount',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )

    # Revenue Metrics
    mrr = fields.Monetary(
        string='Monthly Recurring Revenue (MRR)',
        compute='_compute_revenue_metrics',
        store=True,
        currency_field='currency_id'
    )
    arr = fields.Monetary(
        string='Annual Recurring Revenue (ARR)',
        compute='_compute_revenue_metrics',
        store=True,
        currency_field='currency_id'
    )

    # Invoices & Accounting Payment Tracking
    invoice_ids = fields.One2many(
        'account.move',
        'subscription_id',
        string='Invoices',
        readonly=True
    )
    invoice_count = fields.Integer(
        string='Invoice Count',
        compute='_compute_invoice_stats'
    )
    amount_paid = fields.Monetary(
        string='Total Paid',
        compute='_compute_invoice_stats',
        currency_field='currency_id'
    )
    amount_due = fields.Monetary(
        string='Outstanding Due',
        compute='_compute_invoice_stats',
        currency_field='currency_id'
    )
    amount_overdue = fields.Monetary(
        string='Overdue Amount',
        compute='_compute_invoice_stats',
        currency_field='currency_id'
    )
    payment_status = fields.Selection([
        ('no_invoices', 'No Invoices'),
        ('paid', 'Fully Paid'),
        ('partial', 'Partially Paid'),
        ('pending', 'Payment Pending'),
        ('overdue', 'Overdue'),
    ], string='Payment Status', compute='_compute_invoice_stats')

    close_reason_id = fields.Many2one(
        'subscription.close.reason',
        string='Close Reason',
        copy=False,
        tracking=True
    )
    close_notes = fields.Text(
        string='Close Notes',
        copy=False
    )
    terms_and_conditions = fields.Html(
        string='Terms and Conditions'
    )

    # -------------------------------------------------------------------------
    # CRUD & ORM
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('subscription.subscription')
                    or _('New')
                )
        return super().create(vals_list)

    # -------------------------------------------------------------------------
    # CONSTRAINTS & ONCHANGE
    # -------------------------------------------------------------------------
    @api.constrains('date_start', 'date_end')
    def _check_contract_dates(self):
        for sub in self:
            if sub.date_start and sub.date_end and sub.date_end < sub.date_start:
                raise ValidationError(_('Contract End Date cannot be earlier than Start Date.'))

    @api.constrains('date_start', 'next_billing_date')
    def _check_billing_dates(self):
        for sub in self:
            if sub.date_start and sub.next_billing_date and sub.next_billing_date < sub.date_start:
                raise ValidationError(_('Next Billing Date cannot be earlier than Start Date.'))

    @api.onchange('plan_id')
    def _onchange_plan_id(self):
        if self.plan_id:
            self.auto_renew = self.plan_id.auto_renew
            if self.plan_id.description and not self.terms_and_conditions:
                self.terms_and_conditions = self.plan_id.description
            base_date = self.date_start or fields.Date.context_today(self)
            if self.plan_id.trial_period_days > 0:
                self.next_billing_date = base_date + relativedelta(days=self.plan_id.trial_period_days)
            else:
                self.next_billing_date = base_date

    # -------------------------------------------------------------------------
    # COMPUTED METHODS
    # -------------------------------------------------------------------------
    @api.depends('line_ids.price_subtotal', 'line_ids.price_tax', 'line_ids.price_total', 'discount_id')
    def _compute_amounts(self):
        for sub in self:
            untaxed = sum(sub.line_ids.mapped('price_subtotal'))
            
            # Apply eligible discount
            discount = 0.0
            if sub.discount_id and sub.discount_id.is_eligible(untaxed, sub.date_start):
                discount = sub.discount_id.calculate_discount_amount(untaxed)

            sub.discount_amount = discount
            effective_untaxed = max(0.0, untaxed - discount)
            taxes = sum(sub.line_ids.mapped('price_tax'))

            sub.amount_untaxed = untaxed
            sub.amount_tax = taxes
            sub.amount_total = effective_untaxed + taxes

    @api.depends('amount_total', 'plan_id.billing_interval', 'plan_id.billing_interval_count')
    def _compute_revenue_metrics(self):
        for sub in self:
            if not sub.plan_id or not sub.plan_id.billing_interval_count:
                sub.mrr = 0.0
                sub.arr = 0.0
                continue

            interval = sub.plan_id.billing_interval
            count = max(sub.plan_id.billing_interval_count, 1)
            total = sub.amount_total

            if interval == 'daily':
                sub.mrr = (total / count) * 30.0
            elif interval == 'weekly':
                sub.mrr = (total / count) * (52.0 / 12.0)
            elif interval == 'monthly':
                sub.mrr = total / count
            elif interval == 'yearly':
                sub.mrr = (total / count) / 12.0
            else:
                sub.mrr = total

            sub.arr = sub.mrr * 12.0

    def _compute_invoice_stats(self):
        today = fields.Date.context_today(self)
        for sub in self:
            invoices = sub.invoice_ids.filtered(lambda m: m.state != 'cancel')
            sub.invoice_count = len(invoices)

            if not invoices:
                sub.amount_paid = 0.0
                sub.amount_due = 0.0
                sub.amount_overdue = 0.0
                sub.payment_status = 'no_invoices'
                continue

            posted_invoices = invoices.filtered(lambda m: m.state == 'posted')
            paid_sum = 0.0
            due_sum = 0.0
            overdue_sum = 0.0

            for inv in posted_invoices:
                paid_sum += (inv.amount_total - inv.amount_residual)
                if inv.amount_residual > 0:
                    due_sum += inv.amount_residual
                    due_date = inv.invoice_date_due or inv.invoice_date
                    if due_date and due_date < today:
                        overdue_sum += inv.amount_residual

            sub.amount_paid = paid_sum
            sub.amount_due = due_sum
            sub.amount_overdue = overdue_sum

            if due_sum <= 0 and paid_sum > 0:
                sub.payment_status = 'paid'
            elif overdue_sum > 0:
                sub.payment_status = 'overdue'
            elif paid_sum > 0 and due_sum > 0:
                sub.payment_status = 'partial'
            elif due_sum > 0:
                sub.payment_status = 'pending'
            else:
                sub.payment_status = 'no_invoices'

    # -------------------------------------------------------------------------
    # STATE TRANSITIONS & ACTIONS
    # -------------------------------------------------------------------------
    def _get_next_date(self, current_date):
        self.ensure_one()
        if not self.plan_id:
            return current_date
        interval = self.plan_id.billing_interval
        count = self.plan_id.billing_interval_count or 1

        if interval == 'daily':
            return current_date + timedelta(days=count)
        elif interval == 'weekly':
            return current_date + relativedelta(weeks=count)
        elif interval == 'monthly':
            return current_date + relativedelta(months=count)
        elif interval == 'yearly':
            return current_date + relativedelta(years=count)
        return current_date + relativedelta(months=1)

    def action_quotation(self):
        self.write({'state': 'quotation'})
        self.message_post(body=_('Quotation generated for customer.'))

    def action_confirm(self):
        for sub in self:
            if not sub.line_ids:
                raise UserError(_('Please add at least one subscription product line before confirming.'))
            for line in sub.line_ids:
                if line.quantity <= 0:
                    raise UserError(_('All line quantities must be strictly greater than 0.'))
            if not sub.next_billing_date:
                base_date = sub.date_start or fields.Date.context_today(sub)
                if sub.plan_id.trial_period_days > 0:
                    sub.next_billing_date = base_date + relativedelta(days=sub.plan_id.trial_period_days)
                else:
                    sub.next_billing_date = base_date
            sub.write({'state': 'confirmed'})
            sub.message_post(body=_('Subscription quotation confirmed.'))

    def action_activate(self):
        for sub in self:
            if not sub.line_ids:
                raise UserError(_('Cannot activate a subscription without product lines.'))
            if not sub.next_billing_date:
                sub.next_billing_date = sub.date_start or fields.Date.context_today(sub)
            sub.write({'state': 'in_progress'})
            sub.message_post(body=_('Subscription activated.'))

    def action_pause(self):
        for sub in self:
            sub.write({'state': 'paused'})
            sub.message_post(body=_('Subscription has been paused.'))

    def action_resume(self):
        for sub in self:
            sub.write({'state': 'in_progress'})
            sub.message_post(body=_('Subscription resumed to active status.'))

    def action_close(self):
        for sub in self:
            sub.write({'state': 'closed'})
            sub.message_post(body=_('Subscription has been closed.'))

    def action_cancel(self):
        for sub in self:
            sub.write({'state': 'cancel'})
            sub.message_post(body=_('Subscription has been cancelled.'))

    def action_draft(self):
        for sub in self:
            sub.write({'state': 'draft'})
            sub.message_post(body=_('Subscription reset to draft.'))

    # -------------------------------------------------------------------------
    # RECURRING INVOICING ENGINE
    # -------------------------------------------------------------------------
    def action_create_invoice(self):
        """Generate recurring customer invoice for active subscription with duplicate protection."""
        today = fields.Date.context_today(self)
        invoices = self.env['account.move']

        for sub in self:
            if sub.state != 'in_progress':
                raise UserError(_('Invoices can only be generated for Active subscriptions.'))

            if not sub.partner_id:
                raise UserError(_('Customer is required on subscription %s to generate an invoice.') % sub.name)

            if not sub.line_ids:
                raise UserError(_('Subscription %s has no lines to bill.') % sub.name)

            billing_date = sub.next_billing_date or today

            # Duplicate Invoice Prevention: verify no existing invoice for this subscription and period
            existing_invoice = self.env['account.move'].search([
                ('subscription_id', '=', sub.id),
                ('subscription_billing_date', '=', billing_date),
                ('state', '!=', 'cancel')
            ], limit=1)

            if existing_invoice:
                raise UserError(_(
                    'An invoice (%(inv)s) has already been created for subscription %(sub)s for billing date %(date)s.'
                ) % {
                    'inv': existing_invoice.name or existing_invoice.id,
                    'sub': sub.name,
                    'date': billing_date
                })

            invoice_lines = []
            for line in sub.line_ids:
                invoice_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': f"{line.name} [{sub.name} - Period: {billing_date}]",
                    'quantity': line.quantity,
                    'price_unit': line.price_unit,
                    'discount': line.discount,
                    'tax_ids': [(6, 0, line.tax_ids.ids)],
                }))

            # If coupon discount applies, add discount line
            if sub.discount_id and sub.discount_id.is_eligible(sub.amount_untaxed, billing_date):
                discount_val = sub.discount_id.calculate_discount_amount(sub.amount_untaxed)
                if discount_val > 0:
                    invoice_lines.append((0, 0, {
                        'name': f"Discount: {sub.discount_id.name} [{sub.discount_id.code}]",
                        'quantity': 1,
                        'price_unit': -discount_val,
                    }))

            invoice_vals = {
                'move_type': 'out_invoice',
                'partner_id': sub.partner_id.id,
                'invoice_date': today,
                'invoice_date_due': billing_date,
                'currency_id': sub.currency_id.id,
                'company_id': sub.company_id.id,
                'subscription_id': sub.id,
                'subscription_billing_date': billing_date,
                'invoice_user_id': sub.user_id.id,
                'ref': f"{sub.name} - {sub.plan_id.name}",
                'invoice_line_ids': invoice_lines,
            }

            created_inv = self.env['account.move'].create(invoice_vals)
            invoices |= created_inv

            # Advance next billing date
            from_date = billing_date
            next_date = sub._get_next_date(from_date)

            # Check if contract expired
            if sub.date_end and next_date > sub.date_end and not sub.auto_renew:
                sub.write({
                    'next_billing_date': next_date,
                    'state': 'closed'
                })
                sub.message_post(body=_('Contract term reached. Subscription closed automatically.'))
            else:
                sub.write({'next_billing_date': next_date})

            sub.message_post(body=_(
                'Recurring invoice <a href="#" data-oe-model="account.move" data-oe-id="%s">%s</a> generated for period %s.'
            ) % (created_inv.id, created_inv.name or created_inv.id, billing_date))

        if len(invoices) == 1:
            return {
                'name': _('Customer Invoice'),
                'view_mode': 'form',
                'res_model': 'account.move',
                'res_id': invoices.id,
                'type': 'ir.actions.act_window',
            }
        elif invoices:
            return {
                'name': _('Generated Invoices'),
                'view_mode': 'list,form',
                'res_model': 'account.move',
                'domain': [('id', 'in', invoices.ids)],
                'type': 'ir.actions.act_window',
            }
        return False

    def action_view_invoices(self):
        self.ensure_one()
        return {
            'name': _('Invoices for %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('subscription_id', '=', self.id)],
            'context': {
                'default_move_type': 'out_invoice',
                'default_partner_id': self.partner_id.id,
                'default_subscription_id': self.id,
            }
        }

    # -------------------------------------------------------------------------
    # AUTOMATED CRON RECURRING BILLING
    # -------------------------------------------------------------------------
    @api.model
    def _cron_recurring_create_invoice(self):
        """Automated cron method to find subscriptions ready for billing and process each safely."""
        today = fields.Date.context_today(self)
        subscriptions = self.search([
            ('state', '=', 'in_progress'),
            ('next_billing_date', '<=', today),
        ])
        _logger.info('Subscription Cron: Found %s subscriptions due for recurring billing on %s.', len(subscriptions), today)
        for sub in subscriptions:
            try:
                sub.action_create_invoice()
            except Exception as e:
                _logger.error('Failed to generate recurring invoice for subscription %s: %s', sub.name, str(e))
                continue

    @api.model
    def _cron_generate_recurring_invoices(self):
        """Alias for _cron_recurring_create_invoice to ensure compatibility."""
        return self._cron_recurring_create_invoice()
