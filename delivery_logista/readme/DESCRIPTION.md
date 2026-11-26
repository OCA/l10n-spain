This module integrates Odoo's `delivery` framework (along with `delivery_package_number`, `delivery_state`, and `stock_picking_volume`) with **Logista Parcel REST API v5**:

- **Expedition Registration (`POST /EnlaceB2B/app/integrations/shipment/v1`)**:
  - Supports Test (`qua-clientes.integra2.es`) and Production (`clientes.integra2.es`) environments with header token authentication.
  - Full support for all 9 Logista Parcel services (`AMBIPAQ`, `URGEPAQ`, `FRIOFARMA`, `FRIOPAQ`, `URGEFRIO`, `FARMAPLUS`, `AEREO FRIO`, `FARMA < 25`, `I2GOURMET`), Spain (`ES`), Portugal (`PT`), and Andorra (`AD` -> `AN`).
  - Automatic handling of unit parcels (`Packages`), pallets (`ControlPackages`), and mixed pallet + loose parcel shipments (`MixShipment`, `MixPalets`, `MixPackages`), volume (`m³`), insurance (`InsuranceValue`), cash on delivery (`CashOnDelivery`), SMS/Email notifications, arranged delivery dates, delivery note actions, tight flow, and `ePackingList`.
- **Plaza & Delivery Zone Resolution (`wsRepartoProductoPorPlazas`)**:
  - Automatic destination delegation (`delegacion`) and delivery zone (`zonaReparto`) resolution for labels.
- **Official 34-Digit Code 128 Labels (PDF & Zebra ZPL)**:
  - Generates 100x150mm **PDF** (QWeb) and **ZPL** thermal labels for both parcels (`Bto.`) and pallets (`Pal.`), including the 34-character Code 128C/B barcode per Logista Parcel Labelling Specification v4.
