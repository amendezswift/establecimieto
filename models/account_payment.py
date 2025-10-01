from odoo import models, fields


class AccountPayment(models.Model):
    _inherit = "account.payment"

    num_cheque = fields.Char(string="Número de cheque", copy=False)
    tipo_conciliacion = fields.Selection(
        string="Tipo de conciliación",
        selection_add=[
            ("cobrar_clientes_locales", "Cuentas por cobrar clientes locales"),
            ("cobrar_clientes_exterior", "Cuentas por cobrar clientes del exterior"),
            (
                "relacionadas_locales_exterior",
                "Cuentas y documentos por cobrar relacionadas locales y del exterior",
            ),
            ("cobrar_socios", "Cuentas por cobrar a socios"),
            ("cobrar_empleados", "Cuentas por cobrar empleados"),
            ("anticipo_clientes", "Anticipo de clientes"),
            ("intereses_ganados", "Intereses ganados"),
            (
                "transferencia_entre_cuentas",
                "Transferencia de fondos entre cuentas bancarias",
            ),
            ("otros_ingresos", "Otros ingresos"),
            ("proveedores", "Proveedores"),
            ("gastos_operativos", "Gastos operativos"),
            ("pagos_anticipados", "Pagos anticipados"),
            ("pago_prestamos", "Pago a préstamos"),
            ("pago_dividendos", "Pago de dividendos"),
            ("por_pagar_socios", "Cuentas por pagar socios"),
            ("pagar_relacionadas_locales", "Cuentas por pagar relacionadas locales"),
            (
                "pagar_relacionadas_exterior",
                "Cuentas por pagar relacionadas del exterior",
            ),
            (
                "egreso_transferencia_fondos",
                "Egreso por transferencia de fondos entre cuentas bancarias",
            ),
            ("otros_egresos", "Otros egresos"),
        ],
        copy=False,
    )
