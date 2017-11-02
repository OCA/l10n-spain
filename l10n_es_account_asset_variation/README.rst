.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=======================
Account Asset Variation
=======================

* New option in opened assets to load a variation in the asset, only if the
  method time in the asset is percentage.
* When executing the button, a wizard will be launched, where you have to
  configure the variation in the asset, the percentage to depreciate between
  two dates.
* When the wizard is executed, all the depreciation lines in the asset that are
  not contabilized, will be removed, and the new lines will be created
  depreciating the asset method percentage as default and the wizard percentage
  when the date of a depreciation line is between the two dates defined in the 
  wizard.


Credits
=======

Contributors
------------
* Ainara Galdona <ainaragaldona@avanzosc.es>
* Ana Juaristi <anajuaristi@avanzosc.es>
