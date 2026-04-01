


{
    'name': 'Expansion Reporte Liquidaciones',
    'version': '1.0',
    'summary': 'Anade nuevos campos al reporte de liquidaciones',

    'depends': [
        'settlement_expenses','account'
    ],
   
    'data': [
        'report/_inherit_settlement.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
