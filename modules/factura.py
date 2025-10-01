from odoo import models, fields
from odoo.exceptions import ValidationError, UserError

import xml.etree.ElementTree as ET
from datetime import datetime
import pytz
from dateutil import tz


class GenerarFactura(models.TransientModel):
    _name = "generar.factura"

    def generar_factura(self, factura, correlativo):
        # VALIDACIÓN DE FECHAS
        if factura.tipo_factura == "fact":
            if not factura.invoice_date:
                fecha_factura = datetime.now(pytz.timezone("America/Guatemala")).date()
                if fecha_factura == factura.invoice_date_due:
                    factura.invoice_date = fecha_factura
                else:
                    raise UserError(
                        "La fecha de factura debe ser la misma a la fecha de vencimiento para una factura."
                    )
            if factura.invoice_date != factura.invoice_date_due:
                raise UserError(
                    "La fecha de factura debe ser la misma a la fecha de vencimiento para una factura."
                )

        # ETIQUETA RAIZ DEL XML
        root = ET.Element(
            "dte:GTDocumento",
            {
                "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "xmlns:crc": "http://www.sat.gob.gt/face2/ComplementoReferenciaConstancia/0.1.0",
                "xmlns:cesp": "http://www.sat.gob.gt/face2/ComplementoEspectaculos/0.1.0",
                "xmlns:ctrasmer": "http://www.sat.gob.gt/face2/TrasladoMercancias/0.1.0",
                "xmlns:cexprov": "http://www.sat.gob.gt/face2/ComplementoExportacionProvisional/0.1.0",
                "xmlns:clepp": "http://www.sat.gob.gt/face2/ComplementoPartidosPolitico/0.1.0",
                "xmlns:cmep": "http://www.sat.gob.gt/face2/ComplementoMediosDePago/0.1.0",
                "xmlns:cfc": "http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0",
                "xmlns:cfe": "http://www.sat.gob.gt/face2/ComplementoFacturaEspecial/0.1.0",
                "xmlns:cno": "http://www.sat.gob.gt/face2/ComplementoReferenciaNota/0.1.0",
                "xmlns:cca": "http://www.sat.gob.gt/face2/CobroXCuentaAjena/0.1.0",
                "xmlns:ds": "http://www.w3.org/2000/09/xmldsig#",
                "xmlns:ctup": "http://www.sat.gob.gt/face2/ComplementoTurismoPasaje/0.1.0",
                "xmlns:cex": "http://www.sat.gob.gt/face2/ComplementoExportaciones/0.1.0",
                "Version": "0.1",
                "xmlns:dte": "http://www.sat.gob.gt/dte/fel/0.2.0",
            },
        )

        # INFORMACIÓN GENERAL DEL DOCUMENTO
        dte_sat = ET.SubElement(root, "dte:SAT", {"ClaseDocumento": "dte"})
        dte_dte = ET.SubElement(dte_sat, "dte:DTE", {"ID": "DatosCertificados"})
        datos_emision = ET.SubElement(dte_dte, "dte:DatosEmision", {"ID": "DatosEmision"})
        zh_usuario = tz.gettz(self.env.user.tz)

        if factura.invoice_date:
            fecha_base = factura.invoice_date
        else:
            now_local = fields.Datetime.context_timestamp(factura, fields.Datetime.now())
            fecha_base = now_local.date()

        hora_local = fields.Datetime.context_timestamp(factura, fields.Datetime.now())

        fecha_hora_utc = datetime(
            fecha_base.year,
            fecha_base.month,
            fecha_base.day,
            hora_local.hour,
            hora_local.minute,
            hora_local.second,
        )
        fecha_hora = fecha_hora_utc.replace(tzinfo=zh_usuario)
        factura.fecha_emision = fecha_hora.astimezone(tz.UTC).replace(tzinfo=None)
        fecha_obtenida = fecha_hora.strftime("%Y-%m-%dT%H:%M:%S-06:00")
        tipos_documento = {"fact": "FACT", "fact_cambiaria": "FCAM"}
        tipo_documento = tipos_documento[f"{factura.tipo_factura}"]

        datos_generales = ET.SubElement(
            datos_emision,
            "dte:DatosGenerales",
            {
                "CodigoMoneda": f"{factura.currency_id.name}",
                "FechaHoraEmision": f"{fecha_obtenida}",
                "Tipo": tipo_documento,
            },
        )

        # DATOS DEL EMISOR
        afiliacion_iva = "GEN" if factura.company_id.tipo_contribuyente == "general" else ""

        entorno_prueba_activo = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("fel.entorno_pruebas_%d" % self.env.company.id, default=False)
        )

        nit = (
            factura.company_id.nit_pruebas if entorno_prueba_activo else factura.company_id.vat
        )

        dte_emisor = ET.SubElement(
            datos_emision,
            "dte:Emisor",
            {
                "AfiliacionIVA": f"{afiliacion_iva}",
                "CodigoEstablecimiento": f"{factura.establecimiento_id.codigo}",
                "CorreoEmisor": f"{factura.company_id.email or ''}",
                "NITEmisor": f"{nit}",
                "NombreComercial": f"{factura.company_id.nombre_comercial}",
                "NombreEmisor": f"{factura.company_id.nombre_emisor}",
            },
        )
        direccion_emisor = ET.SubElement(dte_emisor, "dte:DireccionEmisor")
        dte_direccion_emisor = ET.SubElement(direccion_emisor, "dte:Direccion").text = (
            f"{factura.establecimiento_id.direccion}"
        )
        codigo_postal_emisor = ET.SubElement(direccion_emisor, "dte:CodigoPostal").text = (
            f"{factura.establecimiento_id.empresa_id.zip}"
        )
        municipio_emisor = ET.SubElement(direccion_emisor, "dte:Municipio").text = (
            f"{factura.establecimiento_id.municipio}"
        )
        departamento_emisor = ET.SubElement(direccion_emisor, "dte:Departamento").text = (
            f"{factura.establecimiento_id.departamento}"
        )
        pais_emisor = ET.SubElement(direccion_emisor, "dte:Pais").text = (
            f"{factura.establecimiento_id.empresa_id.country_id.code}"
        )

        # DATOS DEL RECEPTOR
        receptor_id = factura.partner_id

        correo_receptor = f"{receptor_id.email}" if receptor_id.email else ""

        if receptor_id.type == "invoice":
            nombre_receptor = (
                receptor_id.razon_social_child
                if receptor_id.razon_social_child
                else receptor_id.name
            )

            id_receptor = receptor_id.nit_child if receptor_id.nit_child else receptor_id.cui

        elif receptor_id:
            nombre_receptor = (
                receptor_id.razon_social if receptor_id.razon_social else receptor_id.name
            )

            id_receptor = receptor_id.vat if receptor_id.vat else receptor_id.cui

        else:
            nombre_receptor = (
                f"{receptor_id.razon_social}"
                if not receptor_id.extranjero and receptor_id.razon_social
                else f"{receptor_id.name}"
            )

        dte_receptor = ET.SubElement(
            datos_emision,
            "dte:Receptor",
            {
                "CorreoReceptor": correo_receptor,
                "NombreReceptor": f"{nombre_receptor}",
            },
        )

        dte_receptor.set("IDReceptor", f"{id_receptor}")

        if receptor_id.extranjero:
            dte_receptor.set("TipoEspecial", "EXT")
        elif not receptor_id.extranjero and id_receptor == receptor_id.cui:
            dte_receptor.set("TipoEspecial", "CUI")

        direccion_receptor = ET.SubElement(dte_receptor, "dte:DireccionReceptor")
        direccion_receptor_valor = f"{receptor_id.street}" if receptor_id.street else "CIUDAD"
        dte_direccion_receptor = ET.SubElement(direccion_receptor, "dte:Direccion").text = (
            f"{direccion_receptor_valor}"
        )
        codigo_postal = f"{receptor_id.zip}" if receptor_id.zip else "00000"
        codigo_postal_receptor = ET.SubElement(direccion_receptor, "dte:CodigoPostal").text = (
            codigo_postal
        )
        municipio = (
            f"{receptor_id.state_id.name}" if receptor_id.state_id.name else "Guatemala"
        )
        municipio_receptor = ET.SubElement(direccion_receptor, "dte:Municipio").text = (
            municipio
        )
        departamento = f"{receptor_id.city}" if receptor_id.city else "Guatemala"
        departamento_receptor = ET.SubElement(direccion_receptor, "dte:Departamento").text = (
            departamento
        )
        pais_receptor = ET.SubElement(direccion_receptor, "dte:Pais").text = (
            f"{receptor_id.country_id.code}"
        )

        # FRASES
        dte_frases = ET.SubElement(datos_emision, "dte:Frases")
        if factura.company_id.tipo_contribuyente == "general":
            if factura.company_id.regimen_isr == "utilities":
                frase_uno_escenario = 1
            elif factura.company_id.regimen_isr == "simplified":
                frase_uno_escenario = 2
            elif factura.company_id.regimen_isr == "simplified_direct_payment":
                frase_uno_escenario = 3

            if frase_uno_escenario != 3:
                frase_uno = ET.SubElement(
                    dte_frases,
                    "dte:Frase",
                    {"TipoFrase": "1", "CodigoEscenario": f"{frase_uno_escenario}"},
                )
            else:
                frase_uno = ET.SubElement(
                    dte_frases,
                    "dte:Frase",
                    {
                        "TipoFrase": "1",
                        "CodigoEscenario": f"{frase_uno_escenario}",
                        "FechaResolucion": f"{factura.company_id.fecha_resolucion}",
                        "NumeroResolucion": f"{factura.company_id.numero_resolucion}",
                    },
                )
        if factura.exento_iva:
            frase_exento = ET.SubElement(
                dte_frases,
                "dte:Frase",
                {
                    "TipoFrase": f"{factura.frase_base_ids.tipo_frase}",
                    "CodigoEscenario": f"{factura.frase_base_ids.codigo_escenario}",
                },
            )

        if factura.company_id.retenedor_iva:
            frase_dos = ET.SubElement(
                dte_frases, "dte:Frase", {"TipoFrase": "2", "CodigoEscenario": "1"}
            )

        if factura.fiscal_position_id.frases_fel_id:
            for frase in factura.fiscal_position_id.frases_fel_id:
                if frase.name == "Exportaciones":
                    continue

                frase_fel = ET.SubElement(
                    dte_frases,
                    "dte:Frase",
                    {
                        "TipoFrase": f"{frase.tipo_frase}",
                        "CodigoEscenario": f"{frase.codigo_escenario}",
                    },
                )

        # ITEMS
        dte_items = ET.SubElement(datos_emision, "dte:Items")
        linea = 1
        impuestos_encontrados = dict()

        for line in factura.invoice_line_ids:
            if line.display_type != "product":
                continue

            bien_o_servicio = "B" if line.product_id.detailed_type != "service" else "S"
            dte_item = ET.SubElement(
                dte_items,
                "dte:Item",
                {"BienOServicio": f"{bien_o_servicio}", "NumeroLinea": f"{linea}"},
            )
            linea += 1
            descuento = round(((line.discount / 100) * line.price_unit * line.quantity), 6)
            dte_cantidad = ET.SubElement(dte_item, "dte:Cantidad").text = f"{line.quantity}"
            if line.product_uom_id:
                medida = (
                    line.product_uom_id.name[:3]
                    if len(line.product_uom_id.name) > 3
                    else line.product_uom_id.name
                )
            else:
                medida = "UND"
            unidad_medida = ET.SubElement(dte_item, "dte:UnidadMedida").text = medida.upper()
            dte_descripcion = ET.SubElement(dte_item, "dte:Descripcion").text = f"{line.name}"

            impuestos_incluidos_precio = 0
            for imp in line.tax_ids:
                if imp.nombre_corto == "BEBIDAS ALCOHOLICAS" and imp.price_include:
                    impuestos_incluidos_precio += (
                        (imp.amount / 100)
                        * line.product_uom_id.ratio
                        * line.product_id.precio_sugerido
                    )
                elif imp.nombre_corto == "BEBIDAS NO ALCOHOLICAS" and imp.price_include:
                    impuestos_incluidos_precio += (
                        (imp.amount / 100)
                        * line.product_uom_id.ratio
                        * (line.product_id.contenido_neto / 1000)
                    )
                elif imp.nombre_corto == "TIMBRE DE PRENSA" and imp.price_include:
                    importe_iva = 0
                    importe_tdp = imp.amount / 100

                    for _impuesto in line.tax_ids:
                        if _impuesto.nombre_corto == "IVA" and _impuesto.codigo_gravable == 1:
                            importe_iva = _impuesto.amount / 100

                    monto_gravable = round(
                        (line.price_unit - descuento) / (1 + importe_iva + importe_tdp), 6
                    )
                    # raise ValidationError(monto_gravable)
                    impuestos_incluidos_precio += (imp.amount / 100) * monto_gravable

            precio_unitario_sat = round((line.price_unit - impuestos_incluidos_precio), 6)
            precio_unitario = ET.SubElement(dte_item, "dte:PrecioUnitario").text = (
                f"{precio_unitario_sat}"
            )

            dte_precio = ET.SubElement(dte_item, "dte:Precio").text = (
                f"{round((precio_unitario_sat * line.quantity), 6)}"
            )
            dte_descuento = ET.SubElement(dte_item, "dte:Descuento").text = f"{descuento}"

            # IMPUESTOS DEL ITEM
            dte_impuestos = ET.SubElement(dte_item, "dte:Impuestos")
            for impuesto in line.tax_ids:
                dte_impuesto = ET.SubElement(dte_impuestos, "dte:Impuesto")
                nombre = impuesto.nombre_corto
                nombre_corto = ET.SubElement(dte_impuesto, "dte:NombreCorto").text = (
                    f"{nombre}"
                )
                codigo_unidad_gravable = ET.SubElement(
                    dte_impuesto, "dte:CodigoUnidadGravable"
                ).text = f"{impuesto.codigo_gravable}"

                # SI ES BEBIDA
                # SI ES ALCOHOLICA
                monto = 0
                if impuesto.nombre_corto == "BEBIDAS ALCOHOLICAS":
                    bebidas_alcoholicas = self.env["account.tax"]
                    monto = bebidas_alcoholicas._get_bebidas_alcoholicas_tax(
                        line, impuesto, dte_impuesto
                    )
                # SI NO ES ALCOHOLICA
                elif impuesto.nombre_corto == "BEBIDAS NO ALCOHOLICAS":
                    bebidas_no_alcoholias = self.env["account.tax"]
                    monto = bebidas_no_alcoholias._get_bebidas_no_alcoholicas_tax(
                        line, impuesto, dte_impuesto
                    )

                # TIMBRE DE PRENSA
                elif impuesto.nombre_corto == "TIMBRE DE PRENSA":
                    calculo_monto_gravable = round(
                        (((line.quantity * precio_unitario_sat) - descuento) / 1.12), 6
                    )
                    monto_gravable = ET.SubElement(dte_impuesto, "dte:MontoGravable").text = (
                        f"{calculo_monto_gravable}"
                    )
                    importe = impuesto.amount / 100
                    monto = round((calculo_monto_gravable * importe), 6)
                    monto_impuesto = ET.SubElement(dte_impuesto, "dte:MontoImpuesto").text = (
                        f"{monto}"
                    )

                elif impuesto.nombre_corto == "IVA" and impuesto.codigo_gravable == 2:
                    calculo_monto_gravable = round(
                        ((line.quantity * precio_unitario_sat) - descuento), 6
                    )
                    monto_gravable = ET.SubElement(dte_impuesto, "dte:MontoGravable").text = (
                        f"{calculo_monto_gravable}"
                    )
                    importe = impuesto.amount / 100
                    monto = round((calculo_monto_gravable * importe), 6)
                    monto_impuesto = ET.SubElement(dte_impuesto, "dte:MontoImpuesto").text = (
                        f"{monto}"
                    )

                else:
                    calculo_monto_gravable = round(
                        (((line.quantity * precio_unitario_sat) - descuento) / 1.12), 6
                    )
                    monto_gravable = ET.SubElement(dte_impuesto, "dte:MontoGravable").text = (
                        f"{calculo_monto_gravable}"
                    )
                    importe = impuesto.amount / 100
                    monto = round((calculo_monto_gravable * importe), 6)
                    monto_impuesto = ET.SubElement(dte_impuesto, "dte:MontoImpuesto").text = (
                        f"{monto}"
                    )

                impuestos_encontrados[nombre] = impuestos_encontrados.get(nombre, 0) + monto

            dte_total = ET.SubElement(dte_item, "dte:Total").text = (
                f"{round(line.price_total, 6)}"
            )

        # TOTALES
        dte_totales = ET.SubElement(datos_emision, "dte:Totales")
        total_impuestos = ET.SubElement(dte_totales, "dte:TotalImpuestos")

        for registro_impuesto, registro_monto in impuestos_encontrados.items():
            total_impuesto = ET.SubElement(
                total_impuestos,
                "dte:TotalImpuesto",
                {
                    "NombreCorto": f"{registro_impuesto}",
                    "TotalMontoImpuesto": f"{round(registro_monto, 6)}",
                },
            )

        gran_total = ET.SubElement(dte_totales, "dte:GranTotal").text = (
            f"{round(factura.amount_total, 6)}"
        )

        if (
            factura.tipo_factura == "fact_cambiaria"
            or factura.fiscal_position_id.name == "Exportación"
        ):
            dte_complementos = ET.SubElement(datos_emision, "dte:Complementos")

        # ADENDAS
        dte_adenda = ET.SubElement(dte_sat, "dte:Adenda")
        referencia_cliente = factura.ref if factura.ref else ""
        envios_orden_compra = ET.SubElement(dte_adenda, "envios-orden-compra").text = (
            f"{referencia_cliente}"
        )
        numero_interno = ET.SubElement(dte_adenda, "numerointerno").text = correlativo

        telefono = ""
        if factura.partner_id.phone:
            telefono = factura.partner_id.phone
        elif factura.partner_id.mobile:
            telefono = factura.partner_id.mobile

        telefono_cliente = ET.SubElement(dte_adenda, "telefonocliente").text = f"{telefono}"
        iniciales_vendedor = ET.SubElement(dte_adenda, "inicialesvendedor").text = (
            f"{factura.invoice_user_id.name}"
        )
        codigo_cliente = ET.SubElement(dte_adenda, "codigocliente").text = (
            f"{factura.partner_id.id}"
        )
        interes = ET.SubElement(dte_adenda, "INTERESES").text = "5"
        fecha_vencimiento = ET.SubElement(dte_adenda, "FECHA-DE-VENCIMIENTO").text = (
            f"{factura.invoice_date_due.strftime('%d/%m/%Y')}"
        )
        nombre_cliente = ET.SubElement(dte_adenda, "nombre-cliente").text = (
            f"{factura.partner_id.name}"
        )

        if factura.tipo_factura == "fact_cambiaria":
            if not factura.invoice_date:
                factura.invoice_date = datetime.now(pytz.timezone("America/Guatemala")).date()

            dias = factura.invoice_date_due - factura.invoice_date
            dias_formatedos = str(dias).split(" ")[0]
            credito = ET.SubElement(dte_adenda, "credito").text = "X"
            dias_credito = ET.SubElement(dte_adenda, "dias").text = f"{dias_formatedos}"
        else:
            contado = ET.SubElement(dte_adenda, "contado").text = "X"
            dias_credito = ET.SubElement(dte_adenda, "dias").text = "0"

        if factura.company_id.proveedor == "megaprint":
            adenda_detail = ET.SubElement(dte_adenda, "AdendaDetail")
            adenda_summary = ET.SubElement(adenda_detail, "AdendaSummary")
            adenda_untaxed = ET.SubElement(adenda_summary, "Valor1").text = (
                f"Q.{factura.amount_untaxed}"
            )

        # CAMBIARIA
        # VALIDACIÓN DE FECHAS
        if factura.tipo_factura == "fact_cambiaria":
            if not factura.invoice_date:
                fecha_factura_cambiaria = datetime.now(
                    pytz.timezone("America/Guatemala")
                ).date()
                factura.invoice_date = fecha_factura_cambiaria
                if factura.invoice_date_due == factura.invoice_date:
                    raise UserError(
                        "La fecha de factura debe ser distinta de la fecha de vencimiento para una factura cambiaria"
                    )
                else:
                    factura.invoice_date = fecha_factura_cambiaria
            if factura.invoice_date == factura.invoice_date_due:
                raise UserError(
                    "La fecha de factura debe ser distinta de la fecha de vencimiento para una factura cambiaria"
                )

            complemento_cambiaria = ET.SubElement(
                dte_complementos,
                "dte:Complemento",
                {
                    "IDComplemento": "1",
                    "NombreComplemento": "Abono",
                    "URIComplemento": "http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0",
                },
            )
            cfc_abonos_factura_cambiaria = ET.SubElement(
                complemento_cambiaria,
                "cfc:AbonosFacturaCambiaria",
                {
                    "Version": "1",
                    "xmlns:cfc": "http://www.sat.gob.gt/dte/fel/CompCambiaria/0.1.0",
                },
            )
            cfc_abono = ET.SubElement(cfc_abonos_factura_cambiaria, "cfc:Abono")
            cfc_numero_abono = ET.SubElement(cfc_abono, "cfc:NumeroAbono").text = "1"
            cfc_fecha_vencimiento = ET.SubElement(cfc_abono, "cfc:FechaVencimiento").text = (
                f"{factura.invoice_date_due}"
            )
            cfc_monto_abono = ET.SubElement(cfc_abono, "cfc:MontoAbono").text = (
                f"{factura.amount_total}"
            )

        # EXPORTACIÓN
        if factura.fiscal_position_id.name == "Exportación":
            datos_generales.set("Exp", "SI")

            # COMPLEMENTOS EXPORTACION
            if not factura.nombre_consignatario or not factura.direccion_consignatario:
                raise ValidationError(
                    "Debe ingresar un nombre y dirección para el consignatario."
                )

            complemento_exportacion = ET.SubElement(
                dte_complementos,
                "dte:Complemento",
                {
                    "IDComplemento": "1",
                    "NombreComplemento": "EXPORTACION",
                    "URIComplemento": "http://www.sat.gob.gt/face2/ComplementoExportaciones/0.1.0",
                },
            )
            cex_exportacion = ET.SubElement(
                complemento_exportacion,
                "cex:Exportacion",
                {
                    "xmlns:cex": "http://www.sat.gob.gt/face2/ComplementoExportaciones/0.1.0",
                    "Version": "1",
                },
            )
            nombre_consignatario = ET.SubElement(
                cex_exportacion, "cex:NombreConsignatarioODestinatario"
            ).text = f"{factura.nombre_consignatario}"
            direccion_consignatario = ET.SubElement(
                cex_exportacion, "cex:DireccionConsignatarioODestinatario"
            ).text = f"{factura.direccion_consignatario}"
            if factura.codigo_consignatario:
                codigo_consignatario = ET.SubElement(
                    cex_exportacion, "cex:CodigoConsignatarioODestinatario"
                ).text = f"{factura.codigo_consignatario}"
            if factura.nombre_comprador:
                nombre_comprador = ET.SubElement(
                    cex_exportacion, "cex:NombreComprador"
                ).text = f"{factura.nombre_comprador}"
            if factura.direccion_comprador:
                direccion_comprador = ET.SubElement(
                    cex_exportacion, "cex:DireccionComprador"
                ).text = f"{factura.direccion_comprador}"
            if factura.codigo_comprador:
                codigo_comprador = ET.SubElement(
                    cex_exportacion, "cex:CodigoComprador"
                ).text = f"{factura.codigo_comprador}"
            otra_referencia = ET.SubElement(cex_exportacion, "cex:OtraReferencia").text = (
                f"{factura.referencia}"
            )
            if factura.invoice_incoterm_id:
                cex_incoterm = ET.SubElement(cex_exportacion, "cex:INCOTERM").text = (
                    f"{factura.invoice_incoterm_id.code}"
                )
            nombre_exportador = ET.SubElement(cex_exportacion, "cex:NombreExportador").text = (
                f"{factura.company_id.razon_social}"
            )
            codigo_exportador = ET.SubElement(cex_exportacion, "cex:CodigoExportador").text = (
                f"{factura.company_id.codigo_exportador}"
            )

        tree = ET.ElementTree(root)
        return tree
