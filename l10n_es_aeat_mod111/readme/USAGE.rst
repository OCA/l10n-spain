Para crear un modelo, por ejemplo de un trimestre del año:

1. Ir a Facturación > Declaraciones AEAT > Modelo 111
2. Pulsar en el botón "Crear"
3. Seleccionar el ejercicio fiscal y el tipo de período, los periodos incluidos
   se calculan automáticamente
4. Seleccionar el tipo de declaración
5. Rellenar el teléfono y teléfono móvil, necesarios para la exportacion BOE
6. Guardar y pulsar en el botón "Calcular"
7. Rellenar (si es necesario) aquellos campos que Odoo no calcula automáticamente:

   * Rendimientos del trabajo: Dinerarios ([01], [02], [03]) y en especie ([04], [05], [06])
   * Premios por la participación en juegos, concursos, ...: Dinerarios ([13], [14], [15]) y en especie ([16], [17], [18])
   * Ganancias patrimoniales derivadas de los aprovechamientos forestales ...: Dinerarias ([19], [20], [21]) y en especie ([22], [23], [24])
   * Contraprestaciones por la cesión de derechos de imagen ...: Casillas [25], [26] y [27]
   * Resultados a ingresar anteriores: Casilla [29]

8. Cuando los valores sean los correctos, pulsar en el botón "Confirmar"
9. Podemos exportar en formato BOE para presentarlo telemáticamente en el portal
   de la AEAT

NOTA: En el caso en que tengamos el addon 'l10n_es_aeat_mod216' deberemos
indicar los proveedores que son residentes (éste es el valor por defecto),
en la ficha de la empresa: Contabilidad > Proveedores > Proveedores, pestaña de
Contabilidad. El campo "Es no residente" no debe estar marcado para que
las retenciones realizadas a éste proveedor se incluyan en el modelo 111.
