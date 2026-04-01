

{
    'name': 'report_expansion_account',
    'version': '1.0',
    'summary': 'El modulo agrega la columna serial y numero de factura',
  
    'depends': [
       'account', 'account_reports',
    ],
   
    'data': [
        'data/data.xml'
        
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
