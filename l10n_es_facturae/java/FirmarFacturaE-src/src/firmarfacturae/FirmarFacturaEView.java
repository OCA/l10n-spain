/*
 * FirmarFacturaEView.java
 */

package firmarfacturae;

import java.io.BufferedReader;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStreamReader;

import java.security.cert.X509Certificate;
import java.text.SimpleDateFormat;
import java.util.Vector;

import org.jdesktop.application.Action;
import org.jdesktop.application.ResourceMap;
import org.jdesktop.application.SingleFrameApplication;
import org.jdesktop.application.FrameView;
import org.jdesktop.application.TaskMonitor;

import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import javax.swing.Timer;
import javax.swing.Icon;
import javax.swing.JDialog;
import javax.swing.filechooser.FileNameExtensionFilter;
import javax.swing.JFrame;


import es.mityc.firmaJava.configuracion.Configuracion;
import es.mityc.firmaJava.configuracion.EnumAlmacenCertificados;
import es.mityc.firmaJava.libreria.errores.ClienteError;
import es.mityc.firmaJava.libreria.utilidades.UtilidadDNIe;
import es.mityc.firmaJava.libreria.utilidades.UtilidadFirmaElectronica;
import es.mityc.firmaJava.libreria.xades.InterfazFirma;
import es.mityc.firmaJava.libreria.xades.InterfazObjetoDeFirma;
import es.mityc.firmaJava.libreria.xades.ParametrosFirmaXML;
import es.mityc.firmaJava.libreria.xades.errores.FirmaXMLError;

/**
 * The application's main frame.
 */
public class FirmarFacturaEView extends FrameView {

    private Vector<X509Certificate> listCertificates = null;
	private X509Certificate certificadoParaFirmar = null;
	private String NOMBRE_FICHERO_A_FIRMAR = "";
	private String NOMBRE_FICHERO_FIRMADO = "";

    FileNameExtensionFilter filtro = new FileNameExtensionFilter("Xml", "xml");

    public FirmarFacturaEView(SingleFrameApplication app) {
        super(app);

        initComponents();

        // status bar initialization - message timeout, idle icon and busy animation, etc
        ResourceMap resourceMap = getResourceMap();
        int messageTimeout = resourceMap.getInteger("StatusBar.messageTimeout");
        messageTimer = new Timer(messageTimeout, new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                statusMessageLabel.setText("");
            }
        });
        messageTimer.setRepeats(false);
        int busyAnimationRate = resourceMap.getInteger("StatusBar.busyAnimationRate");
        for (int i = 0; i < busyIcons.length; i++) {
            busyIcons[i] = resourceMap.getIcon("StatusBar.busyIcons[" + i + "]");
        }
        busyIconTimer = new Timer(busyAnimationRate, new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                busyIconIndex = (busyIconIndex + 1) % busyIcons.length;
                statusAnimationLabel.setIcon(busyIcons[busyIconIndex]);
            }
        });
        idleIcon = resourceMap.getIcon("StatusBar.idleIcon");
        statusAnimationLabel.setIcon(idleIcon);
        progressBar.setVisible(false);

        // connecting action tasks to status bar via TaskMonitor
        TaskMonitor taskMonitor = new TaskMonitor(getApplication().getContext());
        taskMonitor.addPropertyChangeListener(new java.beans.PropertyChangeListener() {
            public void propertyChange(java.beans.PropertyChangeEvent evt) {
                String propertyName = evt.getPropertyName();
                if ("started".equals(propertyName)) {
                    if (!busyIconTimer.isRunning()) {
                        statusAnimationLabel.setIcon(busyIcons[0]);
                        busyIconIndex = 0;
                        busyIconTimer.start();
                    }
                    progressBar.setVisible(true);
                    progressBar.setIndeterminate(true);
                } else if ("done".equals(propertyName)) {
                    busyIconTimer.stop();
                    statusAnimationLabel.setIcon(idleIcon);
                    progressBar.setVisible(false);
                    progressBar.setValue(0);
                } else if ("message".equals(propertyName)) {
                    String text = (String)(evt.getNewValue());
                    statusMessageLabel.setText((text == null) ? "" : text);
                    messageTimer.restart();
                } else if ("progress".equals(propertyName)) {
                    int value = (Integer)(evt.getNewValue());
                    progressBar.setVisible(true);
                    progressBar.setIndeterminate(false);
                    progressBar.setValue(value);
                }
            }
        });

        jFileChooser1.setFileFilter(filtro);
    }

    @Action
    public void showAboutBox() {
        if (aboutBox == null) {
            JFrame mainFrame = FirmarFacturaEApp.getApplication().getMainFrame();
            aboutBox = new FirmarFacturaEAboutBox(mainFrame);
            aboutBox.setLocationRelativeTo(mainFrame);
        }
        FirmarFacturaEApp.getApplication().show(aboutBox);
    }

    /** This method is called from within the constructor to
     * initialize the form.
     * WARNING: Do NOT modify this code. The content of this method is
     * always regenerated by the Form Editor.
     */
    @SuppressWarnings("unchecked")
    // <editor-fold defaultstate="collapsed" desc="Generated Code">//GEN-BEGIN:initComponents
    private void initComponents() {

        mainPanel = new javax.swing.JPanel();
        jTextOrigen = new javax.swing.JTextField();
        jBtnOrigen = new javax.swing.JButton();
        jTextDestino = new javax.swing.JTextField();
        jBtnDestino = new javax.swing.JButton();
        jCmbCertificados = new javax.swing.JComboBox();
        jBtnCargar = new javax.swing.JButton();
        jBtnFirmar = new javax.swing.JButton();
        menuBar = new javax.swing.JMenuBar();
        javax.swing.JMenu fileMenu = new javax.swing.JMenu();
        javax.swing.JMenuItem exitMenuItem = new javax.swing.JMenuItem();
        javax.swing.JMenu helpMenu = new javax.swing.JMenu();
        javax.swing.JMenuItem aboutMenuItem = new javax.swing.JMenuItem();
        statusPanel = new javax.swing.JPanel();
        javax.swing.JSeparator statusPanelSeparator = new javax.swing.JSeparator();
        statusMessageLabel = new javax.swing.JLabel();
        statusAnimationLabel = new javax.swing.JLabel();
        progressBar = new javax.swing.JProgressBar();
        jFileChooser1 = new javax.swing.JFileChooser();

        mainPanel.setName("mainPanel"); // NOI18N

        jTextOrigen.setName("jTextOrigen"); // NOI18N

        org.jdesktop.application.ResourceMap resourceMap = org.jdesktop.application.Application.getInstance(firmarfacturae.FirmarFacturaEApp.class).getContext().getResourceMap(FirmarFacturaEView.class);
        jBtnOrigen.setText(resourceMap.getString("jBtnOrigen.text")); // NOI18N
        jBtnOrigen.setActionCommand(resourceMap.getString("jBtnOrigen.actionCommand")); // NOI18N
        jBtnOrigen.setName("jBtnOrigen"); // NOI18N
        jBtnOrigen.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                jBtnOrigenActionPerformed(evt);
            }
        });

        jTextDestino.setName("jTextDestino"); // NOI18N

        jBtnDestino.setText(resourceMap.getString("jBtnDestino.text")); // NOI18N
        jBtnDestino.setName("jBtnDestino"); // NOI18N
        jBtnDestino.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                jBtnDestinoActionPerformed(evt);
            }
        });

        jCmbCertificados.setName("jCmbCertificados"); // NOI18N

        jBtnCargar.setText(resourceMap.getString("jBtnCargar.text")); // NOI18N
        jBtnCargar.setName("jBtnCargar"); // NOI18N
        jBtnCargar.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                jBtnCargarActionPerformed(evt);
            }
        });

        jBtnFirmar.setText(resourceMap.getString("jBtnFirmar.text")); // NOI18N
        jBtnFirmar.setName("jBtnFirmar"); // NOI18N
        jBtnFirmar.addActionListener(new java.awt.event.ActionListener() {
            public void actionPerformed(java.awt.event.ActionEvent evt) {
                jBtnFirmarActionPerformed(evt);
            }
        });

        javax.swing.GroupLayout mainPanelLayout = new javax.swing.GroupLayout(mainPanel);
        mainPanel.setLayout(mainPanelLayout);
        mainPanelLayout.setHorizontalGroup(
            mainPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(mainPanelLayout.createSequentialGroup()
                .addContainerGap()
                .addGroup(mainPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.TRAILING)
                    .addComponent(jTextDestino, javax.swing.GroupLayout.Alignment.LEADING, javax.swing.GroupLayout.DEFAULT_SIZE, 345, Short.MAX_VALUE)
                    .addComponent(jTextOrigen, javax.swing.GroupLayout.DEFAULT_SIZE, 345, Short.MAX_VALUE)
                    .addGroup(mainPanelLayout.createSequentialGroup()
                        .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED, 145, Short.MAX_VALUE)
                        .addComponent(jBtnCargar)
                        .addGap(109, 109, 109))
                    .addComponent(jCmbCertificados, javax.swing.GroupLayout.Alignment.LEADING, 0, 345, Short.MAX_VALUE))
                .addGap(18, 18, 18)
                .addGroup(mainPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
                    .addComponent(jBtnOrigen, javax.swing.GroupLayout.PREFERRED_SIZE, 87, javax.swing.GroupLayout.PREFERRED_SIZE)
                    .addComponent(jBtnDestino, javax.swing.GroupLayout.PREFERRED_SIZE, 87, javax.swing.GroupLayout.PREFERRED_SIZE))
                .addGap(157, 157, 157))
            .addGroup(mainPanelLayout.createSequentialGroup()
                .addGap(66, 66, 66)
                .addComponent(jBtnFirmar, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                .addGap(486, 486, 486))
        );
        mainPanelLayout.setVerticalGroup(
            mainPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(mainPanelLayout.createSequentialGroup()
                .addGap(30, 30, 30)
                .addGroup(mainPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.BASELINE)
                    .addComponent(jTextOrigen, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                    .addComponent(jBtnOrigen))
                .addGap(18, 18, 18)
                .addGroup(mainPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.BASELINE)
                    .addComponent(jTextDestino, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                    .addComponent(jBtnDestino))
                .addGap(18, 18, 18)
                .addComponent(jCmbCertificados, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addGap(75, 75, 75)
                .addGroup(mainPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.BASELINE)
                    .addComponent(jBtnFirmar)
                    .addComponent(jBtnCargar))
                .addContainerGap(20, Short.MAX_VALUE))
        );

        menuBar.setName("menuBar"); // NOI18N

        fileMenu.setText(resourceMap.getString("fileMenu.text")); // NOI18N
        fileMenu.setName("fileMenu"); // NOI18N

        javax.swing.ActionMap actionMap = org.jdesktop.application.Application.getInstance(firmarfacturae.FirmarFacturaEApp.class).getContext().getActionMap(FirmarFacturaEView.class, this);
        exitMenuItem.setAction(actionMap.get("quit")); // NOI18N
        exitMenuItem.setText(resourceMap.getString("exitMenuItem.text")); // NOI18N
        exitMenuItem.setName("exitMenuItem"); // NOI18N
        fileMenu.add(exitMenuItem);

        menuBar.add(fileMenu);
        fileMenu.getAccessibleContext().setAccessibleName(resourceMap.getString("fileMenu.AccessibleContext.accessibleName")); // NOI18N

        helpMenu.setText(resourceMap.getString("helpMenu.text")); // NOI18N
        helpMenu.setName("helpMenu"); // NOI18N

        aboutMenuItem.setAction(actionMap.get("showAboutBox")); // NOI18N
        aboutMenuItem.setName("aboutMenuItem"); // NOI18N
        helpMenu.add(aboutMenuItem);

        menuBar.add(helpMenu);

        statusPanel.setName("statusPanel"); // NOI18N

        statusPanelSeparator.setName("statusPanelSeparator"); // NOI18N

        statusMessageLabel.setName("statusMessageLabel"); // NOI18N

        statusAnimationLabel.setHorizontalAlignment(javax.swing.SwingConstants.LEFT);
        statusAnimationLabel.setName("statusAnimationLabel"); // NOI18N

        progressBar.setName("progressBar"); // NOI18N

        javax.swing.GroupLayout statusPanelLayout = new javax.swing.GroupLayout(statusPanel);
        statusPanel.setLayout(statusPanelLayout);
        statusPanelLayout.setHorizontalGroup(
            statusPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addComponent(statusPanelSeparator, javax.swing.GroupLayout.DEFAULT_SIZE, 617, Short.MAX_VALUE)
            .addGroup(statusPanelLayout.createSequentialGroup()
                .addContainerGap()
                .addComponent(statusMessageLabel)
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED, 443, Short.MAX_VALUE)
                .addComponent(progressBar, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED)
                .addComponent(statusAnimationLabel)
                .addContainerGap())
        );
        statusPanelLayout.setVerticalGroup(
            statusPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.LEADING)
            .addGroup(statusPanelLayout.createSequentialGroup()
                .addComponent(statusPanelSeparator, javax.swing.GroupLayout.PREFERRED_SIZE, 2, javax.swing.GroupLayout.PREFERRED_SIZE)
                .addPreferredGap(javax.swing.LayoutStyle.ComponentPlacement.RELATED, javax.swing.GroupLayout.DEFAULT_SIZE, Short.MAX_VALUE)
                .addGroup(statusPanelLayout.createParallelGroup(javax.swing.GroupLayout.Alignment.BASELINE)
                    .addComponent(statusMessageLabel)
                    .addComponent(statusAnimationLabel)
                    .addComponent(progressBar, javax.swing.GroupLayout.PREFERRED_SIZE, javax.swing.GroupLayout.DEFAULT_SIZE, javax.swing.GroupLayout.PREFERRED_SIZE))
                .addGap(3, 3, 3))
        );

        jFileChooser1.setName("jFileChooser1"); // NOI18N

        setComponent(mainPanel);
        setMenuBar(menuBar);
        setStatusBar(statusPanel);
    }// </editor-fold>//GEN-END:initComponents

    private void jBtnOrigenActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_jBtnOrigenActionPerformed
        // TODO add your handling code here:
        int returnVal = jFileChooser1.showDialog(mainPanel, "Fichero a Firmar");

        if (returnVal == javax.swing.JFileChooser.APPROVE_OPTION) {
            jTextOrigen.setText(jFileChooser1.getSelectedFile().getPath());
        }
    }//GEN-LAST:event_jBtnOrigenActionPerformed

    private void jBtnDestinoActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_jBtnDestinoActionPerformed
        // TODO add your handling code here:
        int returnVal = jFileChooser1.showDialog(mainPanel, "Fichero Firmado");

        if (returnVal == javax.swing.JFileChooser.APPROVE_OPTION) {
            jTextDestino.setText(jFileChooser1.getSelectedFile().getPath());
        }
}//GEN-LAST:event_jBtnDestinoActionPerformed

    private void jBtnCargarActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_jBtnCargarActionPerformed
        // TODO add your handling code here:

        // Accedemos al almacén de certificados de internet explorer
        InterfazFirma si = UtilidadFirmaElectronica.getSignatureInstance(EnumAlmacenCertificados.ALMACEN_EXPLORER);
        try {
            listCertificates = si.getAllCertificates("My");
        } catch (FirmaXMLError e1) {
            e1.printStackTrace();
        }
        // Llemanos el Combo
        mostrarInformacionCertificados(listCertificates);

    }//GEN-LAST:event_jBtnCargarActionPerformed

    private void jBtnFirmarActionPerformed(java.awt.event.ActionEvent evt) {//GEN-FIRST:event_jBtnFirmarActionPerformed
        // TODO add your handling code here:
        NOMBRE_FICHERO_A_FIRMAR = jTextOrigen.getText();
        NOMBRE_FICHERO_FIRMADO = jTextDestino.getText();
        System.out.println(jCmbCertificados.getSelectedIndex());
        certificadoParaFirmar = (X509Certificate) listCertificates.get(jCmbCertificados.getSelectedIndex());
        try {
            finalizarFirma();
        } catch (Exception e) {
            e.printStackTrace();
        }
}//GEN-LAST:event_jBtnFirmarActionPerformed

    private void finalizarFirma() throws Exception {

		// Instanciamos la estructura de datos que almacenará el resultado de la firma
		byte[] resultadoFirma = null;

		// Instanciamos la clase Configuracion de Libreriaconfiguracion
		Configuracion configuracion = new Configuracion();
		// Cargamos el valor de los parámetros contenidos en el fichero SignXML.properties
		configuracion.cargarConfiguracion();

		// Se lee el fichero a firmar
		String rutaFicheroAFirmar = NOMBRE_FICHERO_A_FIRMAR;
		BufferedReader in = new BufferedReader(new InputStreamReader(new FileInputStream(rutaFicheroAFirmar), "UTF-8"));

		// Atención!!! aquí cambiamos los saltos de carro del fichero original para facilitar la lectura del ejemplo
		// Si se ha de firmar exactamente el mismo fichero de entrada la lectura no ha de modificar el resultado.
		StringBuffer xmlToSign = new StringBuffer();
		while (in.ready()) {
			xmlToSign.append(in.readLine());
		}

		// Nodos que contendrán las firmas del fichero (se incluye Certificate1 porque será donde irá el certificado de firma)
		String nodesToSign = "Certificate1,";
		configuracion.setValor("xmlNodeToSign", nodesToSign);

        // Para firmar con un certificado del almacén de Internet Explorer
        InterfazObjetoDeFirma soi = UtilidadFirmaElectronica.getSignatureObject(EnumAlmacenCertificados.ALMACEN_EXPLORER,
        		certificadoParaFirmar,
        		"",
        		configuracion);

        // Para firmar con un certificado del almacén de Mozilla
        //InterfazObjetoDeFirma soi = UtilidadFirmaElectronica.getSignatureObject(EnumAlmacenCertificados.ALMACEN_EXPLORER,
        //		cert.getSerialNumber(),
        //		cert.getIssuerDN().toString(),
        //		"Poner aqui la ruta al perfil de Mozilla",
        //		configuracion);

        // Se prepara e inicializa el interfaz de firma
        try {
			soi.initSign();
		} catch (ClienteError e1) {
			e1.printStackTrace();
		}

        // Se realiza la firma
		try {
			resultadoFirma = soi.sign(xmlToSign.toString());
		} catch (ClienteError e) {
			e.printStackTrace();
		}

		if (resultadoFirma != null) {
			System.out.println("\n\nLa firma se creo correctamente. Se salva con el nombre " + NOMBRE_FICHERO_FIRMADO);

			// Una vez finalizada la firma, escribimos el resultado en el fichero de salida
			grabarAFichero(resultadoFirma);

			// Si se quiere continuar realizando validaciones o firmas es necesario inicializar esta estructura
			ParametrosFirmaXML.initialize();
		} else
			System.out.println("\n\nLa firma NO se creo correctamente");
	}

    private void grabarAFichero(byte[] firmaXADESByte) {

		FileOutputStream fos = null;
		try {
			String rutaFicheroFirmado = NOMBRE_FICHERO_FIRMADO;
			fos = new FileOutputStream(rutaFicheroFirmado);
			fos.write(firmaXADESByte);
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		} catch (IOException e) {
			e.printStackTrace();
		} finally {
			try {
				fos.flush();
				fos.close();
			} catch (IOException e) {
				e.printStackTrace();
			}
		}
	}

    private void mostrarInformacionCertificados(Vector<X509Certificate> listCertificates) {

		for (int a = 0; a < listCertificates.size(); a++) {
			X509Certificate certTemp = (X509Certificate) listCertificates.get(a);

            jCmbCertificados.addItem(UtilidadDNIe.getCN(certTemp, UtilidadDNIe.SUBJECT_OR_ISSUER.SUBJECT));
		}
	}

    // Variables declaration - do not modify//GEN-BEGIN:variables
    private javax.swing.JButton jBtnCargar;
    private javax.swing.JButton jBtnDestino;
    private javax.swing.JButton jBtnFirmar;
    private javax.swing.JButton jBtnOrigen;
    private javax.swing.JComboBox jCmbCertificados;
    private javax.swing.JFileChooser jFileChooser1;
    private javax.swing.JTextField jTextDestino;
    private javax.swing.JTextField jTextOrigen;
    private javax.swing.JPanel mainPanel;
    private javax.swing.JMenuBar menuBar;
    private javax.swing.JProgressBar progressBar;
    private javax.swing.JLabel statusAnimationLabel;
    private javax.swing.JLabel statusMessageLabel;
    private javax.swing.JPanel statusPanel;
    // End of variables declaration//GEN-END:variables

    private final Timer messageTimer;
    private final Timer busyIconTimer;
    private final Icon idleIcon;
    private final Icon[] busyIcons = new Icon[15];
    private int busyIconIndex = 0;

    private JDialog aboutBox;
}
