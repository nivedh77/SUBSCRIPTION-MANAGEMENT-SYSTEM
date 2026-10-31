# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
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
        ('draft', 'Draft Quotation'),
        ('in_progress', 'Active'),
        ('paused', 'Paused'),
        ('closed', 'Closed'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, copy=False)

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
        currency_field='currency_id',
        tracking=True
    )
    mrr = fields.Monetary(
        string='Monthly Recurring Revenue (MRR)',
        compute='_compute_revenue_metrics',
        store=True,
        currency_field='currency_id',
        tracking=True
    )
    arr = fields.Monetary(
        string='Annual Recurring Revenue (ARR)',
        compute='_compute_revenue_metrics',
        store=True,
        currency_field='currency_id'
    )

    invoice_ids = fields.One2many(
        'account.move',
        'subscription_id',
        string='Invoices',
        readonly=True
    )
    invoice_count = fields.Integer(
        string='Invoice Count',
        compute='_compute_invoice_count'
    )

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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('subscription.subscription') or _('New')
        return super().create(vals_list)

    @api.onchange('plan_id')
    def _onchange_plan_id(self):
        if self.plan_id:
            self.auto_renew = self.plan_id.auto_renew
            if self.plan_id.description and not self.terms_and_conditions:
                self.terms_and_conditions = self.plan_id.description
            if self.date_start:
                if self.plan_id.trial_period_days > 0:
                    self.next_billing_date = self.date_start + relativedelta(days=self.plan_id.trial_period_days)
                else:
                    self.next_billing_date = self.date_start

    @api.depends('line_ids.price_subtotal', 'line_ids.price_tax', 'line_ids.price_total')
    def _compute_amounts(self):
        for sub in self:
            sub.amount_untaxed = sum(sub.line_ids.mapped('price_subtotal'))
            sub.amount_tax = sum(sub.line_ids.mapped('price_tax'))
            sub.amount_total = sum(sub.line_ids.mapped('price_total'))

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

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for sub in self:
            sub.invoice_count = len(sub.invoice_ids)

    def _get_next_date(self, current_date):
        self.ensure_one()
        if not self.plan_id:
            return current_date
        interval = self.plan_id.billing_interval
        count = self.plan_id.billing_interval_count or 1
        delta = relativedelta()

        if interval == 'daily':
            delta = relativedelta(days=count)
        elif interval == 'weekly':
            delta = relativedelta(weeks=count)
        elif interval == 'monthly':
            delta = relativedelta(months=count)
        elif interval == 'yearly':
            delta = relativedelta(years=count)

        return current_date + delta

    def action_confirm(self):
        for sub in self:
            if not sub.line_ids:
                raise UserError(_('Please add at least one subscription product line before confirming.'))
            if not sub.next_billing_date:
                if sub.plan_id.trial_period_days > 0:
                    sub.next_billing_date = sub.date_start + relativedelta(days=sub.plan_id.trial_period_days)
                else:
                    sub.next_billing_date = sub.date_start
            sub.write({'state': 'in_progress'})
            sub.message_post(body=_('Subscription confirmed and activated.'))

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

    def action_create_invoice(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_('Cannot generate an invoice for a subscription with no lines.'))

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.context_today(self),
            'currency_id': self.currency_id.id,
            'company_id': self.company_id.id,
            'subscription_id': self.id,
            'invoice_user_id': self.user_id.id,
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': line.product_id.id,
                    'name': f"{line.name} [{self.name}]",
                    'quantity': line.quantity,
                    'price_unit': line.price_unit,
                    'discount': line.discount,
                    'tax_ids': [(6, 0, line.tax_ids.ids)],
                }) for line in self.line_ids
            ]
        }
        invoice = self.env['account.move'].create(invoice_vals)

        # Advance next billing date
        from_date = self.next_billing_date or fields.Date.context_today(self)
        self.next_billing_date = self._get_next_date(from_date)

        # Check if contract expired
        if self.date_end and self.next_billing_date > self.date_end:
            if not self.auto_renew:
                self.write({'state': 'closed'})
                self.message_post(body=_('Contract term ended. Subscription closed automatically.'))

        self.message_post(body=_(
            'Recurring invoice <a href="#" data-oe-model="account.move" data-oe-id="%s">%s</a> generated.'
        ) % (invoice.id, invoice.name or invoice.id))

        return {
            'name': _('Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': invoice.id,
        }

    def action_view_invoices(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('account.action_move_out_invoice_type')
        action['domain'] = [('id', 'in', self.invoice_ids.ids)]
        action['context'] = {'default_subscription_id': self.id, 'default_move_type': 'out_invoice'}
        if len(self.invoice_ids) == 1:
            action['views'] = [(self.env.ref('account.view_move_form').id, 'form')]
            action['res_id'] = self.invoice_ids.id
        return action

    @api.model
    def _cron_recurring_create_invoice(self):
        """Automated cron method to find subscriptions ready for billing."""
        today = fields.Date.context_today(self)
        subscriptions = self.search([
            ('state', '=', 'in_progress'),
            ('next_billing_date', '<=', today),
        ])
        _logger.info('Subscription Cron: Found %s subscriptions to process.', len(subscriptions))
        for sub in subscriptions:
            try:
                sub.action_create_invoice()
                self.env.cr.commit()
            except Exception as e:
                self.env.cr.rollback()
                _logger.error('Failed to generate recurring invoice for subscription %s: %s', sub.name, str(e))
