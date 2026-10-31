# 🔄 Subscription Management System for Odoo 19 Community

> Built for the **Odoo Makeathon / Hackathon 2026** by Team STRANGERS [Nivedh M](https://github.com/nivedh77) and [RASHMI KRISHNA P](https://github.com/rashmikrishnap)

A robust, enterprise-ready Subscription Management module designed natively for **Odoo 19 Community Edition**. It provides automated recurring billing, contract lifecycle management, flexible pricing plans, and customer self-service capabilities.

---

## 🚀 Key Features

- **Flexible Subscription Plans**:
  - Support for multiple billing frequencies: Daily, Weekly, Monthly, and Yearly.
  - Trial period support with auto-conversion settings.
  - Configurable auto-close conditions for unpaid invoices.
  - Multi-currency support and standard pricing structures.

- **Role-Based Security & Permissions**:
  - **Subscription Administrator**: Full configuration, plan creation, and financial audit controls.
  - **Subscription User / Staff**: Contract creation, quotation generation, and customer management.
  - **Portal / Customer**: View active subscriptions, download invoices, and request changes.

- **Automated Lifecycle Management**:
  - Contract states: Draft Quotation → Active → In Review → Paused → Closed / Cancelled.
  - Pause and resume workflows with prorated billing adjustments.
  - Automated recurring invoice generation via Odoo cron jobs.

- **Finance & Invoicing Integration**:
  - Tight integration with Odoo `account` (Invoicing).
  - Automated tax calculation and journal entry creation.
  - Fixed and percentage-based promotional discount handling.

- **Revenue Analytics & Reporting**:
  - Real-time tracking of Monthly Recurring Revenue (MRR) and Annual Recurring Revenue (ARR).
  - Churn rate, active subscriber metrics, and renewal success ratios.

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
    │   ├── subscription_plan_data.xml
    │   └── subscription_sequence.xml
    ├── models/
    │   ├── __init__.py
    │   ├── account_move.py
    │   ├── product_template.py
    │   ├── subscription_close_reason.py
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
- `product`
- `account`
- `portal`

---

## 📜 License

Licensed under the **LGPL-3** license.
