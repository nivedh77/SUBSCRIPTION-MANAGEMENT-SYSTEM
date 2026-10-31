# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class SubscriptionDashboard(models.Model):
    _name = 'subscription.dashboard'
    _description = 'Subscription Live Analytics Dashboard'

    name = fields.Char(default='Live Dashboard Metrics', required=True)
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    # Real Database Statistics (Queried directly from PostgreSQL/ORM)
    total_subscriptions = fields.Integer(
        string='Total Subscriptions',
        compute='_compute_dashboard_stats'
    )
    active_subscriptions = fields.Integer(
        string='Active Subscriptions',
        compute='_compute_dashboard_stats'
    )
    closed_subscriptions = fields.Integer(
        string='Closed Subscriptions',
        compute='_compute_dashboard_stats'
    )
    paused_subscriptions = fields.Integer(
        string='Paused Subscriptions',
        compute='_compute_dashboard_stats'
    )
    draft_subscriptions = fields.Integer(
        string='Draft & Quotations',
        compute='_compute_dashboard_stats'
    )

    # Financial Metrics from actual account.move records
    revenue_received = fields.Monetary(
        string='Total Revenue Received',
        compute='_compute_dashboard_stats',
        currency_field='currency_id'
    )
    outstanding_invoices_amount = fields.Monetary(
        string='Outstanding Invoices',
        compute='_compute_dashboard_stats',
        currency_field='currency_id'
    )
    overdue_invoices_amount = fields.Monetary(
        string='Overdue Invoices',
        compute='_compute_dashboard_stats',
        currency_field='currency_id'
    )
    outstanding_invoices_count = fields.Integer(
        string='Outstanding Count',
        compute='_compute_dashboard_stats'
    )
    overdue_invoices_count = fields.Integer(
        string='Overdue Count',
        compute='_compute_dashboard_stats'
    )

    def _compute_dashboard_stats(self):
        today = fields.Date.context_today(self)
        sub_obj = self.env['subscription.subscription']
        move_obj = self.env['account.move']

        for rec in self:
            # Query actual database counts
            rec.total_subscriptions = sub_obj.search_count([])
            rec.active_subscriptions = sub_obj.search_count([('state', 'in', ('in_progress', 'confirmed'))])
            rec.closed_subscriptions = sub_obj.search_count([('state', '=', 'closed')])
            rec.paused_subscriptions = sub_obj.search_count([('state', '=', 'paused')])
            rec.draft_subscriptions = sub_obj.search_count([('state', 'in', ('draft', 'quotation'))])

            # Query real posted invoices linked to subscriptions
            subscription_moves = move_obj.search([
                ('subscription_id', '!=', False),
                ('state', '=', 'posted'),
                ('move_type', '=', 'out_invoice')
            ])

            rev = 0.0
            out_amt = 0.0
            overdue_amt = 0.0
            out_cnt = 0
            overdue_cnt = 0

            for move in subscription_moves:
                paid = move.amount_total - move.amount_residual
                rev += paid
                if move.amount_residual > 0:
                    out_amt += move.amount_residual
                    out_cnt += 1
                    due_date = move.invoice_date_due or move.invoice_date
                    if due_date and due_date < today:
                        overdue_amt += move.amount_residual
                        overdue_cnt += 1

            rec.revenue_received = rev
            rec.outstanding_invoices_amount = out_amt
            rec.overdue_invoices_amount = overdue_amt
            rec.outstanding_invoices_count = out_cnt
            rec.overdue_invoices_count = overdue_cnt

    @api.model
    def action_open_dashboard(self):
        """Find or create singleton dashboard record and open form view."""
        dashboard = self.search([], limit=1)
        if not dashboard:
            dashboard = self.create({'name': 'Live Dashboard Metrics'})
        return {
            'name': _('Subscription Analytics Dashboard'),
            'type': 'ir.actions.act_window',
            'res_model': 'subscription.dashboard',
            'res_id': dashboard.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # Action drilldowns from dashboard stat cards
    def action_view_all_subscriptions(self):
        return {
            'name': _('All Subscriptions'),
            'type': 'ir.actions.act_window',
            'res_model': 'subscription.subscription',
            'view_mode': 'list,kanban,form',
            'context': self.env.context,
        }

    def action_view_active_subscriptions(self):
        return {
            'name': _('Active Subscriptions'),
            'type': 'ir.actions.act_window',
            'res_model': 'subscription.subscription',
            'view_mode': 'list,kanban,form',
            'domain': [('state', 'in', ('in_progress', 'confirmed'))],
            'context': self.env.context,
        }

    def action_view_closed_subscriptions(self):
        return {
            'name': _('Closed Subscriptions'),
            'type': 'ir.actions.act_window',
            'res_model': 'subscription.subscription',
            'view_mode': 'list,form',
            'domain': [('state', '=', 'closed')],
            'context': self.env.context,
        }

    def action_view_outstanding_invoices(self):
        return {
            'name': _('Outstanding Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [
                ('subscription_id', '!=', False),
                ('state', '=', 'posted'),
                ('amount_residual', '>', 0),
            ],
        }

    def action_view_overdue_invoices(self):
        today = fields.Date.context_today(self)
        return {
            'name': _('Overdue Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [
                ('subscription_id', '!=', False),
                ('state', '=', 'posted'),
                ('amount_residual', '>', 0),
                ('invoice_date_due', '<', today),
            ],
        }

    def action_view_revenue_invoices(self):
        return {
            'name': _('Paid Subscription Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [
                ('subscription_id', '!=', False),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ('paid', 'in_payment')),
            ],
        }
