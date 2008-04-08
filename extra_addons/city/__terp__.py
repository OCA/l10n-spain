#!/usr/bin/env python
# -*- coding: utf-8 -*-
{
	"name" : "City",
	"version" : "0.1",
	"author" : "Pablo Rocandio",
	"description": """
		This modules creates tables for storing cities
			""",
	"depends" : ["base"],
	"init_xml" : [
		"data/data_provincias_es.xml",
	    "data/data_countries.xml",
	    "city_wizard.xml",		
		],
	"update_xml" : [
	    'city_view.xml',
	    ],
	"active": False,
	"installable": True
}




