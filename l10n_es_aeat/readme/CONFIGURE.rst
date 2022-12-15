Todos aquellos modelos que se especifiquen en los módulos adicionales y
hereden el AEAT base, deberán definir una variable interna que se llame
'_aeat_number' asignándole como valor, el número del modelo (130, 340, 347...).

Para poder utilizar el motor genérico de cálculo de casillas por impuestos
(como el 303), hay que heredar del modelo "l10n.es.aeat.report.tax.mapping" en
lugar de "l10n.es.aeat.report". Para la vista, hay que añadir el campo a mano,
ya que la herencia de vistas no permite una doble herencia de AbstractModel,
pero lo que es la vista tree ya está definida.

Para activar la creación del asiento de regularización en un modelo, hay que
poner en el modelo correspondiente el campo allow_posting a True, y establecer
en la configuración de impuestos los conceptos que se regularizarán con el
flag "to_regularize". Esto sólo es posible sobre los modelos que utilicen
el cálculo de casillas por códigos de impuestos.

ADVERTENCIA: Debido a que se utiliza una sola tabla para almacenar las líneas
de los impuestos de todos los modelos, hay una limitación en el ORM de Odoo
cuando se coloca el campo one2many de dichas líneas (tax_line_ids) como
dependencia en la definición del cálculo de un campo (entrada con
@api.depends), que recalcula los campos calculados de todos los modelos con el
mismo ID que el del registro en curso, lo que puede ser un problema en entornos
multi-compañía. Una solución a ello (aunque no evita el recálculo), es poner en
esos campos calculados `compute_sudo=True`.

Se ha creado el campo base computado error_count en el modelo l10n.es.aeat.report,
cuyo valor dependerá de sus herencias, que heredarán la función _compute_error_count
para indicar cuantas líneas con errores hay en el informe. Si el valor es 0, no
se mostrará ningún aviso; si el valor es mayor a 0, se mostrará un aviso en la
parte superior de la vista formulario del informe.
