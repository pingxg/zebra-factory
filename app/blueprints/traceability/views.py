from io import BytesIO
from datetime import datetime
from collections import OrderedDict
from types import SimpleNamespace

import pandas as pd
from flask import render_template, request, send_file, url_for
from sqlalchemy import String, and_, cast, or_

from ... import db
from ...models import Customer, Order, Weight
from ...utils.auth_decorators import roles_required
from . import traceability_bp


def _aggregate_rows_by_order(rows):
    grouped_rows = OrderedDict()

    for row in rows:
        if row.order_id not in grouped_rows:
            grouped_rows[row.order_id] = {
                "order_id": row.order_id,
                "order_date": row.order_date,
                "product": row.product,
                "ordered_quantity": row.ordered_quantity,
                "order_note": row.order_note,
                "customer_name": row.customer_name,
                "company": row.company,
                "phone": row.phone,
                "email": row.email,
                "priority": row.priority,
                "packing": row.packing,
                "weight_ids": [],
                "total_weight_quantity": 0,
                "batch_numbers": [],
                "latest_production_time": None,
            }

        grouped = grouped_rows[row.order_id]

        if row.weight_id is not None:
            grouped["weight_ids"].append(str(row.weight_id))
        if row.weight_quantity is not None:
            grouped["total_weight_quantity"] += row.weight_quantity
        if row.batch_number:
            batch = row.batch_number.upper()
            if batch not in grouped["batch_numbers"]:
                grouped["batch_numbers"].append(batch)
        if row.production_time and (
            grouped["latest_production_time"] is None
            or row.production_time > grouped["latest_production_time"]
        ):
            grouped["latest_production_time"] = row.production_time

    aggregated = []
    for grouped in grouped_rows.values():
        weight_record_count = len(grouped["weight_ids"])
        grouped["weight_ids"] = ", ".join(grouped["weight_ids"])
        grouped["weight_record_count"] = weight_record_count
        grouped["batch_numbers"] = ", ".join(grouped["batch_numbers"])
        aggregated.append(SimpleNamespace(**grouped))

    return aggregated


def _build_filtered_query(args):
    keyword = (args.get("keyword") or "").strip()
    order_id = (args.get("order_id") or "").strip()
    batch_number = (args.get("batch_number") or "").strip().upper()
    customer = (args.get("customer") or "").strip()
    product = (args.get("product") or "").strip()
    phone = (args.get("phone") or "").strip()
    date_from = (args.get("date_from") or "").strip()
    date_to = (args.get("date_to") or "").strip()

    query = (
        db.session.query(
            Order.id.label("order_id"),
            Order.date.label("order_date"),
            Order.product.label("product"),
            Order.quantity.label("ordered_quantity"),
            Order.note.label("order_note"),
            Customer.customer.label("customer_name"),
            Customer.company.label("company"),
            Customer.phone.label("phone"),
            Customer.email.label("email"),
            Customer.priority.label("priority"),
            Customer.packing.label("packing"),
            Weight.id.label("weight_id"),
            Weight.quantity.label("weight_quantity"),
            Weight.batch_number.label("batch_number"),
            Weight.production_time.label("production_time"),
        )
        .outerjoin(Customer, Order.customer == Customer.customer)
        .outerjoin(Weight, Order.id == Weight.order_id)
    )

    filters = []
    if keyword:
        keyword_like = f"%{keyword}%"
        filters.append(
            or_(
                cast(Order.id, String).ilike(keyword_like),
                cast(Weight.id, String).ilike(keyword_like),
                Order.customer.ilike(keyword_like),
                Order.product.ilike(keyword_like),
                Customer.company.ilike(keyword_like),
                Customer.phone.ilike(keyword_like),
                Customer.email.ilike(keyword_like),
                Weight.batch_number.ilike(keyword_like),
            )
        )

    if order_id:
        if order_id.isdigit():
            filters.append(Order.id == int(order_id))
        else:
            filters.append(Order.id == -1)

    if batch_number:
        filters.append(Weight.batch_number.ilike(f"%{batch_number}%"))

    if customer:
        customer_like = f"%{customer}%"
        filters.append(
            or_(Order.customer.ilike(customer_like), Customer.company.ilike(customer_like))
        )

    if product:
        filters.append(Order.product.ilike(f"%{product}%"))

    if phone:
        filters.append(Customer.phone.ilike(f"%{phone}%"))

    if date_from:
        filters.append(Order.date >= date_from)
    if date_to:
        filters.append(Order.date <= date_to)

    if filters:
        query = query.filter(and_(*filters))

    return query.order_by(
        Order.date.desc(), Order.id.desc(), Weight.production_time.desc()
    )


@traceability_bp.route("/", methods=["GET"])
@roles_required("admin")
def index():
    searched = request.args.get("searched") == "1"
    per_page = request.args.get("per_page", "50")
    page = request.args.get("page", "1")

    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 50
    per_page = min(max(per_page, 10), 200)

    try:
        page = int(page)
    except ValueError:
        page = 1
    page = max(page, 1)

    rows = []
    total_records = 0
    total_pages = 0
    prev_url = None
    next_url = None
    page_links = []
    start_record = 0
    end_record = 0

    filters = request.args.to_dict()
    filters["per_page"] = str(per_page)

    if searched:
        base_query = _build_filtered_query(request.args)
        aggregated_rows = _aggregate_rows_by_order(base_query.all())

        total_records = len(aggregated_rows)
        total_pages = max(1, (total_records + per_page - 1) // per_page) if total_records else 1
        page = min(page, total_pages)

        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        rows = aggregated_rows[start_idx:end_idx]
        if total_records:
            start_record = (page - 1) * per_page + 1
            end_record = min(page * per_page, total_records)

        base_params = {
            k: v
            for k, v in filters.items()
            if k != "page" and v is not None and str(v).strip() != ""
        }

        visible_start = max(1, page - 2)
        visible_end = min(total_pages, page + 2)
        page_links = [
            {
                "number": page_number,
                "url": url_for("traceability.index", **base_params, page=page_number),
                "is_current": page_number == page,
            }
            for page_number in range(visible_start, visible_end + 1)
        ]

        if page > 1:
            prev_url = url_for("traceability.index", **base_params, page=page - 1)
        if page < total_pages:
            next_url = url_for("traceability.index", **base_params, page=page + 1)

    return render_template(
        "traceability/index.html",
        rows=rows,
        filters=filters,
        searched=searched,
        page=page,
        per_page=per_page,
        total_records=total_records,
        total_pages=total_pages,
        prev_url=prev_url,
        next_url=next_url,
        page_links=page_links,
        start_record=start_record,
        end_record=end_record,
    )


@traceability_bp.route("/export", methods=["GET"])
@roles_required("admin")
def export():
    rows = []
    if request.args.get("searched") == "1":
        rows = _aggregate_rows_by_order(_build_filtered_query(request.args).all())

    data = []
    for row in rows:
        data.append(
            {
                "Order ID": row.order_id,
                "Order Date": row.order_date,
                "Customer Name": row.customer_name,
                "Company": row.company,
                "Phone": row.phone,
                "Email": row.email,
                "Priority": row.priority,
                "Packing": row.packing,
                "Product": row.product,
                "Ordered Quantity (kg)": row.ordered_quantity,
                "Weight Record Count": row.weight_record_count,
                "Weight IDs": row.weight_ids,
                "Total Weight Quantity (kg)": row.total_weight_quantity,
                "Batch Numbers": row.batch_numbers,
                "Latest Production Time": row.latest_production_time,
                "Order Note": row.order_note,
            }
        )

    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Traceability")
    output.seek(0)

    file_name = f"traceability_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(
        output,
        as_attachment=True,
        download_name=file_name,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
