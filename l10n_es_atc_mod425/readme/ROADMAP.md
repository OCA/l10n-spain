## Limitación en entorno Runboat

Este módulo no podrá generar archivos `.dec` o `.pdf` en entornos ejecutados desde Runboat, debido a que la instalación de la librería `ttf-mscorefonts-installer` requiere la aceptación de una licencia, lo cual no es posible automatizar en dicho entorno.

Se puede consultar el informe del problema en el siguiente enlace:
https://github.com/OCA/oca-ci/issues/94

Para verificar la funcionalidad completa del módulo, hay que realizar las pruebas localmente siguiendo las instrucciones indicadas en el apartado de instalación.