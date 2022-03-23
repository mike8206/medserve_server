from flask import Blueprint, render_template, request, flash, redirect, url_for
from . import db
from .models import Case, MyCaseList
from flask_login import login_required, current_user
from datetime import datetime
import requests

func_list = Blueprint('func_list', __name__)

@func_list.route('/list', methods=['GET','POST'])
@login_required
def list():
    search_result = False
    cases=[]
    if request.method == 'POST':
        if request.form['btname'] == 'listRedcap':
            r = redcaplist()
            status = request_code(r.status_code)
            if status == '查詢成功':
                cases = r.json()
                Case.query.delete()
                db.session.commit()
                for c in cases:
                    redcap_id=c['patient_id']
                    name=c['name']
                    sex=c['sex']
                    birthday=c['birthday']
                    age=c['age']
                    location=c['location']
                    try:
                        birthday=datetime.strptime(c['birthday'], "%Y-%m-%d")
                    except ValueError:
                        birthday=None
                    case = Case.query.filter_by(redcap_id=redcap_id).first()
                    if case:
                        case.name=name
                        case.sex=sex
                        case.birthday=birthday
                        case.age=age
                        case.location=location
                        db.session.commit()
                    else:
                        new_case = Case(redcap_id=redcap_id, name=name, birthday=birthday, sex=sex, age=age, location=location)
                        db.session.add(new_case)
                        db.session.commit()
                cases = Case.query.all()
                flash("同步成功", category='success')
                search_result = True
            else:
                flash(status, category='error')
        elif request.form['btname'] == 'myList':
            try:
                r = MyCaseList.query.filter(MyCaseList.user_id==current_user.id).first().list
            except AttributeError:
                r=[]
            if r==[]:
                search_result = False
                flash('我的病人清單是空的!!', category='error')
                return redirect(url_for('func_list.list'))
            else:
                cases = Case.query.filter(Case.redcap_id.in_(r)).all()
                search_result = True
                flash("成功匯入我的病人清單", category='success')
        elif request.form['btname'] == 'saveMyList':
            lists = request.form.getlist('checkcase')
            if lists==[]:
                flash('未選取個案!!', category='error')
                return redirect(url_for('func_list.list'))
            else:
                l = MyCaseList.query.filter(MyCaseList.user_id==current_user.id).first()
                if l:
                    l.list = lists
                    db.session.commit()
                    flash('我的清單已成功更新!', category='success')
                else:
                    new_list = MyCaseList(list=lists, user_id=current_user.id)
                    db.session.add(new_list)
                    db.session.commit()
                    flash('已新增個案到我的清單!', category='success')
        else:
            form = request.form
            search_result = searchfunc(form)
            if search_result[0]==True:
                cases = search_result[1]
                flash('查詢成功!',category='success')
            else:
                flash('查無個案資料!!', category='error')
                return redirect(url_for('func_list.list'))
    return render_template("/cases/list.html", user=current_user,search_result=search_result,cases=cases)

def redcaplist():
    data = {
    'token': current_user.token,
    'content': 'record',
    'action': 'export',
    'format': 'json',
    'type': 'flat',
    'csvDelimiter': '',
    'fields[0]': 'patient_id',
    'fields[1]': 'name',
    'fields[2]': 'sex',
    'fields[3]': 'birthday',
    'fields[4]': 'age',
    'fields[5]': 'location',
    'rawOrLabel': 'label',
    'rawOrLabelHeaders': 'label',
    'exportCheckboxLabel': 'false',
    'exportSurveyFields': 'false',
    'exportDataAccessGroups': 'false',
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

def searchfunc(form):
    cases=[]
    filterList = []
    search_caseName = request.form['search_caseName']
    search_caseGender = request.form['search_caseGender']
    search_Area = request.form['search_Area']
    search_location = request.form['search_location']
    if search_caseName:
        search_caseName=str(search_caseName)
        filterList.append(Case.name.like('%'+search_caseName+'%'))
    if search_caseGender:
        search_caseGender=str(search_caseGender)
        filterList.append(Case.sex==search_caseGender)
    if search_Area:
        filterList.append(Case.location.like('%'+search_Area+'%'))
    if search_location:
        filterList.append(Case.location.like('%'+search_location+'%'))
    cases = Case.query.filter(*filterList).order_by(Case.location).all()
    if cases==[]:
        search_status = False
    else:
        search_status = True
    return (search_status, cases)
