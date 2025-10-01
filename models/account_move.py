from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class AccountMove(models.Model):
    _inherit = "account.move"
    _description = "Modulo de facturación electrónica por Swift Solutions."

    facturacion_electronica_activa = fields.Boolean(
        related="journal_id.facturacion_activa", store=True
    )
    numero_autorizacion = fields.Char(string="Número de autorización", copy=False)
    serie = fields.Char(string="Número de serie", copy=False)
    numero_dte = fields.Char(string="Número de DTE", copy=False)
    numero_acceso = fields.Char(string="Número de acceso", copy=False)
    fecha_emision = fields.Datetime(
        string="Fecha y hora de emisión", readonly=True, copy=False
    )
    fecha_certificacion = fields.Datetime(
        string="Fecha y hora de certificación", readonly=True, copy=False
    )
    certificada = fields.Boolean(default=False, copy=False)
    certificacion_error = fields.Boolean(default=False, copy=False)
    xml_generado = fields.Char(string="XML Generado", readonly=True, copy=False)
    xml_certificado = fields.Char(string="XML Certificado", readonly=True, copy=False)
    json_temporal = fields.Char(string="XML con errores", readonly=True, copy=False)
    numero_anulacion = fields.Char(string="Número de anulación", readonly=True, copy=False)
    anulacion_serie = fields.Char(
        string="Número de serie de anulación", readonly=True, copy=False
    )
    numero_dte_anulado = fields.Char(
        string="Número de DTE de anulación", readonly=True, copy=False
    )
    numero_acceso_anulacion = fields.Char(
        string="Número de acceso de anulación", readonly=True, copy=False
    )
    fecha_anulacion = fields.Datetime(string="Fecha de anulación", readonly=True, copy=False)
    xml_cancelado_generado = fields.Char(
        string="XML cancelado generado", readonly=True, copy=False
    )
    xml_cancelado_firmado = fields.Char(
        string="XML cancelado firmado", readonly=True, copy=False
    )
    xml_cancelado_certificado = fields.Char(
        string="XML cancelado certificado", readonly=True, copy=False
    )
    motivo_anulacion = fields.Char(
        string="Motivo de anulación",
        help="Si desea anular una factura, deberá indicar el motivo.",
        copy=False,
    )
    tipo_factura = fields.Selection(
        selection=[
            ("recibo", "Recibo"),
            ("fact_cambiaria", "Factura cambiaria"),
            ("fact_peque", "Factura pequeño contribuyente"),
            ("fact_peque_cam", "Factura cambiaria pequeño contribuyente"),
            ("recibo_donacion", "Recibo donación"),
            ("fact", "Factura"),
            ("impo_fact", "Factura de importación"),
            ("impo_taxless", "Factura de importación sin impuestos"),
            ("nota_abono", "Nota de abono"),
            ("nota_credito", "Nota de crédito"),
            ("nota_debito", "Nota de débito"),
            ("poliza", "Póliza"),
            ("fyduca", "Fyduca"),
            ("fauca", "FAUCA"),
            ("fact_elect", "Factura electrónica"),
            ("declaracion_aduanera", "Declaración aduanera"),
            ("form_sat", "Formulario SAT"),
            ("escritura_publica", "Escritura pública"),
            ("fact_elect_peque", "Factura electrónica pequeño contribuyente"),
            (
                "fact_reg_elec_peque",
                "Factura régimen electrónico pequeño contribuyente",
            ),
            (
                "fact_reg_esp_agrope",
                "Factura régimen especial contribuyente agropecuario",
            ),
            (
                "fact_reg_elect_esp_agrope",
                "Factura régimen electrónico especial contribuyente agropecuario",
            ),
            ("fesp", "Factura especial"),
            ("igss", "Recibo de planilla IGSS"),
        ],
        default=False,
        copy=False,
    )
    tipo_pago = fields.Selection(
        string="Método de pago",
        selection=[
            ("efectivo", "Efectivo"),
            ("cheque", "Cheque"),
            ("transferencia", "Transferencia"),
            ("tarjeta_credito", "Tarjeta de crédito"),
            ("deposito", "Depósito"),
        ],
        copy=False,
    )
    errores_fel_id = fields.One2many("errores.fel", "account_move_factuas_ids")
    partner_vat = fields.Char(string="NIT", related="partner_id.vat", store=True)
    tiene_nota_credito = fields.Boolean(default=False, compute="_compute_tiene_nota_credito")
    tiene_nota_debito = fields.Boolean(default=False, compute="_compute_tiene_nota_debito")
    establecimiento_id = fields.Many2one(
        comodel_name="establecimientos", string="Establecimiento"
    )

    def _correlativo_mas_grande(self, facturas):
        if not facturas:
            return 0

        correlativos = [int(factura.split("/")[-1]) for factura in facturas]

        return max(correlativos)

    def _post(self, soft=True):
        for move in self:
            if not move.journal_id.facturacion_activa:
                move.certificacion_error = False

            if "es_nota_abono" in self._fields:
                if move.es_nota_abono and not move.journal_id.facturacion_activa:
                    for line in move.invoice_line_ids:
                        if any(line.tax_ids):
                            raise ValidationError(
                                "Una nota de abono no debe incluir impuestos."
                            )

        facturas_especiales = self.filtered(lambda factura: factura.factura_especial)
        for factura_especial in facturas_especiales:
            if not factura_especial.journal_id.facturas_especiales:
                raise ValidationError(
                    "El diario no está configurado para trabajar con facturas especiales"
                )

        move_types = ["fact", "fact_cambiaria", "fact_exportacion", "out_refund"]
        por_certificar = self.filtered(
            lambda factura: factura.journal_id.facturacion_activa
            and (
                factura.tipo_factura in move_types
                or factura.factura_especial
                or not factura.tipo_factura
            )
            and not factura.certificada
        )

        for factura in por_certificar:
            proveedor_certificacion = factura.company_id.proveedor

            if proveedor_certificacion == "none" or not proveedor_certificacion:
                raise ValidationError(
                    "No hay un certificador configurado en la información de la empresa."
                )
            certificador = self.env[f"{proveedor_certificacion}"]
            certificador.get_certificacion(factura)

        continuar_movimientos = self.filtered(lambda fact: not fact.certificacion_error)

        return super(AccountMove, continuar_movimientos)._post(soft)

    def boton_anular(self):
        for factura in self:
            if factura.state == "posted" and not factura.motivo_anulacion:
                return {
                    "type": "ir.actions.act_window",
                    "res_model": "wizard.anular.factura",
                    "view_mode": "form",
                    "target": "new",
                    "context": {"default_factura_id": factura.id},
                }
            else:
                factura.procesar_anulacion()

    def procesar_anulacion(self):
        if not self.facturacion_electronica_activa and not self.xml_certificado:
            self.mapped("line_ids").remove_move_reconcile()
            self.write({"state": "cancel", "is_move_sent": False})
            return

        for factura in self:
            if factura.state != "posted":
                raise UserError(
                    "El asiento contable debe estar publicado para poder anularlo."
                )

            if not factura.motivo_anulacion:
                raise UserError(
                    "Debe indicar el motivo por el cual desea anular esta factura."
                )

            proveedor_certificacion = self.company_id.proveedor
            if proveedor_certificacion == "none" or not proveedor_certificacion:
                raise ValidationError(
                    "No hay un certificador configurado en la información de la empresa."
                )

            certificador = self.env[f"{proveedor_certificacion}"]
            certificador.get_certificacion(factura, es_anulacion=True)

            self.mapped("line_ids").remove_move_reconcile()
            self.write({"state": "cancel", "is_move_sent": False})

    def forzar_cancelacion(self):
        self.mapped("line_ids").remove_move_reconcile()
        self.write({"state": "cancel", "is_move_sent": False})

    def forzar_activacion(self):
        self.write({"state": "posted", "is_move_sent": True})

    @api.depends("partner_id")
    def _compute_tiene_nota_credito(self):
        for factura in self:
            notas_credito = self.env["account.move"].search(
                [
                    ("reversed_entry_id", "=", factura.id),
                    ("move_type", "=", "out_refund"),
                    ("state", "=", "posted"),
                ],
                limit=1,
            )

            if notas_credito:
                factura.tiene_nota_credito = True
            else:
                factura.tiene_nota_credito = False

    @api.depends("partner_id")
    def _compute_tiene_nota_debito(self):
        for factura in self:
            notas_debito = self.env["account.move"].search(
                [
                    ("debit_origin_id", "=", factura.id),
                    ("move_type", "=", "out_invoice"),
                    ("state", "=", "posted"),
                ],
                limit=1,
            )

            if notas_debito:
                factura.tiene_nota_debito = True
            else:
                factura.tiene_nota_debito = False
