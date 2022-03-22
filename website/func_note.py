from flask import Blueprint, render_template, request, flash, jsonify, send_file
from .models import Note
from . import db
from flask_login import login_required, current_user
import json
import csv

func_note = Blueprint('func_note', __name__)

@func_note.route('/note', methods=['GET', 'POST'])
@login_required
def note():
    if request.method == 'POST':
        if request.form['btname'] == 'addNote':
            note = request.form.get('note')
            if len(note) < 1:
                flash('筆記不能為空白!', category='error')
            else:
                new_note = Note(data=note, user_id=current_user.id)
                db.session.add(new_note)
                db.session.commit()
                flash('已新增筆記!', category='success')
        else:
            notes = Note.query.filter(Note.user_id==current_user.id).all()
            filename = current_user.userName + '_Note.csv'
            with open('note.csv', 'w', newline='') as csvfile:
                csvwriter = csv.writer(csvfile, delimiter=',')
                for note in notes:
                    csvwriter.writerow([note.date,note.data])
            return send_file('../note.csv',mimetype='text/csv', attachment_filename=filename, as_attachment=True)
    return render_template("/users/note.html", user=current_user)

@func_note.route('/delete-note', methods=['POST'])
@login_required
def deleteNote():
    data = json.loads(request.data)
    noteId = data['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()
            flash('已刪除筆記!', category='error')
    return jsonify({})