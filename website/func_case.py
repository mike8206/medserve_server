from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import Case, MyCaseList
from . import db
from flask_login import login_required, current_user
from datetime import datetime
import json, requests

func_case = Blueprint('func_case', __name__)

@func_case.route('/newcase', methods=['GET', 'POST'])
@login_required
def newcase():
    date = datetime.today().strftime('%Y-%m-%d')
    if request.method == 'POST':
        if request.form['btname'] == 'newcase':            
            r = redcapNewNumber()
            patient_id = str(r.json())
            date_registered = datetime.today().strftime('%Y-%m-%d %H:%M')
            personal_info_recorder = str(current_user.userName)
            name = str(request.form.get('name'))
            sex = str(request.form.get('sex'))
            birthday = request.form.get('birthday')
            age = str(request.form.get('age'))
            location = request.form.get('location')
            address = str(request.form.get('address'))
            number_of_family_members = str(request.form.get('number_of_family_members'))
            key_person = str(request.form.get('key_person'))
            education_level = str(request.form.get('education_level'))
            occupation = str(request.form.get('occupation'))
            case = Case.query.filter_by(name=name, location=location).first()
            if case:
                flash('此姓名與地址已被登錄', category='error')
            elif len(name) < 2:
                flash('姓名必須超過1個字', category='error')
            else:
                record = {
                    'patient_id': patient_id,
                    'personal_info_recorder': personal_info_recorder,
                    'name': name,
                    'sex': sex,
                    'birthday': birthday,
                    'age': age,
                    'location': location,
                    'address': address,
                    'number_of_family_members': number_of_family_members,
                    'key_person': key_person,
                    'education_level': education_level,
                    'occupation': occupation,
                    'date_registered': date_registered,
                    'ddcd_54576c_complete': 2,
                }
                casedata = json.dumps([record]) 
                r = redcapnew(casedata)
                status = request_code(r.status_code)
                if status == '查詢成功':
                    new_case = Case(redcap_id=patient_id)
                    db.session.add(new_case)
                    db.session.commit()
                    flash('個案資料已建立', category='success')
                    return redirect(url_for('func_case.detail_var', caseID=patient_id))
                else:
                    flash(status, category='error')
    else:
        if current_user.token =='':
            flash('帳號無Redcap Token!!', category='error')
            return redirect(url_for('auth.edituser'))
        else:
            r = redcapNewNumber()
            status = request_code(r.status_code)
            if status != '查詢成功':
                flash(status, category='error')
                return redirect(url_for('auth.edituser'))
    return render_template("/cases/newcase.html", user=current_user, date=date)

def redcapNewNumber():
    data = {
        'token': current_user.token,
        'content': 'generateNextRecordName'
    }
    r = requests.post('https://redcap.mc.ntu.edu.tw/api/',data=data, verify=False)
    return r

def redcapnew(casedata):
    data = {
        'token': current_user.token,
        'content': 'record',
        'format': 'json',
        'type': 'flat',
        'overwriteBehavior': 'normal',
        'forceAutoNumber': 'true',
        'data': casedata,
        'returnFormat': 'json'
    }
    r = requests.post('https://redcap.mc.ntu.edu.tw/api/',data=data, verify=False)
    return r

def request_code(code):
  if code == 200:
    return("查詢成功")
  elif code == 400:
    return("查詢無效")
  elif code == 401:
    return("API 憑證遺失或錯誤")
  elif code == 403:
    return("無權限使用 API")
  elif code == 404:
    return("網址無效或不存在")
  elif code == 406:
    return("匯入資料格式錯誤")
  elif code == 500:
    return("RedCap伺服器錯誤")
  else:
    return("查詢方法無法執行")

@func_case.route('/detail')
@login_required
def detail():
    detail_display = False
    try:
        m = MyCaseList.query.filter(MyCaseList.user_id==current_user.id).first().list
    except AttributeError:
        m = []
    cases = Case.query.filter(Case.redcap_id.in_(m)).all()
    return render_template("/cases/detail.html", user=current_user, detail_display=detail_display,cases=cases)

@func_case.route('/detail/<caseID>', methods=['GET','POST'])
@login_required
def detail_var(caseID):
    detail_display = False
    try:
        m = MyCaseList.query.filter(MyCaseList.user_id==current_user.id).first().list
    except AttributeError:
        m = []
    cases = Case.query.filter(Case.redcap_id.in_(m)).all()
    if current_user.token =='':
        flash('帳號無Redcap Token!!', category='error')
        return redirect(url_for('auth.edituser'))
    else:
        r = redcapDetail(caseID)
        status = request_code(r.status_code)
        if status != '查詢成功':
            flash(status, category='error')
            return redirect(url_for('func_list.list'))
        else:
            detail_display = True
            case = r.json()
            if case:
                for c in case:
                    patient_id = c['patient_id']
                    name = str(c['name'])
                    sex = str(c['sex'])
                    birthday = c['birthday']
                    age = str(c['age'])
                    location = str(c['location'])
                try:
                    birthday=datetime.strptime(birthday, "%Y-%m-%d")
                except ValueError:
                    birthday=None
                case_update = Case.query.filter_by(redcap_id=patient_id).first()
                case_update.name=name
                case_update.sex=sex
                case_update.birthday=birthday
                case_update.age=age
                case_update.location=location
                db.session.commit()
                caselink = redcapLink(caseID)
            else:
                null_case = Case.query.filter_by(redcap_id=caseID).first()
                db.session.delete(null_case)
                db.session.commit()
                flash("查無個案", category='error')
                return redirect(url_for('func_list.list'))
    return render_template("/cases/detail.html", user=current_user, detail_display=detail_display, caseID=caseID, case=case,cases=cases, caselink=caselink)

def redcapDetail(caseID):
    data = {
    'token': current_user.token,
    'content': 'record',
    'action': 'export',
    'format': 'json',
    'type': 'flat',
    'csvDelimiter': '',
    'records[0]': caseID,
    'forms[0]': 'ddcd_54576c',
    'rawOrLabel': 'label',
    'rawOrLabelHeaders': 'label',
    'exportCheckboxLabel': 'false',
    'exportSurveyFields': 'false',
    'exportDataAccessGroups': 'false',
    'returnFormat': 'json'
    }
    r = requests.post('https://redcap.mc.ntu.edu.tw/api/',data=data, verify=False)
    return r

def redcapLink(caseID):
    token = current_user.token
    url = 'https://redcap.mc.ntu.edu.tw/api/'
    surveyQueueLink = {
    'token': token,
    'content': 'surveyQueueLink',
    'format': 'json',
    'record': caseID,
    'returnFormat': 'json'
    }
    surveyQueueLink = requests.post(url,data=surveyQueueLink, verify=False).text
    dict1 = {'surveyQueueLink':surveyQueueLink}
    return (dict1)
