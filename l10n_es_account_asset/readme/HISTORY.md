## 20.0.1.0.0

- El método de porcentaje fijo toma un trimestre como 3 meses, como
  account_asset_management, en vez de 4. En los perfiles y activos trimestrales cuyo
  porcentaje se introdujo por trimestre, el porcentaje anual guardado, que es el que
  amortiza, quedó mal (el 5 % trimestral se guardó como el 15 % anual, no como el 20 %),
  y la migración no lo puede corregir porque no sabe cuál de los dos se introdujo.
  Revise el porcentaje anual de los perfiles y activos trimestrales.
