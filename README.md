# 🔄 Subscription Management System for Odoo 19 Community

> Built for the **Odoo Makeathon / Hackathon 2026** by Team STRANGERS: [Nivedh M](https://github.com/nivedh77) and [RASHMI KRISHNA P](https://github.com/rashmikrishnap).

A robust, enterprise-grade, native **Odoo 19 Community Edition** module providing complete recurring subscription lifecycle management, automated invoicing with Odoo `account.move`, promotional discounts, payment tracking, customer isolation security rules, customer self-service portal, and real-time database KPI analytics.

---

## 🚀 Implemented Features

### A. Subscription Plans (`subscription.plan`)
- Plan name, code, description, and active/inactive archive toggle.
- Billing frequencies: **Daily**, **Weekly**, **Monthly**, and **Yearly** with custom repeat count.
- Unit pricing and minimum required subscription volume constraints.
- Free introductory trial periods in days.
- Auto-renew toggling and multi-company support.

### B. Subscriptions (`subscription.subscription`)
- Automatic sequential reference generation (`SUB/2026/00001`).
- Customer selection linked to `res.partner`.
- Subscription plan integration with automatic billing date calculation.
- Start date, end date, and next billing date tracking with strict validation.
- Multi-line subscription details (`subscription.line`): products, descriptions, quantities, unit prices, taxes, and subtotals.
- Lifecycle stages: **Draft → Quotation → Confirmed → Active → Paused → Closed → Cancelled**.
- Complete action workflow: Create Quotation, Confirm, Activate, Pause, Resume, Close, and Reset to Draft.
- Comprehensive date and quantity integrity constraints.

### C. Recurring Invoices (`account.move` Integration)
- Native integration with Odoo's Invoicing module (`move_type='out_invoice'`).
- Manual and automated recurring invoice generation for active due subscriptions.
- Duplicate invoice prevention for the same subscription and billing period.
- Automatic calculation and advancement of `next_billing_date` based on plan interval.
- Safe handling of invalid data or missing partners without data corruption.
- Invoices remain in draft/posted states without artificially marking them paid.

### D. Promotional Discounts (`subscription.discount`)
- Fixed amount and percentage-based discounts.
- Date validity windows (`start_date` to `end_date`).
- Minimum purchase subtotal thresholds.
- Eligible discount computation applied dynamically to subscription totals and invoice line generation.
- Strict validation rules (percentage bounded between 0% and 100%, positive amounts).

### E. Payments & Accounting Visibility
- Live synchronization with Odoo account payments and invoice residuals.
- Real-time tracking of:
  - Total Paid Amount
  - Outstanding Balance Due
  - Overdue Receivables
- Visual payment status badges: *Fully Paid*, *Partially Paid*, *Payment Pending*, *Overdue*.

### F. Real Database KPI Dashboard (`subscription.dashboard`)
- Zero hardcoded mock numbers—100% computed from real database tables and ORM records:
  - Total Subscriptions
  - Active Subscriptions
  - Closed Subscriptions
  - Revenue Received (actual collected payments)
  - Outstanding Invoices Amount & Count
  - Overdue Invoices Amount & Count
- Quick-filter drilldown action buttons linking directly to filtered views of subscriptions and invoices.

### G. Customer Portal & Self-Service
- Native Odoo Customer Portal routes (`/my/subscriptions` and `/my/subscriptions/<id>`).
- Subscription review, line details, billing schedule, and self-service cancellation requests.
- Customer record-level isolation ensuring privacy and security.

### H. Revenue Analytics & Reporting
- Real-time tracking of Monthly Recurring Revenue (MRR) and Annual Recurring Revenue (ARR).
- Interactive Pivot analysis and Bar Graph reports by subscription plan and status.

### I. Security & Access Permissions
- **User (Staff) Group**: Create, edit, and manage day-to-day subscriptions, quotations, and invoice generation.
- **Administrator Group**: Full access to plans, discounts, configurations, and financial audits.
- **Portal / Customer Record Rules**: Strict row-level isolation ensuring customers can only access their own subscription contracts.
- Complete `ir.model.access.csv` matrix for all models.

---

## 📁 Repository Structure

```text
├── .gitignore
├── README.md
└── subscription_management/
    ├── __init__.py
    ├── __manifest__.py
    ├── controllers/
    │   ├── __init__.py
    │   └── portal.py
    ├── data/
    │   ├── subscription_close_reason_data.xml
    │   ├── subscription_cron.xml
    │   ├── subscription_discount_data.xml
    │   ├── subscription_plan_data.xml
    │   └── subscription_sequence.xml
    ├── models/
    │   ├── __init__.py
    │   ├── account_move.py
    │   ├── product_template.py
    │   ├── subscription_close_reason.py
    │   ├── subscription_dashboard.py
    │   ├── subscription_discount.py
    │   ├── subscription_line.py
    │   ├── subscription_plan.py
    │   └── subscription_subscription.py
    ├── security/
    │   ├── ir.model.access.csv
    │   └── subscription_security.xml
    ├── static/
    │   └── description/
    │       ├── icon.png
    │       └── index.html
    └── views/
        ├── portal_subscription_templates.xml
        ├── subscription_close_reason_views.xml
        ├── subscription_dashboard_views.xml
        ├── subscription_discount_views.xml
        ├── subscription_menus.xml
        ├── subscription_plan_views.xml
        ├── subscription_product_views.xml
        └── subscription_views.xml
```

---

## 🛠️ Installation & Setup

1. **Clone or Copy Module**:
   Clone this repository directly into your Odoo custom addons directory:
   ```bash
   git clone https://github.com/nivedh77/SUBSCRIPTION-MANAGEMENT-SYSTEM.git
   ```

2. **Add to Addons Path**:
   Ensure the directory containing `subscription_management` is included in your `odoo.conf` file:
   ```ini
   addons_path = /path/to/odoo/addons,/path/to/SUBSCRIPTION-MANAGEMENT-SYSTEM
   ```

3. **Install the Module**:
   - Restart your Odoo server.
   - Activate **Developer Mode** in Odoo Settings.
   - Navigate to **Apps** -> Click **Update Apps List**.
   - Search for `Subscription Management System` and click **Activate**.

---

## 📦 Dependencies

- `base`
- `mail`
- `product`
- `account`
- `portal`

---

## 📜 License

Licensed under the **LGPL-3** license.
