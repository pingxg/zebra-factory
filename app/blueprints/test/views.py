from flask import render_template, request
from flask_login import login_required
from . import test_bp
from datetime import date, datetime, timedelta
from ...models import Customer, Order, Weight, Product, MaterialInfo
from sqlalchemy import func, case
from ... import db
from collections import defaultdict
import os
import numpy as np
from ...utils.helper import calculate_salmon_box



@test_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():

    # selected_date = request.form.get('selected_date') or request.args.get('selected_date', (datetime.today() + timedelta(days=1)).date())
    selected_date_str = request.form.get('selected_date') or request.args.get('selected_date')
    if selected_date_str:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    else:
        # Default to tomorrow's date if none is provided
        selected_date = (datetime.today() + timedelta(days=1)).date()

    # Check if prev_date or next_date buttons were clicked
    if 'prev_date' in request.form:
        selected_date -= timedelta(days=1)
    elif 'next_date' in request.form:
        selected_date += timedelta(days=1)

    if selected_date:
        order_details = (
            db.session.query(
                Order.id,
                Order.customer, 
                Order.date, 
                Order.product,
                (func.coalesce(Order.price * 1.14, 0)).label("price"),
                Order.quantity,
                (func.coalesce(func.sum(Weight.quantity), 0)).label("total_produced"),
                Customer.priority,
                Customer.packing,
                Product.product_type,
                case(
                    [(func.length(Order.fish_size) == 0, Customer.fish_size),  # If Order.fish_size is empty, use Customer.fish_size
                    (func.length(Customer.fish_size) == 0, Order.fish_size)],  # If Customer.fish_size is empty, use Order.fish_size
                    else_=func.coalesce(Order.fish_size, Customer.fish_size)
                ).label("fish_size")
            )
            .outerjoin(Product, Order.product == Product.product_name)
            .outerjoin(Weight, Order.id == Weight.order_id)
            .filter(Order.date == selected_date)
            .group_by(Order.id)
            .outerjoin(Customer, Order.customer == Customer.customer)
            .order_by(Customer.priority.asc(), Customer.packing.asc(), Order.product.asc(), "fish_size")
            .all()
        )
        grouped_orders = {}
        totals = {}  # Dictionary to store the total for each product group
        details = {}
        for order in order_details:
            if order[9] not in grouped_orders:
                grouped_orders[order[9]] = {}
            if f'Priority {order[7]}' not in grouped_orders[order[9]]:
                grouped_orders[order[9]][f'Priority {order[7]}'] = []
            grouped_orders[order[9]][f'Priority {order[7]}'].append(order)

            if order[3] not in totals:
                totals[order[3]] = []
                totals[order[3]].append(0)
                totals[order[3]].append(0)
            totals[order[3]][0] += (order[5])
            totals[order[3]][1] += (order[6])

        
            if order[9] == 'Lohi':

                key_name = f'{order[8]} | {order[3]} | {order[10]}'
                if key_name not in details.keys():
                    details[key_name] = np.array([[0, 0], [0, 0]])
                box_info_total = np.array(calculate_salmon_box(order[5]))
                # print(key_name, box_info_total)
                # else:
                #     details[key_name] = details[key_name] + np.array([box_info_total, [0, 0]])

                if float(order[6]) < float(order[5])*float(os.environ.get('COMPLETION_THRESHOLD', 0.9)):
                    box_info_unfinished = np.array(calculate_salmon_box(float(order[5])))
                    details[key_name] = details[key_name] + np.vstack([box_info_total, box_info_unfinished])
                else:
                    details[key_name] = details[key_name] + np.vstack([box_info_total, [0, 0]])

        totals = {key: totals[key] for key in sorted(totals)}
        details = {key: details[key] for key in sorted(details)}
        # print(details)
        # Preprocess data
        grouped_details = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        for key, value in details.items():
            box_type, product_type, size = key.split(' | ')
            grouped_details[box_type][product_type][size] = value.tolist()

        # Flatten the structure and calculate row spans
        data_for_template = []
        category_rowspan_tracker = {}

        # Iterate through categories and subcategories
        for category, subcategories in grouped_details.items():
            category_rowspan = sum(len(items) for items in subcategories.values())
            category_rowspan_tracker[category] = category_rowspan
            for subcategory, items in subcategories.items():
                subcategory_rowspan = len(items)
                category_subcategory_unique = f"{category}_{subcategory}"
                for item, values in items.items():
                    row = {
                        "category": category,
                        "subcategory": subcategory,
                        "item": item,
                        "full_total": values[0][0],
                        "half_total": values[0][1],
                        "full_unfinished": values[1][0],
                        "half_unfinished": values[1][1],
                        "merge_info": {
                            "category_rowspan": category_rowspan_tracker.get(category, 0),
                            "subcategory_rowspan": subcategory_rowspan,
                            "category_subcategory_unique": category_subcategory_unique
                        }
                    }
                    # Append row to data list
                    data_for_template.append(row)
                # After processing the first item of a subcategory, subsequent items should not repeat the subcategory name
                subcategory_rowspan = 0
            # Reset category rowspan tracker for this category after processing
            category_rowspan_tracker[category] = 0
        grouped_orders = {k: v for k, v in sorted(grouped_orders.items())}

    return render_template('main/index.html', grouped_orders=grouped_orders, selected_date=selected_date, totals=totals, grouped_details=grouped_details, data_for_template=data_for_template, timedelta=timedelta)