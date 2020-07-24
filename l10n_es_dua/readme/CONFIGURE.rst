Este addon añade los impuestos y posiciones fiscales a las siguientes plantillas:

* PGCE entidades sin ánimo de lucro 2008
* PGCE PYMEs 2008
* PGCE completo 2008

Para aplicar los cambios al plan contable que tengamos configurado en nuestra
compañía es posible que sea necesario instalar el addon
'OCA/account-financial-tools/account_chart_update' y actualizar:

* Impuestos
* Posiciones fiscales

Una vez actualizado el plan contable (Impuestos y Posiciones fiscales) es
necesario asignar los impuestos a los productos DUA que crea este addon para
facilitar la contabilidad de las facturas de la empresa de tránsito:

1. Ir a Compras > Productos > Productos
2. Quitar el filtro por defecto y buscar "DUA"
3. Asignar los siguientes impuestos en el campo "Impuestos proveedor"
    * DUA Compensación: "DUA Exento"
    * DUA Valoración IVA 10%: "IVA 10% Importaciones bienes corrientes"
    * DUA Valoración IVA 21%: "IVA 21% Importaciones bienes corrientes"
    * DUA Valoración IVA 4%: "IVA 4% Importaciones bienes corrientes"
