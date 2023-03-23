WARNING: This module conflicts with the Intrastat modules from the official
enterprise addons. If you have already installed these modules, you should
uninstall them before installing this module.

You need to add HS product codes for your company through the installation
wizard. It's automatically launched if installing the module from the UI.

If any other installation method is used, you can go to
*Settings > Technical > Actions > Configuration Wizards* on developer mode,
and launch there the wizard called "Import Spanish Product HS Codes"

The included codes are for 2023. Please check possible updates for this codes in:

https://www.agenciatributaria.es/AEAT.internet/Inicio/La_Agencia_Tributaria/Memorias_y_estadisticas_tributarias/Estadisticas/_Comercio_exterior_/Documentacion/Tablas_de_codigos/Tablas_de_codigos.shtml

This wizard also sets a sane default Intrastat transaction type for each kind
of invoice at company level, but it can be changed later.
