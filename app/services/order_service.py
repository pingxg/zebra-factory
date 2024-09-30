from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from ..models import Order, Customer, db
from sqlalchemy import func, case


class OrderService:
    @staticmethod
    def get_order(order_id):
        try:
            order = (
                db.session.query(
                    Order.id,
                    Order.customer,
                    Order.date,
                    Order.product,
                    (func.coalesce(Order.price * 1.14, 0)).label("price"),
                    Order.quantity,
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
                .join(Customer, Order.customer == Customer.customer)
                .filter(Order.id == order_id)
                .first()
            )
            if order:
                # Manually mapping the selected columns to their values
                order_dict = {
                    "id": order.id,
                    "customer": order.customer,
                    "date": order.date.isoformat(),
                    "product": order.product,
                    "price": order.price,
                    "quantity": order.quantity,
                    "fish_size": order.fish_size,
                    "original_price": order.price,
                    "original_quantity": order.quantity,
                    "original_fish_size": order.fish_size,
                    "note": order.note,
                }
                return order_dict
            else:
                return {"status": "error", "message": "Order not found"}
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"status": "error", "message": "Failed to get order: " + str(e)}

    @staticmethod
    def add_order(order_data):
        try:
            existing_order = Order.query.filter_by(
                customer=order_data.get("customer"),
                product=order_data.get("product"),
                price=round(float(order_data.get("price")) / 1.14, 4),
                date=datetime.strptime(order_data.get("date"), "%Y-%m-%d").date(),
            ).first()

            if existing_order:
                existing_order.quantity = float(existing_order.quantity) + float(
                    order_data.get("quantity")
                )
                existing_order.fish_size = order_data.get("fishSize")
                db.session.commit()
                return {
                    "status": "success",
                    "message": "Order updated successfully",
                }, 200

            new_order = Order(
                customer=order_data.get("customer"),
                product=order_data.get("product"),
                price=round(float(order_data.get("price")) / 1.14, 4),
                quantity=float(order_data.get("quantity")),
                fish_size=order_data.get("fishSize"),
                date=datetime.strptime(order_data.get("date"), "%Y-%m-%d").date(),
                note=order_data.get("note"),
            )
            db.session.add(new_order)
            db.session.commit()
            return {
                "status": "success",
                "message": "Order added successfully",
            }, 201  # Created
        except IntegrityError as e:
            db.session.rollback()
            # Extract more specific error message from e.orig here if needed
            return {
                "status": "error",
                "message": "Failed to add order: Unique constraint violation",
            }, 400

    @staticmethod
    def update_order(order_id, data):
        try:
            order = Order.query.filter_by(id=order_id).first()
            if order:
                order.price = data["price"] / 1.14
                order.quantity = data["quantity"]
                order.fish_size = data["fish_size"]
                order.note = data["note"]
                db.session.commit()
                return {
                    "status": "success",
                    "message": "Order updated successfully",
                }, 200
            else:
                return {"status": "error", "message": "Order not found"}, 404
        except SQLAlchemyError as e:
            db.session.rollback()
            return {
                "status": "error",
                "message": "Failed to update order: " + str(e),
            }, 400

    @staticmethod
    def delete_order(order_id):
        try:
            order = Order.query.filter_by(id=order_id).first()
            if order:
                db.session.delete(order)
                db.session.commit()
                return {"status": "success", "message": "Order deleted successfully"}
            else:
                return {"status": "error", "message": "Order not found"}
        except SQLAlchemyError as e:
            db.session.rollback()
            return {"status": "error", "message": "Failed to delete order: " + str(e)}
