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
        batch_number = request.form['batch_number']
        # try:
        #     batch_number = int(batch_number)
        # except ValueError:
        #     flash('Batch number not specified! Using the previous batch number.', 'info')
        #     batch_number = (
        #         db.session.query(
        #             MaterialInfo.batch_number, 
        #         )
        #         .order_by(MaterialInfo.date.desc())
        #         .first()
        #     )

        weight = Weight(
            order_id=order_id, 
            quantity=scale_reading, 
            production_time=datetime.now(pytz.timezone(os.environ.get('TIMEZONE'))),
            # batch_number=batch_number
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
        edit_val = data.get('edit_weight')
        if edit_val is None:
            flash('No edit value provided!', 'error')
            return jsonify(success=False, error="No edit value provided"), 400

        try:
            edit_val = float(edit_val)  # Adjust according to your data type
            weight.quantity = edit_val
            db.session.commit()
            flash('Weight updated successfully!', 'success')
            return jsonify(success=True)
        except ValueError:
            flash('Invalid value for weight.', 'error')
            return jsonify(success=False, error="Invalid value provided"), 400
        except Exception as e:
            flash('An error occurred while updating the weight.', 'error')
            db.session.rollback()  # Rollback in case of any error
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