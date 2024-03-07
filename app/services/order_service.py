from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from ..models import Order,Customer, db
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
                        [(func.length(Order.fish_size) == 0, Customer.fish_size),
                        (func.length(Customer.fish_size) == 0, Order.fish_size)],
                        else_=func.coalesce(Order.fish_size, Customer.fish_size)
                    ).label("fish_size")
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
                }
                return order_dict
        except SQLAlchemyError as e:
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def add_order(data):
        try:
            new_order = Order(
                customer=data['customer'],
                product=data['product'],
                price=float(data['price'])/1.14,  # Adjust the price as needed
                quantity=float(data['quantity']),
                fish_size=data.get('fishSize'),
                date=datetime.strptime(data.get('date'), '%Y-%m-%d').date()
            )
            db.session.add(new_order)
            db.session.commit()
            return {'status': 'success', 'message': 'Order added successfully'}
        except SQLAlchemyError as e:
            db.session.rollback()
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def update_order(order_id, data):
        try:
            order = Order.query.filter_by(id=order_id).first()
            if order:
                order.price = data['price']/1.14
                order.quantity = data['quantity']
                order.fish_size = data['fish_size']
                db.session.commit()
                return {'status': 'success', 'message': 'Order updated successfully'}
            else:
                return {'status': 'error', 'message': 'Order not found'}
        except SQLAlchemyError as e:
            db.session.rollback()
            return {'status': 'error', 'message': str(e)}

    @staticmethod
    def delete_order(order_id):
        try:
            order = Order.query.filter_by(id=order_id).first()
            if order:
                db.session.delete(order)
                db.session.commit()
                return {'status': 'success', 'message': 'Order deleted successfully'}
            else:
                return {'status': 'error', 'message': 'Order not found'}
        except SQLAlchemyError as e:
            db.session.rollback()
            return {'status': 'error', 'message': str(e)}
