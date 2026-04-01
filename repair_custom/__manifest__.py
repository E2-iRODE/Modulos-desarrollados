{
    'name': 'Compatibilidad Repuestos',
    'version': '1.0',
    'summary': 'Módulo para gestionar la compatibilidad de repuestos en Odoo',
    'category': 'Inventory, repairs',
    'license': 'GPL-3',
    
'depends': ['base', 'product', 'repair'],


    'data': [
        
        'views/producto_view.xml',
        'views/reparacion_view.xml',
        'security/ir.model.access.csv',
        'views/menu.xml'
        
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
