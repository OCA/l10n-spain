El parámetro de sistema ``l10n_es_verifactu_pos_oca.max_chaining_attempts``
(por defecto: 10) limita cuántas veces reintenta la acción planificada un
mismo pedido. Los fallos que se resuelven solos, como una colisión del bloqueo
de encadenamiento, no cuentan; un pedido que alcanza el límite deja de entrar
en el barrido y necesita el botón manual.
