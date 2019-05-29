* El módulo recupera los datos enviados a la AEAT mediante peticiones unitarias o por meses (como una declaración AEAT)
* Los datos recibidos se procesan intentando asociarlos mediante su CSV (Código Seguro de Verificación) y si no encuentra el CSV, busca por número de factura/fecha/partner
* El módulo muestra aquellos registros que no han conseguido asociarse, así como aquellas facturas en Odoo que no tienen su correspondiente registro en los datos recibidos.
* En segundo lugar se exponen los registros que tienen diferencias entre Odoo y AEAT
* Por último se muestran por separado facturas 'No contrastadas' o 'Parcialmente contrastadas', es decir, las que la propia AEAT no haya podido cotejar entre el emisor de la factura y el receptor, siendo los dos obligados a declarar en el sistema SII.
