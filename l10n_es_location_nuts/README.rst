NUTS Regions for Spain
======================

This module allows to import NUTS locations for Spain.

* Spanish Provinces (NUTS level 4) as Partner State
* Spanish Autonomous communities (NUTS level 3) as Partner Substate
* Spanish Regions (NUTS level 2) as Partner Region

After installation, you must click at import wizard to populate NUTS items
in Odoo database in:
Sales > Configuration > Address Book > Import NUTS 2013

This wizard will download from Europe RAMON service the metadata to
build NUTS in Odoo. This localization addon will inherit this wizard and
relate each Spanish NUTS item with Spanish state.

Only Administrator can manage NUTS list (it is not neccesary because
it is an European convention) but any registered user can read them,
in order to allow to assign them to partner object.

Credits
=======

Contributors
------------
* Antonio Espinosa <antonioea@antiun.com>
