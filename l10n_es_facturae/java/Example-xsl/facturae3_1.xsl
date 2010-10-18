<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0" xmlns:m3="http://www.facturae.es/Facturae/2007/v3.1/Facturae" xmlns:ds="http://www.w3.org/2000/09/xmldsig#" xmlns:tns="http://schemas.xmlsoap.org/soap/envelope/">
	<xsl:output method="html" indent="yes"/>
	<xsl:decimal-format grouping-separator="." decimal-separator=","/>
	<xsl:template match="/">
				<xsl:apply-templates select="//m3:Facturae"/>
	</xsl:template>
	<!-- Versión 3.0 -->
	<xsl:template match="m3:Facturae">
		<html>
						<head>
				<title>Resumen de factura</title>
				<link rel="stylesheet" href="factura.css" type="text/css"/>
				<script>
					function masDatos()
					{
						var lote 	= '<xsl:value-of select="FileHeader/Batch/BatchIdentifier"/>';
						var factura = '<xsl:value-of select="Invoices/Invoice/InvoiceHeader/InvoiceNumber"/>';

						var url = "";
						if(document.location.host.toUpperCase().indexOf("CICS03D") > -1)
						{
							// Desarrollo
							if(document.location.host.toUpperCase().indexOf("9443") == -1)
							{
								// Internet
								url = "https://" + document.location.host + ":9443/ES13/S/WIADWIGEIZ26";	
							}
							else
							{
								// Intranet
								url = "/ES13/S/WIADWIGEIZ26";	
							}
						}
						else
						{
							// Produccion
							url = "/ES13/S/WIADWIGEIZ26";	
						}

						var w = open('','','width=600,height=400,resizable=yes,scrollbars=yes');
					   w.document.write('<html>');
					   w.document.write('<body>');
					   w.document.write('<form name="frm_mas" action="' + url + '" method="post">');
					   w.document.write('<input type="hidden" name="NROLOTE" value="" />');
					   w.document.write('<input type="hidden" name="SECLOTE" value="0" />');
					   w.document.write('<input type="hidden" name="NROFAC" value="" />');
					   w.document.write('<input type="hidden" name="SERIEFAC" value="0" />');
					   w.document.write('</form>');
					   w.document.write('</body>');
					   w.document.write('</html>');

						w.document.frm_mas.NROLOTE.value = lote;
						w.document.frm_mas.NROFAC.value = factura;
						w.document.frm_mas.submit();
					}
				</script>
			</head>
			<body>
				<div id="principal">
				<center>
					<table border="0" width="90%" cellpadding="0" cellspacing="0">
						<tr>
							<td width="100%">
								<table border="0" cellpadding="0" cellspacing="0" width="100%">
									<tr>
										<td align="center" colspan="2">
											<font class="titulo1">RESUMEN DE FACTURA</font>
										</td>
										<td align="right">
											<xsl:apply-templates select="Parties/SellerParty"/>
										</td>
									</tr>
									<tr>
										<td colspan="3"><font color="FFFFFF">_</font></td>
									</tr>
									<tr>
										<td width="60%">
											<table border="1" cellpadding="0" cellspacing="0" width="100%">
												<tr>
													<td>
														<table border="0" cellpadding="0" cellspacing="0" width="100%">
															<tr>
																<td align="center" width="33%">
																	<font class="titulopeque">NUMERO</font>
																	<br/><xsl:value-of select="Invoices/Invoice/InvoiceHeader/InvoiceNumber"/></td>
																<td align="center" width="34%">
																	<font class="titulopeque">FECHA EXPED.</font>
																	<br/>
																		<xsl:value-of select="substring(Invoices/Invoice/InvoiceIssueData/IssueDate,9,2)"/>-<xsl:value-of select="substring(Invoices/Invoice/InvoiceIssueData/IssueDate,6,2)"/>-<xsl:value-of select="substring(Invoices/Invoice/InvoiceIssueData/IssueDate,1,4)"/>
																	</td>
																<td align="center" width="33%">
																	<font class="titulopeque">Nº DE SERIE</font>
																	<br/><xsl:value-of select="Invoices/Invoice/InvoiceHeader/InvoiceSeriesCode"/></td>
															</tr>
														</table>
													</td>
												</tr>
												<tr>
													<td>
														<table border="0" cellpadding="0" cellspacing="0" width="100%">
															<tr>
																<td align="center" width="33%">
																	<font class="titulopeque">N.I.F. EMISOR</font>
																	<br/><xsl:value-of select="Parties/SellerParty/TaxIdentification/TaxIdentificationNumber"/></td>
																<td align="center" width="33%">
																	<font class="titulopeque">CONTRATO</font>
																	<br/><xsl:value-of select="Invoices/Invoice/Items/InvoiceLine/ReceiverContractReference"/></td>
																<td align="center" width="34%">
																	<font class="titulopeque">FORMA DE PAGO</font>
																	<br/><xsl:value-of select="Invoices/Invoice/PaymentDetails/Installment/PaymentMeans"/></td>
															</tr>
														</table>
													</td>
												</tr>
												<tr>
													<td>
														<table border="0" cellpadding="0" cellspacing="0" width="100%">
															<tr>
																<td align="center" width="50%">
																	<font class="titulopeque">TIPO DOCUMENTO</font><br/>
																	<xsl:choose>
																		<xsl:when test='Invoices/Invoice/InvoiceHeader/InvoiceClass="OO"' >
																			ORIGINAL
																		</xsl:when>
																		<xsl:when test='Invoices/Invoice/InvoiceHeader/InvoiceClass="OR"' >
																			RECTIFICATIVA
																		</xsl:when>
																		<xsl:when test='Invoices/Invoice/InvoiceHeader/InvoiceClass="CO"' >
																			COPIA
																		</xsl:when>
																		<xsl:when test='Invoices/Invoice/InvoiceHeader/InvoiceClass="CR"' >
																			COPIA RECTIFICATIVA
																		</xsl:when>
																		<xsl:when test='Invoices/Invoice/InvoiceHeader/InvoiceClass="CC"' >
																			COPIA RECAPITULACION
																		</xsl:when>
																		<xsl:otherwise>
																			<xsl:value-of select="Invoices/Invoice/InvoiceHeader/InvoiceClass"/>
																		</xsl:otherwise>
																	</xsl:choose></td>
																<td align="center" width="50%">
																	<font class="titulopeque">Nº FACTURA RECTIF.</font>
																	<br/><xsl:value-of select="Invoices/Invoice/InvoiceHeader/Corrective/InvoiceNumber"/></td>
															</tr>
														</table>
													</td>
												</tr>
											</table>
										</td>
										<td width="3%"><font color="FFFFFF">_</font></td>
										<td width="37%" valign="center">
											<xsl:apply-templates select="Parties/BuyerParty"/>
										</td>
									</tr>
								</table>
							</td>
						</tr>
						<tr>
							<td><font color="FFFFFF">_</font></td>
						</tr>
						<tr>
							<td>
								<hr/>
							</td>
						</tr>
						<tr>
							<td width="100%">
								<table border="0" cellpadding="0" cellspacing="0" width="100%">
									<tr>
										<td colspan="2">
											<font class="titulo2">DIRECCIÓN DE EMPLAZAMIENTO</font>
										</td>
									</tr>
									<tr>
										<td colspan="2"><font color="FFFFFF">_</font></td>
									</tr>
									<tr>
										<td width="30%">
											<font class="titulopeque">DOMICILIO SOCIAL:</font>
										</td>
										<td width="70%">
											<xsl:if test="Parties/SellerParty/LegalEntity!=''">
												<xsl:value-of select="Parties/SellerParty/LegalEntity/AddressInSpain/Address"/><br/>
											</xsl:if>
											<xsl:if test="Parties/SellerParty/Individual!=''">
												<xsl:value-of select="Parties/SellerParty/Individual/AddressInSpain/Address"/><br/>
											</xsl:if>
										</td>
									</tr>
									<tr>
										<td>
											<font class="titulopeque">TRANSFERIR A BANCO:</font>
										</td>
										<td>
											<xsl:value-of select="Invoices/Invoice/PaymentDetails/Installment/AccountToBeCredited/IBAN"/><font color="FFFFFF">___</font>
											<xsl:value-of select="Invoices/Invoice/PaymentDetails/Installment/AccountToBeCredited/BankCode"/>
										</td>
									</tr>
									<tr>
										<td valign="top">
											<font class="titulopeque">OBSERVACIONES:</font>
										</td>
										<td>
											<xsl:for-each select="Invoices/Invoice/AdditionalData/InvoiceAdditionalInformation">
												<xsl:apply-templates/><br/>
											</xsl:for-each>
										</td>
									</tr>
								</table>
							</td>
						</tr>
						<tr>
							<td><font color="FFFFFF">_</font></td>
						</tr>
						<tr>
							<td>
								<hr/>
							</td>
						</tr>
						<tr>
							<td>
								<font class="titulo2">DETALLE FACTURA</font>
							</td>
						</tr>
						<tr>
							<td><font color="FFFFFF">_</font></td>
						</tr>
						<tr>
							<td width="100%">
								<table border="1" cellpadding="0" cellspacing="0" width="100%">
									<tr>
										<td width="48%" align="center">
											<font class="titulopeque">DESCRIPCIÓN</font>
										</td>
										<td width="12%" align="center">
											<font class="titulopeque">FECHA OPER.</font>
										</td>
										<td width="10%" align="center">
											<font class="titulopeque">CANTIDAD</font>
										</td>
										<td width="15%" align="center">
											<font class="titulopeque">IMP. UNITARIO</font>
										</td>
										<td width="15%" align="center">
											<font class="titulopeque">TOTAL</font>
										</td>
									</tr>
									<tr>
										<td width="48%" valign="top">
											<table border="0" cellpadding="0" cellspacing="0" width="100%">
												<tr>
													<td>
														<table border="0" cellpadding="0" cellspacing="0" width="100%">
															<xsl:for-each select="Invoices/Invoice/Items/InvoiceLine">
																<tr>
																	<td>
																		<xsl:apply-templates select="ItemDescription"/>
																	</td>
																</tr>
															</xsl:for-each>
														</table>
													</td>
												</tr>
											</table>
										</td>
										<td width="12%" valign="top">
											<table border="0" cellpadding="0" cellspacing="0" width="100%">
												<tr>
													<td>
														<table border="0" cellpadding="0" cellspacing="0" width="100%">
															<xsl:for-each select="Invoices/Invoice/Items/InvoiceLine">
																<tr>
																	<td align="center">
																		<xsl:value-of select="substring(TransactionDate,9,2)"/>-<xsl:value-of select="substring(TransactionDate,6,2)"/>-<xsl:value-of select="substring(TransactionDate,1,4)"/>
																	</td>
																</tr>
															</xsl:for-each>
														</table>
													</td>
												</tr>
											</table>
										</td>
										<td width="10%" valign="top">
											<table border="0" cellpadding="0" cellspacing="0" width="100%">
												<tr>
													<td>
														<table border="0" cellpadding="0" cellspacing="0" width="100%">
															<xsl:for-each select="Invoices/Invoice/Items/InvoiceLine">
																<tr>
																	<td align="right">
																		<xsl:value-of select="format-number(Quantity,'#.##0')"/>
																	</td>
																</tr>
															</xsl:for-each>
														</table>
													</td>
												</tr>
											</table>
										</td>
										<td width="15%" valign="top">
											<table border="0" cellpadding="0" cellspacing="0" width="100%">
												<tr>
													<td>
														<table border="0" cellpadding="0" cellspacing="0" width="100%">
															<xsl:for-each select="Invoices/Invoice/Items/InvoiceLine">
																<tr>
																	<td align="right">
																		<xsl:value-of select="format-number(UnitPriceWithoutTax,'#.##0,00')"/>
																	</td>
																</tr>
															</xsl:for-each>
														</table>
													</td>
												</tr>
											</table>
										</td>
										<td width="15%" valign="top">
											<table border="0" cellpadding="0" cellspacing="0" width="100%">
												<tr>
													<td>
														<table border="0" cellpadding="0" cellspacing="0" width="100%">
															<xsl:for-each select="Invoices/Invoice/Items/InvoiceLine">
																<tr>
																	<td align="right">
																		<xsl:value-of select="format-number(TotalCost,'#.##0,00')"/>
																	</td>
																</tr>
															</xsl:for-each>
														</table>
													</td>
												</tr>
											</table>
										</td>
									</tr>
								</table>
							</td>
						</tr>
						<tr>
							<td><font color="FFFFFF">_</font></td>
						</tr>
						<tr>
							<td>
								<hr/>
							</td>
						</tr>
						<tr>
							<td>
								<font class="titulo2">IMPORTES</font>
							</td>
						</tr>
						<tr>
							<td><font color="FFFFFF">_</font></td>
						</tr>
						<tr>
							<td width="100%">
								<table border="0" cellpadding="0" cellspacing="0" width="100%">
									<tr>
										<td width="80%" align="right">
											<font class="titulopeque">IMPORTE BRUTO<font color="FFFFFF">___</font></font>
										</td>
										<td width="20%" align="center">
											<table border="1" cellpadding="0" cellspacing="0" width="100%">
												<tr>
													<td align="right">
														<font class="titulopeque">
															<xsl:value-of select="format-number(Invoices/Invoice/InvoiceTotals/TotalGrossAmount,'#.##0,00')"/>
														</font>
													</td>
												</tr>
											</table>
										</td>
									</tr>
								</table>
							</td>
						</tr>
						<tr>
							<td>
								<xsl:if test='Invoices/Invoice/InvoiceTotals/GeneralDiscounts!=""' >
									<font class="titulopeque"><i>DESCUENTOS</i></font>
									<table border="1" cellpadding="0" cellspacing="0" width="100%">
										<tr>
											<td width="70%" valign="top" align="center">
												<font class="titulopeque">CONCEPTO</font>
											</td>
											<td width="10%" valign="top" align="center">
												<font class="titulopeque">TIPO (%)</font>
											</td>
											<td width="20%" valign="top" align="center">
												<font class="titulopeque">IMPORTE</font>
											</td>
										</tr>
										<tr>
											<td width="70%" valign="top">
												<table border="0" cellpadding="0" cellspacing="0" width="100%">
													<xsl:for-each select="Invoices/Invoice/InvoiceTotals/GeneralDiscounts/Discount">
														<tr>
															<td width="100%">
																<xsl:apply-templates select="DiscountReason"/>
															</td>
														</tr>
													</xsl:for-each>
												</table>
											</td>
											<td width="10%" valign="top">
												<table border="0" cellpadding="0" cellspacing="0" width="100%">
													<xsl:for-each select="Invoices/Invoice/InvoiceTotals/GeneralDiscounts/Discount">
														<tr>
															<td width="100%" align="center">
																<xsl:value-of select="format-number(DiscountRate,'#0,00')"/>
															</td>
														</tr>
													</xsl:for-each>
												</table>
											</td>
											<td width="20%" valign="top">
												<table border="0" cellpadding="0" cellspacing="0" width="100%">
													<xsl:for-each select="Invoices/Invoice/InvoiceTotals/GeneralDiscounts/Discount">
														<tr>
															<td align="right">
																<xsl:value-of select="format-number(DiscountAmount,'#.##0,00')"/>
															</td>
														</tr>
													</xsl:for-each>
												</table>
											</td>
										</tr>
									</table>							
								</xsl:if>
							</td>
						</tr>
						<tr>
							<td><font color="FFFFFF">_</font></td>
						</tr>
						<tr>
							<td>
								<xsl:if test='Invoices/Invoice/TaxesOutputs!=""' >
									<font class="titulopeque"><i>IMPUESTOS REPERCUTIDOS</i></font>
									<table border="1" cellpadding="0" cellspacing="0" width="100%">
										<tr>
											<td width="50%" valign="top" align="center">
												<font class="titulopeque">CLASE DE IMPUESTO</font>
											</td>
											<td width="10%" valign="top" align="center">
												<font class="titulopeque">TIPO (%)</font>
											</td>
											<td width="20%" valign="top" align="center">
												<font class="titulopeque">BASE IMPONIBLE</font>
											</td>
											<td width="20%" valign="top" align="center">
												<font class="titulopeque">CUOTA</font>
											</td>
										</tr>
										<tr>
											<td width="50%" valign="top">
												<table border="0" cellpadding="0" cellspacing="0" width="100%">
													<xsl:for-each select="Invoices/Invoice/TaxesOutputs/Tax">
														<tr>
															<td width="100%">
																<xsl:apply-templates select="TaxTypeCode"/>
															</td>
														</tr>
													</xsl:for-each>
												</table>
											</td>
											<td width="10%" valign="top">
												<table border="0" cellpadding="0" cellspacing="0" width="100%">
													<xsl:for-each select="Invoices/Invoice/TaxesOutputs/Tax">
														<tr>
															<td width="100%" align="center">
																<xsl:value-of select="format-number(TaxRate,'#0,00')"/>
															</td>
														</tr>
													</xsl:for-each>
												</table>
											</td>
											<td width="10%" valign="top">
												<table border="0" cellpadding="0" cellspacing="0" width="100%">
													<xsl:for-each select="Invoices/Invoice/TaxesOutputs/Tax">
														<tr>
															<td width="100%" align="right">
																<xsl:value-of select="format-number(TaxableBase/TotalAmount,'#.##0,00')"/>
															</td>
														</tr>
													</xsl:for-each>
												</table>
											</td>
											<td width="20%" valign="top">
												<table border="0" cellpadding="0" cellspacing="0" width="100%">
													<xsl:for-each select="Invoices/Invoice/TaxesOutputs/Tax">
														<tr>
															<td align="right">
																<xsl:value-of select="format-number(TaxAmount/TotalAmount,'#.##0,00')"/>
															</td>
														</tr>
													</xsl:for-each>
												</table>
											</td>
										</tr>
									</table>							
								</xsl:if>
							</td>
						</tr>
						<tr>
							<td><font color="FFFFFF">_</font></td>
						</tr>
						<tr>
							<td>
								<xsl:if test='Invoices/Invoice/TaxesWithheld!=""' >
									<font class="titulopeque"><i>IMPUESTOS RETENIDOS</i></font>
									<table border="1" cellpadding="0" cellspacing="0" width="100%">
										<tr>
											<td width="50%" valign="top" align="center">
												<font class="titulopeque">CLASE DE IMPUESTO</font>
											</td>
											<td width="10%" valign="top" align="center">
												<font class="titulopeque">TIPO (%)</font>
											</td>
											<td width="20%" valign="top" align="center">
												<font class="titulopeque">BASE IMPONIBLE</font>
											</td>
											<td width="20%" valign="top" align="center">
												<font class="titulopeque">CUOTA</font>
											</td>
										</tr>
										<tr>
											<td width="50%" valign="top">
												<table border="0" cellpadding="0" cellspacing="0" width="100%">
													<xsl:for-each select="Invoices/Invoice/TaxesWithheld/Tax">
														<tr>
															<td width="100%">
																<xsl:apply-templates select="TaxTypeCode"/>
															</td>
														</tr>
													</xsl:for-each>
												</table>
											</td>
											<td width="10%" valign="top">
												<table border="0" cellpadding="0" cellspacing="0" width="100%">
													<xsl:for-each select="Invoices/Invoice/TaxesWithheld/Tax">
														<tr>
															<td width="100%" align="center">
																<xsl:value-of select="format-number(TaxRate,'#0,00')"/>
															</td>
														</tr>
													</xsl:for-each>
												</table>
											</td>
											<td width="10%" valign="top">
												<table border="0" cellpadding="0" cellspacing="0" width="100%">
													<xsl:for-each select="Invoices/Invoice/TaxesWithheld/Tax">
														<tr>
															<td width="100%" align="right">
																<xsl:value-of select="format-number(TaxableBase/TotalAmount,'#.##0,00')"/>
															</td>
														</tr>
													</xsl:for-each>
												</table>
											</td>
											<td width="20%" valign="top">
												<table border="0" cellpadding="0" cellspacing="0" width="100%">
													<xsl:for-each select="Invoices/Invoice/TaxesWithheld/Tax">
														<tr>
															<td align="right">
																<xsl:value-of select="format-number(TaxAmount/TotalAmount,'#.##0,00')"/>
															</td>
														</tr>
													</xsl:for-each>
												</table>
											</td>
										</tr>
									</table>							
								</xsl:if>
							</td>
						</tr>
						<tr>
							<td><font color="FFFFFF">_</font></td>
						</tr>
						<tr>
							<td align="right">
								<xsl:if test='Invoices/Invoice/InvoiceTotals/PaymentsonAccount!=""' >
									<table border="0" cellpadding="0" cellspacing="0" width="40%">
										<tr>
											<td><font class="titulopeque"><i>ANTICIPOS</i></font></td>
										</tr>
									</table>
									<table border="1" cellpadding="0" cellspacing="0" width="40%">
										<tr>
											<td width="50%" valign="top" align="center">
												<font class="titulopeque">FECHA</font>
											</td>
											<td width="50%" valign="top" align="center">
												<font class="titulopeque">IMPORTE</font>
											</td>
										</tr>
										<tr>
											<td width="50%" valign="top">
												<table border="0" cellpadding="0" cellspacing="0" width="100%">
													<xsl:for-each select="Invoices/Invoice/InvoiceTotals/PaymentsonAccount/PaymentOnAccount">
														<tr>
															<td width="100%" align="center">
																<xsl:value-of select="substring(PaymentOnAccountDate,9,2)"/>-<xsl:value-of select="substring(PaymentOnAccountDate,6,2)"/>-<xsl:value-of select="substring(PaymentOnAccountDate,1,4)"/>
															</td>
														</tr>
													</xsl:for-each>
												</table>
											</td>
											<td width="50%" valign="top">
												<table border="0" cellpadding="0" cellspacing="0" width="100%">
													<xsl:for-each select="Invoices/Invoice/InvoiceTotals/PaymentsonAccount/PaymentOnAccount">
														<tr>
															<td align="right">
																<xsl:value-of select="format-number(PaymentOnAccountAmount,'#.##0,00')"/>
															</td>
														</tr>
													</xsl:for-each>
												</table>
											</td>
										</tr>
									</table>							
								</xsl:if>
							</td>
						</tr>
						<tr>
							<td><font color="FFFFFF">_</font></td>
						</tr>
						<tr>
							<td width="100%">
								<table border="0" cellpadding="0" cellspacing="0" width="100%">
									<tr>
										<td width="80%" align="right">
											<font class="titulopeque">TOTAL EUROS<font color="FFFFFF">___</font></font>
										</td>
										<td width="20%" align="center">
											<table border="1" cellpadding="0" cellspacing="0" width="100%">
												<tr>
													<td align="right">
														<font class="titulopeque">
															<xsl:value-of select="format-number(Invoices/Invoice/InvoiceTotals/TotalExecutableAmount,'#.##0,00')"/>
														</font>
													</td>
												</tr>
											</table>
										</td>
									</tr>
								</table>
							</td>
						</tr>
						<xsl:apply-templates select="FileHeader/FactoringAssignmentData"/>
						<tr><td><font color="FFFFFF">_</font></td></tr>
						<tr><td><font color="FFFFFF">_</font></td></tr>
						<tr><td><font color="FFFFFF">_</font></td></tr>
					</table>
				</center>
				</div>
			</body>
		</html>
	</xsl:template>
	<xsl:template match="//m3:Facturae/Parties/SellerParty">
		<xsl:if test="LegalEntity!=''">
			<font class="titulo2">
				<xsl:value-of select="LegalEntity/CorporateName"/>
			</font>
			<br/>
			<font class="titulopeque">
				N.I.F.: <xsl:value-of select="TaxIdentification/TaxIdentificationNumber"/><br/>
				<xsl:value-of select="LegalEntity/AddressInSpain/Address"/><br/>
				<xsl:value-of select="LegalEntity/AddressInSpain/PostCode"/><font color="FFFFFF">_</font><font color="FFFFFF">_</font>
				<xsl:value-of select="LegalEntity/AddressInSpain/Town"/>
			</font>
		</xsl:if>
		<xsl:if test="Individual!=''">
			<font class="titulo2">
				<xsl:value-of select="Individual/Name"/>
					<xsl:if test="Individual/FirstSurname!=''">
						<font color="FFFFFF">_</font>
						<xsl:value-of select="Individual/FirstSurname"/>
					</xsl:if>
					<xsl:if test="Individual/SecondSurname!=''">
						<font color="FFFFFF">_</font>
						<xsl:value-of select="Individual/FirstSurname"/>
					</xsl:if>
			</font>
			<br/>
			<font class="titulopeque">
				N.I.F.: <xsl:value-of select="TaxIdentification/TaxIdentificationNumber"/><br/>
				<xsl:value-of select="Individual/AddressInSpain/Address"/><br/>
				<xsl:value-of select="Individual/AddressInSpain/PostCode"/><font color="FFFFFF">__</font>
				<xsl:value-of select="Individual/AddressInSpain/Town"/>
			</font>
		</xsl:if>
	</xsl:template>
	<xsl:template match="//m3:Facturae/Parties/BuyerParty">
		<xsl:if test="LegalEntity!=''">
			<font class="titulo2">
				DESTINATARIO
			</font>
			<br/>
			<font class="titulopeque">
				<xsl:value-of select="LegalEntity/CorporateName"/><br/>
				N.I.F.: <xsl:value-of select="TaxIdentification/TaxIdentificationNumber"/><br/>
				<xsl:value-of select="LegalEntity/AddressInSpain/Address"/><br/>
				<xsl:value-of select="LegalEntity/AddressInSpain/PostCode"/><font color="FFFFFF">_</font><font color="FFFFFF">_</font>
				<xsl:value-of select="LegalEntity/AddressInSpain/Town"/>
			</font>
		</xsl:if>
		<xsl:if test="Individual!=''">
			<font class="titulo2">
				<xsl:value-of select="Individual/Name"/><font color="FFFFFF">_</font>
				<xsl:value-of select="Individual/FirstSurname"/><font color="FFFFFF">_</font>
				<xsl:value-of select="Individual/SecondSurname"/><font color="FFFFFF">_</font>
			</font>
			<br/>
			<font class="titulopeque">
				N.I.F.: <xsl:value-of select="TaxIdentification/TaxIdentificationNumber"/><br/>
				<xsl:value-of select="Individual/AddressInSpain/Address"/><br/>
				<xsl:value-of select="Individual/AddressInSpain/PostCode"/><font color="FFFFFF">__</font>
				<xsl:value-of select="Individual/AddressInSpain/Town"/>
			</font>
		</xsl:if>
	</xsl:template>
	<xsl:template match="//m3:Facturae/FileHeader/FactoringAssignmentData">
		 <tr><td><font color="FFFFFF">_</font></td></tr>
		 <tr><td><hr/></td></tr>
		 <tr>
		 <td width="100%">
		 	<table border="0" cellpadding="0" cellspacing="0" width="100%">
		      		<tr>
		      			<td colspan="2">
						<font class="titulo2">
							DATOS CESIONARIO
						</font>
					</td>        	
		      		</tr>
		      		<tr>
		      			<td colspan="2"><font color="FFFFFF">_</font></td>        	
		      		</tr>
		      		<tr>
		      			<td>
						<font class="titulopeque">
							N.I.F.:
						</font>
					</td>        	
		      			<td><xsl:value-of select="Assignee/TaxIdentification/TaxIdentificationNumber"/></td>        	
		      		</tr>
		      		<tr>
		      			<td width="45%">
						<font class="titulopeque">
							RAZÓN SOCIAL / NOMBRE Y APELLIDOS:
						</font>
					</td>        	
		      			<td width="55%">
						<xsl:if test='Assignee/LegalEntity!=""' >
							<xsl:value-of select="Assignee/LegalEntity/CorporateName"/>
						</xsl:if>
						<xsl:if test='Assignee/Individual!=""' >
							<xsl:value-of select="Assignee/Individual/Name"/><font color="FFFFFF">_</font>
							<xsl:value-of select="Assignee/Individual/FirstSurname"/><font color="FFFFFF">_</font>
							<xsl:value-of select="Assignee/Individual/SecondSurname"/><font color="FFFFFF">_</font>
						</xsl:if>
					</td>        	
		      		</tr>
		      		<tr>
		      			<td>
						<font class="titulopeque">
							CUENTA:
						</font>
					</td>        	
		      			<td colspan="3">
						<xsl:value-of select="PaymentDetails/IBAN"/>
					</td>        	
		      		</tr>
			</table>
		    </td>
		</tr>
		<tr><td><font color="FFFFFF">_</font></td></tr>
		<tr><td><hr/></td></tr>
	</xsl:template>
</xsl:stylesheet>
