Al instalar el módulo se crean las subclases CNAE 2025, sin necesidad de
conexión. Para importar los nombres de las categorías NACE en todos los idiomas
activos, hay que ir a *Contactos > Configuración > Importar industrias NACE* y
lanzar el asistente.

## Migrar desde CNAE 2009

Si ya tenía las categorías CNAE 2009, actualice `l10n_eu_nace` (p. ej.
`-u l10n_eu_nace`), que actualiza también este módulo. Si se actualiza solo este
módulo, la actualización falla y no se aplica, porque `l10n_eu_nace` no ha
creado aún los campos que necesita. Además de migrar los sectores NACE Rev. 2 a NACE Rev. 2.1 (ver `l10n_eu_nace`),
la actualización:

1.  Reutiliza las subclases CNAE 2009 que mantienen código y actividad en
    CNAE 2025 (p. ej. 10.21) y actualiza su nombre.
2.  Archiva el resto y pasa los registros que las usan a su equivalente en
    CNAE 2025, según la tabla de correspondencias del INE. Cuando la tabla da
    varias opciones, se ha elegido la que mejor encaja con la actividad:

    | CNAE 2009 | CNAE 2025 |
    |---|---|
    | 35.15 Energía hidroeléctrica | 35.12 Electricidad de origen renovable |
    | 35.16 Energía térmica convencional | 35.11 Electricidad de origen no renovable |
    | 35.17 Energía nuclear | 35.11 Electricidad de origen no renovable |
    | 35.18 Energía eólica | 35.12 Electricidad de origen renovable |
    | 35.19 Energía de otros tipos | 35.12 Electricidad de origen renovable |
    | 41.21 Edificios residenciales | 41.01 Edificios residenciales |
    | 41.22 Edificios no residenciales | 41.02 Edificios no residenciales |
    | 85.43 Educación universitaria | 85.41 Educación universitaria |
    | 85.44 Educación terciaria no universitaria | 85.42 Educación terciaria no universitaria |
    | 91.05 Bibliotecas | 91.11 Bibliotecas |
    | 91.06 Archivos | 91.12 Archivos |

    Ojo: en NACE Rev. 2.1, 35.15 es *Comercio de electricidad* y 35.16
    *Almacenamiento de electricidad*, por eso no se reutilizan.
