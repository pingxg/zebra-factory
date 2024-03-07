import logging
from flask import Blueprint, request, jsonify, redirect, url_for, session, render_template
from flask_login import login_required
from ... import db, socketio
from ...models import Weight, MaterialInfo
from . import weight_bp
from ...utils.auth_decorators import permission_required
from datetime import date, datetime, timedelta
import pytz
import os


@weight_bp.route('/add/<int:order_id>', methods=['GET', 'POST'])
@permission_required('edit_weight')
def add(order_id):
    scale_reading = float(request.form['scale_reading'])
    batch_number = request.form['batch_number']
    try:
        batch_number = int(batch_number)
    except:
        print("Batch number not provided")
        batch_number = (
            db.session.query(
                MaterialInfo.batch_number, 
            )
            .order_by(MaterialInfo.date.desc())
            .first()
        )

    weight = Weight(
        order_id=order_id, 
        quantity=scale_reading, 
        production_time=datetime.now(pytz.timezone(os.environ.get('TIMEZONE'))),
        batch_number=batch_number
        )
    db.session.add(weight)
    db.session.commit()
    # session['show_toast'] = True
    return redirect(url_for('order.order_detail', order_id=order_id))



@weight_bp.route('/edit/<int:weight_id>', methods=['GET', 'POST'])
@permission_required('edit_weight')
def edit(weight_id):
    weight = Weight.query.filter_by(id=weight_id).first()
    
    if not weight:
        return jsonify(success=False, error="Weight not found"), 404

    if request.method == 'POST':
        edit_val = request.form.get('edit_weight')
        weight.quantity = edit_val
        db.session.commit()
        return jsonify(success=True)

@weight_bp.route('/delete/<int:weight_id>', methods=['POST'])
@permission_required('edit_weight')
def delete(weight_id):
    weight = Weight.query.filter_by(id=weight_id).first()
    if not weight:
        return "Weight not found", 404

    db.session.delete(weight)
    db.session.commit()

    return redirect(url_for('order.order_detail', order_id=weight.order_id))