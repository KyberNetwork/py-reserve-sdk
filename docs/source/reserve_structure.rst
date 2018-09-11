Reserve Structure
=================

Contracts
---------

* :class:`Reserve Contract <reserve_sdk.ReserveContract>`
* :class:`Pricing Contract <reserve_sdk.ConversionRatesContract>`
* :class:`Sanity Contract <reserve_sdk.SanityRatesContract>`

Role
----

Each contract in reserve has three permission groups:

1. Admin

The admin account is unique (usually cold wallet) and handles infrequent, \
manual operations like listing new tokens in the exchange. All sensitive \
operations (e.g. fund related) are limited to the Admin address.

2. Operator

The operator account is a hot wallet and is used for frequent updates like \
setting reserve rates and withdrawing funds from the reserve to certain \
destinations (e.g. when selling excess tokens in the open market).

3. Alerter

The alerter account is also a hot wallet and is used to alert the admin of \
inconsistencies in the system (e.g., strange conversion rates). In such cases, \
the reserve operation is halted and can be resumed only by the admin account.