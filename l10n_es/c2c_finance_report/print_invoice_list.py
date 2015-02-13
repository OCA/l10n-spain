#!/usr/bin/env python2.3
#
#  print_invoice_list.py
#  PEG
#
#  Created by Nicolas Bessi on 13.10.08.
#  Copyright (c) 2008 CamptoCamp. All rights reserved.
#

import time
from mx.DateTime import *
from report import report_sxw
import xml
import rml_parse
import pooler

class print_invoice_list(rml_parse.rml_parse):
	""" Report that print invoices grouped by currency and type """
	_name = 'report.account.print_invoice_list'
	
	
	
	
	def __init__(self, cr, uid, name, context):
		super(print_invoice_list, self).__init__(cr, uid, name, context)
		#contain tuples of in invoices : (curreny, [browse records], currency_total)
		self.in_invoices = []
		#contain tuples of in refunds : (curreny, [browse records], currency_total)
		self.in_refunds = []
		#contain tuples of out invoices : (curreny, [browse records], currency_total)
		self.out_invoices = []
		#contain tuples of out refunds : (curreny, [browse records], currency_total)
		self.out_refunds = []
		self.localcontext.update( {
			'time':time,
			'in_invoices':self.in_invoices,
			'in_refunds':self.in_refunds,
			'out_invoices':self.out_invoices,
			'out_refunds':self.out_refunds,
					})
	
	def preprocess(self, objects, data, ids):
		""" we do the grouping and proceesing of invoices"""
		if not ids :
			return super(print_invoice_list, self).preprocess(objects, data, new_ids)
		
		if not isinstance(ids, list) :
			ids = [ids]
		# we create temp list that will be used for store invoices by type
		ininv = []
		outinv = []
		inref = []
		outref = []
		#we get the invoices and sort them by types
		invoices = self.pool.get('account.invoice').browse(self.cr, self.uid, ids)
		for inv in invoices :
			if inv.type == ('in_invoice'):
				ininv.append(inv)
			if inv.type == ('in_refund'):
				inref.append(inv)
			if inv.type == ('out_invoice'):
				outinv.append(inv)
			if inv.type == ('out_refund'):
				outref.append(inv)
		#e process the invoice and attribute them to the property
		self.filter_invoices(ininv, self.in_invoices)
		self.filter_invoices(outinv, self.out_invoices)
		self.filter_invoices(inref, self.out_refunds)
		self.filter_invoices(outref, self.out_refunds)
		super(print_invoice_list, self).preprocess(objects, data, ids)
		
	

	def filter_invoices(self, list, dest) :
		if not list :
			return 
		tmp = {}
		#We sort the invoice by currency in a tmp dict
		#{'currency':[browse, records]}
		for inv in list:
			currency = inv.currency_id.name
			if tmp.has_key(currency) :
				tmp[currency].append(inv)
			else :
				tmp[currency] = [inv]
		#we compute the total by currency		
		total = 0
		for curr in tmp:
			for tmpinv in tmp[curr]:
				total += tmpinv.amount_total
			#we append the tupe to the property
			dest.append((curr, tmp[curr], total))
			total = 0
		del tmp
			
report_sxw.report_sxw('report.account.print_invoice_list', 'account.invoice', 'addons/c2c_finance_report/list_invoice.rml', parser=print_invoice_list, header=False)
