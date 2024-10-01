from collections import defaultdict
import os
import boto3
from botocore.client import Config
from datetime import date, timedelta
from flask import render_template, request, jsonify, flash
from flask_login import login_required
from sqlalchemy import func, case
from . import order_bp
from ... import db
from ...models import Order, Weight, MaterialInfo, Customer, DeliveryNoteImage
from ...utils.date_utils import calculate_current_iso_week
from ...services.order_service import OrderService
from ...utils.auth_decorators import permission_required, roles_required
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


@order_bp.route("/", methods=["GET", "POST"])
@login_required
def order() -> str:
    week_str: str = request.args.get("week", calculate_current_iso_week())

    year, week = map(int, week_str.split("-W"))
    start_date: date = date.fromisocalendar(year, week, 1)
    end_date: date = start_date + timedelta(days=6)

    # Check if prev_week or next_week buttons were clicked
    if "prev_week" in request.args:
        start_date -= timedelta(weeks=1)
    elif "next_week" in request.args:
        start_date += timedelta(weeks=1)
    end_date = start_date + timedelta(days=6)

    # Update week_str to reflect the new week
    week_str = f"{start_date.year}-W{start_date.isocalendar()[1]:02d}"

    try:
        orders = (
            db.session.query(
                Order.id,
                Order.customer,
                Order.date,
                Order.product,
                (func.coalesce(Order.price * 1.14, 0)).label("price"),
                Order.quantity,
                (func.coalesce(func.sum(Weight.quantity), 0)).label("total_produced"),
            )
            .filter(Order.date.between(start_date, end_date))
            .outerjoin(Weight, Order.id == Weight.order_id)
            .order_by(Order.customer.asc(), Order.product.asc())
            .group_by(Order.id)
            .all()
        )

        # Organize orders by customer and date
        orders_by_customer = defaultdict(lambda: defaultdict(list))
        for order in orders:
            orders_by_customer[order.customer][order.date].append(order)

        # List of dates in the week for column headers
        week_dates = [start_date + timedelta(days=i) for i in range(7)]
        return render_template(
            "order/order.html",
            week_str=week_str,
            orders_by_customer=orders_by_customer,
            week_dates=week_dates,
        )
    except SQLAlchemyError as e:
        flash(f"An unexpected database error occurred: {str(e)}", "error")
        return "Database error", 500
    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}", "error")
        return "Unexpected error", 500


@order_bp.route("/<int:order_id>", methods=["GET", "POST"])
@roles_required("admin", "cutter", "driver")
def order_detail(order_id: int) -> str:
    try:
        order = (
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
                case(
                    (
                        func.length(Order.fish_size) == 0,
                        Customer.fish_size,
                    ),  # If Order.fish_size is empty, use Customer.fish_size
                    (
                        func.length(Customer.fish_size) == 0,
                        Order.fish_size,
                    ),  # If Customer.fish_size is empty, use Order.fish_size
                    else_=func.coalesce(Order.fish_size, Customer.fish_size),
                ).label("fish_size"),
                Order.note,
            )
            .outerjoin(Weight, Order.id == Weight.order_id)
            .filter(Order.id == order_id)
            .group_by(Order.id)
            .outerjoin(Customer, Order.customer == Customer.customer)
            .first()
        )

        weight_details = (
            db.session.query(Weight.id, Weight.quantity, Weight.production_time)
            .filter(Weight.order_id == order_id)
            .order_by(Weight.production_time.asc())
            .all()
        )

        # Fetch image details associated with the order
        images = (
            db.session.query(DeliveryNoteImage.id, DeliveryNoteImage.image_url)
            .filter(DeliveryNoteImage.order_id == order_id)
            .order_by(DeliveryNoteImage.uploaded_at.asc())
            .all()
        )

        if not order:
            flash("Order not found", "error")
            return "Order not found", 404

        s3 = boto3.client(
            "s3",
            config=Config(signature_version="s3v4"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION"),
        )
        bucket_name = os.getenv("AWS_S3_BUCKET_NAME")
        presigned_urls = []

        for image in images:
            presigned_url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket_name, "Key": image.image_url},
                ExpiresIn=3600,
            )  # URL expiration time in seconds
            presigned_urls.append(
                {"image_id": image.id, "presigned_url": presigned_url}
            )

        return render_template(
            "order/order_detail.html",
            order=order,
            weight_details=weight_details,
            image_details=presigned_urls,
        )
    except SQLAlchemyError as e:
        flash("Database error", "error")
        return "Database error", 500
    except Exception as e:
        flash(f"Unexpected error: {str(e)}", "error")
        return "Unexpected error", 500


@roles_required("admin")
@order_bp.route("/get/<int:order_id>", methods=["GET", "POST"])
def get_order(order_id: int) -> jsonify:
    if not order_id:
        return jsonify({"status": "error", "message": "Order ID not provided"}), 400

    try:
        result = OrderService.get_order(order_id)
        return jsonify(result)
    except Exception as e:
        flash(f"Unexpected error: {str(e)}", "error")
        return jsonify({"status": "error", "message": "Unexpected error"}), 500


@order_bp.route("/add", methods=["GET", "POST"])
@roles_required("admin")
def add_order() -> jsonify:
    data = request.json
    if not data:
        flash("No data provided. Please fill in the required fields.", "error")
        return jsonify({"status": "error", "message": "No data provided"}), 400
    try:
        result, status_code = OrderService.add_order(data)
        if status_code in (200, 201):
            flash("Order added successfully!", "success")
            return jsonify(result), status_code
        else:
            error_message = result.get(
                "message", "An error occurred while processing your request."
            )
            flash(error_message, "error")
            return jsonify(result), status_code

    except IntegrityError as e:
        flash(
            "A database integrity error occurred. Please check your data for duplicates or missing fields.",
            "error",
        )
        return jsonify({"status": "error", "message": "Database integrity error"}), 400
    except SQLAlchemyError as e:
        flash(f"An unexpected database error occurred: {str(e)}", "error")
        return jsonify({"status": "error", "message": "Database error"}), 500
    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}", "error")
        return jsonify({"status": "error", "message": "Unexpected error"}), 500


@order_bp.route("/update/<int:order_id>", methods=["POST"])
@roles_required("admin")
def update_order(order_id: int) -> jsonify:
    data = request.json
    if not data or not order_id:
        flash("No data provided or Order ID missing", "error")
        return (
            jsonify(
                {"status": "error", "message": "No data provided or Order ID missing"}
            ),
            400,
        )

    existing_order = Order.query.get(order_id)
    if not existing_order:
        flash("Order not found", "error")
        return jsonify({"status": "error", "message": "Order not found"}), 404

    try:
        result, status_code = OrderService.update_order(order_id, data)
        if result["status"] == "success":
            flash("Order updated successfully!", "success")
            return jsonify(result), status_code
        else:
            flash("Failed to update order", "error")
            return (
                jsonify({"status": "error", "message": "Failed to update order"}),
                status_code,
            )
    except IntegrityError as e:
        flash("Database integrity error", "error")
        return jsonify({"status": "error", "message": "Database integrity error"}), 400
    except SQLAlchemyError as e:
        flash("Database error", "error")
        return jsonify({"status": "error", "message": "Database error"}), 500
    except Exception as e:
        flash(f"Unexpected error: {str(e)}", "error")
        return jsonify({"status": "error", "message": "Unexpected error"}), 500


@order_bp.route("/delete/<int:order_id>", methods=["DELETE"])
@roles_required("admin")
def delete_order(order_id: int) -> jsonify:
    if not order_id:
        flash("Order ID not provided", "error")
        return jsonify({"status": "error", "message": "Order ID not provided"}), 400

    existing_order = Order.query.get(order_id)
    if not existing_order:
        flash("Order not found", "error")
        return jsonify({"status": "error", "message": "Order not found"}), 404

    try:
        result = OrderService.delete_order(order_id)
        if result["status"] == "success":
            flash("Order deleted successfully!", "success")
            return jsonify(result), 200
        else:
            flash("Failed to delete order due to business constraints", "error")
            return (
                jsonify({"status": "error", "message": "Failed to delete order"}),
                400,
            )
    except IntegrityError as e:
        flash(
            "Cannot delete this order because it is referenced by other items.", "error"
        )
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Database integrity error: cannot delete order",
                }
            ),
            400,
        )
    except SQLAlchemyError as e:
        flash("Database error during order deletion", "error")
        return jsonify({"status": "error", "message": "Database error"}), 500
    except Exception as e:
        flash(f"Unexpected error during deletion: {str(e)}", "error")
        return jsonify({"status": "error", "message": "Unexpected error"}), 500
