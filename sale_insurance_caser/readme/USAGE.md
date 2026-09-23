## Tarification (Get Insurance Prices)

1. Go to *Settings > Sales > Caser Insurance*
2. Click on **Configure Price Ranges** button
3. Select one or more price ranges and click **Get Prices from Caser** button (or use *Action > Get Tarification Prices*)
4. Insurance products will be created/updated automatically with prices from Caser API

## Sale Order Flow

### Step 1: Create Sale Order

1. Create a sale order with products that support insurance
2. In each order line, set **Quantity to Insure** field
3. Insurance lines are automatically created based on price ranges

### Step 2: Validate Delivery

1. Confirm the sale order
2. In the delivery order, assign serial numbers to products
3. Click **Validate**
4. Insurance requests are sent to Caser asynchronously via queue jobs

### Step 3: Review Insurance Status

After validation, check the insurance lines in the sale order:

- **Is Caser Insurance**: Identifies insurance product lines
- **Insured Lot**: The serial number that was insured
- **Policy Number**: Caser policy number (if successful)
- **Insurance Price**: Final price charged by Caser
- **Error Message**: Any error from Caser API (if failed)

## Viewing Request/Response Logs

To inspect the XML communication with Caser:

1. Open the sale order
2. Click on an insurance line (where **Is Caser Insurance** = True)
3. Go to the **Caser** tab to view:
   - **Request XML**: Complete SOAP request sent to Caser
   - **Response XML**: Complete response received from Caser
