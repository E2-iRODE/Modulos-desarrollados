
{
    'name': 'POS Sale - Cuotas desde Orden de Venta',
    'version': '17.0.7.0.0',
    'summary': 'Calcula Gastos Administrativos en la orden de venta y no permite duplicar el recargo de la cuota en el pago con tarjeta',
    'category': 'Point of Sale',
    'author': 'Custom',
    'license': 'LGPL-3',
    'depends': [
        'point_of_sale',
        'pos_sale',
        'pay_methods_pos_v17',
    ],
    'data': [
        'views/order_sale_view.xml',
        
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_sale_installments/static/src/js/installments.js',
        ],
    },
    'installable': True,
    'application': False,
}
