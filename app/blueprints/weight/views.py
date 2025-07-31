from flask import request, jsonify, redirect, url_for, flash
from ... import db
from ...models import Weight, MaterialInfo
from . import weight_bp
from ...utils.auth_decorators import roles_required
from datetime import datetime
import pytz
import os


@weight_bp.route('/add/<int:order_id>', methods=['GET', 'POST'])
@roles_required('admin', 'cutter')
def add(order_id):
    if request.method == 'POST':
        scale_reading = float(request.form['scale_reading'])

        # Get the batch number directly from the form as a string.
        # The try-except block is no longer needed as we now handle alphanumeric batch numbers.
        batch_number = request.form.get('batch_number')

        if not batch_number:
            flash('Batch number is missing!', 'error')
            return redirect(url_for('order.order_detail', order_id=order_id))

        weight = Weight(
            order_id=order_id,
            quantity=scale_reading,
            production_time=datetime.now(
                pytz.timezone(os.environ.get('TIMEZONE'))),
            batch_number=batch_number
        )
        db.session.add(weight)
        db.session.commit()
        flash('Weight added sucessfully!', 'success')
        return redirect(url_for('order.order_detail', order_id=order_id))

    return redirect(url_for('order.order_detail', order_id=order_id))


@weight_bp.route('/edit/<int:weight_id>', methods=['GET', 'POST'])
@roles_required('admin', 'cutter')
def edit(weight_id):
    weight = Weight.query.filter_by(id=weight_id).first()
    if not weight:
        flash('Weight record not found!', 'error')
        return jsonify(success=False, error="Weight not found"), 404

    if request.method == 'POST':
        data = request.get_json()
        edit_weight = data.get('edit_weight')
        edit_batch_number = data.get('edit_batch_number')

        if edit_weight is None and edit_batch_number is None:
            return jsonify(success=False, error="No new data provided."), 400

        try:
            if edit_weight is not None:
                weight.quantity = float(edit_weight)
            if edit_batch_number is not None:
                weight.batch_number = str(edit_batch_number)

            db.session.commit()
            flash('Record updated successfully!', 'success')
            return jsonify(success=True)
        except ValueError:
            flash('Invalid value for weight.', 'error')
            return jsonify(success=False, error="Invalid value for weight."), 400
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating the record.', 'error')
            return jsonify(success=False, error=str(e)), 500


@weight_bp.route('/delete/<int:weight_id>', methods=['POST'])
@roles_required('admin', 'cutter')
def delete(weight_id):
    weight = Weight.query.filter_by(id=weight_id).first()
    if not weight:
        return "Weight not found", 404

    db.session.delete(weight)
    db.session.commit()
    flash('Weight deleted sucessfully!', 'success')

    return redirect(url_for('order.order_detail', order_id=weight.order_id))
