En caso de la activación de secuencias por dispositivo:

**Selección de dispositivo**

Al entrar en la sesión se establecerá el dispositivo a utilizar.

* En caso de que haya conexión, el dispositivo es bloqueado y no puede ser
  seleccionado al entrar a la sesión desde otro dispositivo.

* En caso de que no haya conexión, al intentar realizar el primer pedido
  el dispositivo será expulsado de la sesión. Cuando se vuelva a conectar y
  entre en la sesión, el pedido estará pendiente. Se podrá acabar de tramitar.

**Transcurso de sesión**

Se irán haciendo pedidos, y se establecerá la secuencia indicada en la
definición del dispositivo.

En caso de pérdida de conexión: Cuando se recupere la conexión se incluirán los
pedidos en la sesión.

En caso de pérdida de conexión + incidente en dispositivo (pérdida de batería,
cierre de ventana o navegador): El dispositivo se queda bloqueado. Tiene que
ser desbloqueado manualmente para volver a usarse. En caso de entrar en la misma
sesión, los pedidos pendientes se incluirán en la misma sesión. En caso de ser
una sesión diferente, serán incluidos en una sesión de rescate siguiendo el
estándar de Odoo.
