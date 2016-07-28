Feature: Full Contract funcionality

    Background: Configure set of services

        Given a invoice configuration database
        And Basic Contract configuration
        And set of services:
            | name      |
            | service1 |
            | service2 |
            | service3 |
            | service4 |

    Scenario: Full Scenario with Monthly Contract
        Given a contract Monthly that starts on 2015-01-01, first invoice on 2015-01-01, monthly and interval of 1
        And A set of lines for contracts:
            | service  | decimal(unit_price)   | date(start_date) | date(end_date) |
            | service1 | 100                 | 2015-01-01       | 2015-03-01     |
            | service2 | 200                 | 2015-01-01       | 2015-02-15     |
            | service3 | 300                 | 2015-02-15       | 2015-02-28     |
            | service4 | 400                 | 2015-02-15       |                |

        When confirm contract
        Then contract state is confirmed
        When I Create Consumptions for Date 2015-01-31
        Then I get 2 consumptions Lines
        When I Create Consumptions for Date 2015-02-28
        Then I get 6 consumptions lines
        When I Create Consumptions for Date 2015-04-01
        Then I get 9 consumptions lines
        And I get a set of consumptions not invoiced:
            | service  | date(init_period_date) | date(end_period_date) | date(start_date) | date(end_date)   | date(invoice_date) |
            | service1 | 2015-01-01             | 2015-01-31            | 2015-01-01       | 2015-01-31       |  2015-01-01  |
            | service2 | 2015-01-01             | 2015-01-31            | 2015-01-01       | 2015-01-31       |  2015-01-01  |
            | service1 | 2015-02-01             | 2015-02-28            | 2015-02-01       | 2015-02-28       |  2015-02-01  |
            | service2 | 2015-02-01             | 2015-02-28            | 2015-02-01       | 2015-02-15       |  2015-02-01  |
            | service3 | 2015-02-01             | 2015-02-28            | 2015-02-15       | 2015-02-28       |  2015-02-01  |
            | service4 | 2015-02-01             | 2015-02-28            | 2015-02-15       | 2015-02-28       |  2015-02-01  |
            | service1  | 2015-03-01            | 2015-03-31            | 2015-03-01       | 2015-03-01       |  2015-03-01  |
            | service4  | 2015-03-01            | 2015-03-31            | 2015-03-01       | 2015-03-31       |  2015-03-01  |
            | service4  | 2015-04-01            | 2015-04-30            | 2015-04-01       | 2015-04-30       |  2015-04-01  |

        When I Invoice on Date 2015-02-15
        Then I get 2 invoices
        When I Invoice on Date 2015-04-01
        Then I get 4 invoices
        And Invoice line Amounts for consumptions:
            |  service  | date(invoice_date) | decimal(amount) |
            |  service1 | 2015-01-01         |  100.00         |
            |  service1 | 2015-02-01         |  100.00         |
            |  service1 | 2015-03-01         |  3.23           |
            |  service2 | 2015-01-01         |  200.00         |
            |  service2 | 2015-02-01         |  107.14         |
            |  service3 | 2015-02-01         |  150.00         |
            |  service4 | 2015-02-01         |  200.00         |
            |  service4 | 2015-03-01         |  400.00         |
            |  service4 | 2015-04-01         |  400.00         |






