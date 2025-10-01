from odoo import models, fields

import xml.etree.ElementTree as ET
from datetime import datetime
from dateutil import tz


class AnularFactura(models.TransientModel):
    _name = "anular.factura"

    def anular_factura(self, factura):
        # ETIQUETA RAIZ DEL XML
        root = ET.Element(
            "dte:GTAnulacionDocumento",
            {
                "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                "xmlns:ds": "http://www.w3.org/2000/09/xmldsig#",
                "Version": "0.1",
                "xmlns:dte": "http://www.sat.gob.gt/dte/fel/0.1.0",
            },
        )

        # INFORMACIÓN GENERAL DEL DOCUMENTO
        dte_sat = ET.SubElement(root, "dte:SAT")
        anulacion_dte = ET.SubElement(dte_sat, "dte:AnulacionDTE", {"ID": "DatosCertificados"})
        zona_horaria = tz.gettz(self.env.user.tz)
        fecha_emision_zh = fields.Datetime.context_timestamp(self, factura.fecha_emision)
        fecha_hora_documento = fecha_emision_zh.strftime("%Y-%m-%dT%H:%M:%S-06:00")
        fecha_generada = datetime.now(zona_horaria)
        fecha_anulacion = fecha_generada.strftime("%Y-%m-%dT%H:%M:%S-06:00")

        entorno_prueba_activo = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("fel.entorno_pruebas_%d" % self.env.company.id, default=False)
        )

        nit = (
            factura.company_id.nit_pruebas if entorno_prueba_activo else factura.company_id.vat
        )
        datos_generales = ET.SubElement(
            anulacion_dte,
            "dte:DatosGenerales",
            {
                "FechaEmisionDocumentoAnular": f"{fecha_hora_documento}",
                "FechaHoraAnulacion": f"{fecha_anulacion}",
                "ID": "DatosAnulacion",
                "IDReceptor": f"{factura.partner_id.vat}",
                "MotivoAnulacion": f"{factura.motivo_anulacion}",
                "NITEmisor": f"{nit}",
                "NumeroDocumentoAAnular": f"{factura.numero_autorizacion}",
            },
        )
        tree = ET.ElementTree(root)
        return tree
