# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError


class CustomerSubscriptionPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'subscription_count' in counters:
            partner = request.env.user.partner_id
            values['subscription_count'] = request.env['subscription.subscription'].search_count([
                ('partner_id', 'child_of', [partner.commercial_partner_id.id])
            ]) if request.env['subscription.subscription'].check_access_rights('read', raise_exception=False) else 0
        return values

    @http.route(['/my/subscriptions', '/my/subscriptions/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_subscriptions(self, page=1, sortby=None, **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        Subscription = request.env['subscription.subscription']

        domain = [('partner_id', 'child_of', [partner.commercial_partner_id.id])]
        sub_count = Subscription.search_count(domain)

        pager = portal_pager(
            url='/my/subscriptions',
            total=sub_count,
            page=page,
            step=10
        )

        subscriptions = Subscription.search(
            domain,
            order='id desc',
            limit=10,
            offset=pager['offset']
        )

        values.update({
            'subscriptions': subscriptions,
            'page_name': 'subscription',
            'pager': pager,
            'default_url': '/my/subscriptions',
        })
        return request.render('subscription_management.portal_my_subscriptions', values)

    @http.route(['/my/subscriptions/<int:sub_id>'], type='http', auth='user', website=True)
    def portal_subscription_page(self, sub_id=None, **kw):
        try:
            sub_sudo = request.env['subscription.subscription'].sudo().browse(sub_id)
            if not sub_sudo.exists():
                raise MissingError(_('This subscription does not exist.'))
            commercial_partner = request.env.user.partner_id.commercial_partner_id
            if sub_sudo.partner_id.commercial_partner_id != commercial_partner:
                raise AccessError(_('You do not have access to this subscription.'))
        except (AccessError, MissingError):
            return request.redirect('/my')

        values = {
            'subscription': sub_sudo,
            'page_name': 'subscription',
        }
        return request.render('subscription_management.portal_subscription_page', values)

    @http.route(['/my/subscriptions/<int:sub_id>/cancel'], type='http', auth='user', methods=['POST'], website=True)
    def portal_subscription_cancel(self, sub_id=None, reason=None, **kw):
        sub_sudo = request.env['subscription.subscription'].sudo().browse(sub_id)
        commercial_partner = request.env.user.partner_id.commercial_partner_id
        if sub_sudo.exists() and sub_sudo.partner_id.commercial_partner_id == commercial_partner:
            if sub_sudo.state in ('draft', 'in_progress', 'paused'):
                sub_sudo.message_post(
                    body=_('Customer requested subscription cancellation from portal. Feedback: %s') % (reason or _('No reason provided'))
                )
                sub_sudo.write({
                    'close_notes': f"Portal Request: {reason}" if reason else "Cancelled via Customer Portal",
                    'state': 'closed'
                })
        return request.redirect(f'/my/subscriptions/{sub_id}')
