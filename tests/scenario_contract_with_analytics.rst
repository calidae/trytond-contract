=================
Contract Scenario
=================

Imports::

    >>> import datetime
    >>> from decimal import Decimal
    >>> from proteus import Model, Wizard, Report
    >>> from trytond.tests.tools import activate_modules
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.account.tests.tools import create_fiscalyear, \
    ...     create_chart, get_accounts, create_tax
    >>> from trytond.modules.account_invoice.tests.tools import \
    ...     set_fiscalyear_invoice_sequences, create_payment_term
    >>> today = datetime.date(2020, 1, 1)

Install contract::

    >>> config = activate_modules(['analytic_invoice', 'contract'])

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Create fiscal year::

    >>> fiscalyear = set_fiscalyear_invoice_sequences(
    ...     create_fiscalyear(company, today))
    >>> fiscalyear.click('create_period')

Create chart of accounts::

    >>> _ = create_chart(company)
    >>> accounts = get_accounts(company)

Create analytic accounts::

    >>> AnalyticAccount = Model.get('analytic_account.account')
    >>> root = AnalyticAccount(type='root', name='Root')
    >>> root.save()
    >>> analytic_account = AnalyticAccount(root=root, parent=root,
    ...     name='Analytic')
    >>> analytic_account.save()
    >>> analytic_account2 = AnalyticAccount(root=root, parent=root,
    ...     name='Analytic 2')
    >>> analytic_account2.save()

Create analytic rules::

    >>> AnalyticRule = Model.get('analytic_account.rule')
    >>> rule1 = AnalyticRule(company=company, account=accounts['expense'])
    >>> entry, = rule1.analytic_accounts
    >>> entry.account = analytic_account
    >>> rule1.save()
    >>> rule2 = AnalyticRule(company=company, account=accounts['revenue'])
    >>> entry, = rule2.analytic_accounts
    >>> entry.account = analytic_account2
    >>> rule2.save()

Create tax::

    >>> tax = create_tax(Decimal('.10'))
    >>> tax.save()

Create payment term::

    >>> payment_term = create_payment_term()
    >>> payment_term.save()

Create party::

    >>> Party = Model.get('party.party')
    >>> customer = Party(name='Customer')
    >>> customer.customer_payment_term = payment_term
    >>> customer.save()

Configure contract::

    >>> ContractConfig = Model.get('contract.configuration')
    >>> Journal = Model.get('account.journal')

    >>> contract_config = ContractConfig(1)
    >>> contract_config.journal, = Journal.find([('type', '=', 'revenue')])
    >>> contract_config.save()

Create account category::

    >>> ProductCategory = Model.get('product.category')
    >>> account_category = ProductCategory(name="Account Category")
    >>> account_category.accounting = True
    >>> account_category.account_expense = accounts['expense']
    >>> account_category.account_revenue = accounts['revenue']
    >>> account_category.customer_taxes.append(tax)
    >>> account_category.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> unit.rounding =  0.01
    >>> unit.digits = 2
    >>> unit.save()

    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> template = ProductTemplate()
    >>> template.name = 'service'
    >>> template.default_uom = unit
    >>> template.type = 'service'
    >>> template.list_price = Decimal('40')
    >>> template.account_category = account_category
    >>> template.save()
    >>> product, = template.products

    >>> Service = Model.get('contract.service')
    >>> service1 = Service(name='service1', product=product)
    >>> service1.save()
    >>> service2 = Service(name='service2', product=product)
    >>> service2.save()
    >>> service3 = Service(name='service3', product=product)
    >>> service3.save()
    >>> service4 = Service(name='service4', product=product)
    >>> service4.save()

Create Monthly Contract with analytics::

    >>> Contract = Model.get('contract')
    >>> contract = Contract()
    >>> contract.party = customer
    >>> contract.freq = 'monthly'
    >>> contract.interval = 1
    >>> contract.start_period_date = datetime.date(2020, 1, 1)
    >>> contract.first_invoice_date = datetime.date(2020, 1, 1)
    >>> line1 = contract.lines.new(
    ...     service=service1,
    ...     unit_price=Decimal(100),
    ...     start_date=datetime.date(2020, 1, 1),
    ...     end_date=datetime.date(2020, 3, 1))
    >>> line1.analytic_accounts[0].account = analytic_account
    >>> contract.save()
    >>> contract.click('confirm')

Create consumptions::

    >>> Consumption = Model.get('contract.consumption')
    >>> create_consumptions = Wizard('contract.create_consumptions')
    >>> create_consumptions.form.date = datetime.date(2020, 1, 31)
    >>> create_consumptions.execute('create_consumptions')

Create invoice ::

    >>> Invoice = Model.get('account.invoice')
    >>> create_invoices = Wizard('contract.create_invoices')
    >>> create_invoices.form.date = datetime.date(2020, 2, 15)
    >>> create_invoices.execute('create_invoices')
    >>> invoice, = Invoice.find([])
    >>> line1.analytic_accounts[0].root == invoice.lines[0].analytic_accounts[0].root
    True
    >>> line1.analytic_accounts[0].account == invoice.lines[0].analytic_accounts[0].account
    True
