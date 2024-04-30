from collections import defaultdict
from sqlalchemy import func
from ..models import Customer, Order, Weight
from .. import db


def get_data_for_pdf(date, customer=None):
    subquery = (
        db.session.query(
            Weight.order_id,
            func.coalesce(func.sum(Weight.quantity), 0).label("delivered")
        )
        .group_by(Weight.order_id)
        .subquery()
    )

    query = db.session.query(
        Order.customer.label("store"), 
        Customer.company.label("customer"),
        Customer.address,
        Customer.phone,
        Order.date,
        Customer.note,
        Customer.priority,
        Order.product,
        (func.coalesce(Order.price * 1.14, 0)).label("price"),
        Order.quantity.label("weight"),
        subquery.c.delivered,
    )\
    .outerjoin(subquery, Order.id == subquery.c.order_id) \
    .outerjoin(Customer, Order.customer == Customer.customer)\
    .filter(Order.date == date)\
    .order_by(Order.customer.asc(), Order.product.asc())

    # Apply customer filter if customer is provided
    if customer:
        query = query.filter(Customer.customer == customer)

    # Finalize the query
    data = query.all()

    store_dict = defaultdict(lambda: {
        'store': '',
        'customer': '',
        'address': '',
        'phone': '',
        'date': '',
        'note': '',
        'priority': '',
        'order_detail': [],
        'contain_frozen':False,
        'contain_lohi':False,
        'contain_other':False,
    })

    for order in data:
        store, customer, address, phone, date, note, priority, product, price, weight, delivered = order

        # Convert Decimal and datetime.date to a more friendly format if necessary
        price = float(price) if price is not None else 0.0
        weight = float(weight) if weight is not None else 0.0
        delivered = float(delivered) if delivered is not None else 0.0
        date = date.strftime('%Y-%m-%d')

        if store not in store_dict:
            store_dict[store].update({
                'store': store,
                'customer': customer,
                'address': address,
                'phone': phone,
                'date': date,
                'note': note,
                'priority': priority
            })

        store_dict[store]['order_detail'].append({
            'id': len(store_dict[store]['order_detail']) + 1,
            'product': product,
            'weight': str(round(weight,2)),
            'price': str(round(price,2)),
            'delivered': str(round(delivered,2))
        })
        if 'Frozen' in product:
            store_dict[store]['contain_frozen'] = True
        elif 'Frozen' not in product and 'Lohi' in product:
            store_dict[store]['contain_lohi'] = True
        elif 'Lohi' not in product:
            store_dict[store]['contain_other'] = True
    print(list(store_dict.values()))
    return list(store_dict.values())