.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=========
INE codes
=========

Description
===========
This module contains the codes of the National Statistics Institute (INE) for Spanish cities.

The name of the city is in Spanish, in another language (if applicable) and reordered (if applicable).
These three variants of the city name are simplified (in capital letters and without diacritical characters)
to facilitate comparison.

If the city name is found, the city, province and state codes can be obtained.

Example
-------

.. code-block:: python

   city_name = self.partner_id.city
   city_name_simplified = unicodedata.normalize(‘NFKD’, city_name).upper()
   codes = self.env['res.ine.code'].search(
       ['|', '|', '|',
       ('city_name_simplified', '=', city_name_simplified),
       ('city_name_aka_simplified', '=', city_name_simplified),
       ('city_name_reordered_simplified', '=', city_name_simplified)])
   if codes:
       state_code = codes.ine_code_state
       province_code = codes.ine_code_province
       city_code = codes.ine_code_city

Credits
=======

* Moval Agroingeniería S.L.

Contributors
------------

* Samuel Fernández Verdú <sfernandez@moval.es>
* Alberto Hernández <ahernandez@moval.es>
* Eduardo Iniesta <einiesta@moval.es>
* Jesús Martínez <jmartinez@moval.es>
* Miguel Mora <mmora@moval.es>
* Miguel Ángel Rodríguez <marodriguez@moval.es>
* Juanu Sandoval <jsandoval@moval.es>
* Salvador Sánchez <ssanchez@moval.es>
* Jorge Vera <jvera@moval.es>
* Guillermo Amante <gamante@moval.es>

Maintainer
----------

.. image:: https://services.moval.es/static/images/logo_moval_small.png
   :target: http://moval.es
   :alt: Moval Agroingeniería

This module is maintained by Moval Agroingeniería.
