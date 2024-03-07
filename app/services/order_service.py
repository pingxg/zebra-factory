from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from ..models import Order, db

class OrderService:
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
