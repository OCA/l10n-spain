Para configurar el transportista:

#. Vaya a *Inventario > Configuración > Entrega > Método de envío* y cree uno
   nuevo.
#. Escoja *MRW* Como proveedor.
#. Configure los datos de servicio que tiene contratados y el producto de
   envío que desea utilizar.

Si no tiene credenciales todavía, puede dejar los campos vacíos y dejar el
método de envío en "Entorno de prueba". Se utilizará el usuario de pruebas de
MRW.

Si MRW cambiase en un futuro el usuario de prueba, puede cambiarlo en los
*Parámetros del sistema* en las claves:

- delivery_mrw.user_demo_franquicia_code
- delivery_mrw.user_demo_client_code
- delivery_mrw.user_demo_department_code
- delivery_mrw.user_demo_username
- delivery_mrw.user_demo_password
