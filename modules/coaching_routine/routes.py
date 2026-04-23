from flask import render_template, request, redirect, url_for, flash
from . import coaching_routine_bp
from .services import *

@coaching_routine_bp.route('/coaching-routine')
def routine_list():
    routines = get_all_routines()
    return render_template('coaching_routine/routine_list.html', routines=routines)


@coaching_routine_bp.route('/coaching-routine/create', methods=['GET', 'POST'])
def routine_create():
    if request.method == 'POST':
        data = {
            'routine_name': request.form['routine_name'],
            'subject': request.form['subject'],
            'coach_name': request.form['coach_name'],
            'days': request.form['days'],
            'start_time': request.form['start_time'],
            'end_time': request.form['end_time'],
            'location': request.form['location'],
            'target_group': request.form['target_group']
        }
        create_routine(data)
        flash('Coaching Routine Created', 'success')
        return redirect(url_for('coaching_routine.routine_list'))

    return render_template('coaching_routine/routine_form.html')
