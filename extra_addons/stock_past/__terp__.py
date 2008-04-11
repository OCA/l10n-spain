{
	"name" : "Update to stock module to allow calculations of past stocks",
	"version" : "1.0",
	"depends" : ["stock", "product", "base"],
	"author" : "ACYSOS SL",
	"description": """ Update to stock module. The stock calculation functions now 
        have a new date parameter that can be used to limit the stock reported. Inventories 
        now use the inventory date and update the stock at that date.
	""",
	"website" : "http://acysos.com",
	"category" : "Extensions",
	"init_xml" : [
		
	],
	"demo_xml" : [
	],
	"update_xml" : [
		"stock_wizard.xml",
		"stock_view.xml",
	],
	"active": False,
	"installable": True
}
