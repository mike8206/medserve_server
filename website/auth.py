from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from flask_login import login_user, login_required, logout_user, current_user

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        account = request.form.get('account')
        password = request.form.get('password')

        user = User.query.filter_by(account=account).first()
        if user:
            if check_password_hash(user.password, password):
                flash('登入成功!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('密碼錯誤!', category='error')
        else:
            flash('帳號不存在!', category='error')
    return render_template("/users/login.html", user=current_user)

@auth.route('/logout')
def logout():
    logout_user()
    flash('已成功登出!', category='success')
    return redirect(url_for('views.home'))

@auth.route('/initial')
def initial():
    user = User.query.filter_by(account="admin").first()
    if user:
        return redirect(url_for('views.home'))
    else:
        new_admin = User(account="admin", userName="管理員", email="abcd@text.com", group="admin", password=generate_password_hash("password", method='sha256'))
        db.session.add(new_admin)
        db.session.commit()
        flash('Default admin created! Please use admin/password to login!', category='success')
        return redirect(url_for('views.home'))

@auth.route('/sign-up', methods=['GET', 'POST'])
@login_required
def sign_up():
    if current_user.group == 'admin':
        if request.method == 'POST':
            if request.form['btname'] == 'addUser':
                account = request.form.get('account')
                userName = request.form.get('userName')
                email = request.form.get('email')
                group = request.form.get('group')
                token = request.form.get('token')
                password1 = request.form.get('password1')
                password2 = request.form.get('password2')
                user = User.query.filter_by(account=account).first()
                if user:
                    flash('帳號已被申請', category='error')
                elif len(account) <5:
                    flash('帳號必須超過5個字', category='error')
                elif len(email) < 4:
                    flash('電子信箱必須超過4個字', category='error')
                elif len(userName) < 2:
                    flash('姓名必須超過1個字', category='error')
                elif password1 != password2:
                    flash('確認密碼不相符', category='error')
                elif len(password1) < 7:
                    flash('密碼必須超過7個字', category='error')
                else:
                    new_user = User(account=account, userName=userName, email=email, 
                        group=group, token=token, password=generate_password_hash(password1, method='sha256'))
                    db.session.add(new_user)
                    db.session.commit()
                    login_user(new_user, remember=True)
                    flash('帳號已建立', category='success')
                    return redirect(url_for('views.home'))
            else:
                if current_user.token =='':
                    flash('帳號無Redcap Token!!', category='error')
                    return redirect(url_for('auth.edituser'))
                else:
                    r = importRedcapUser()
                    status = request_code(r.status_code)
                    if status == "查詢成功":
                        users=r.json()
                        for u in users:
                            account=u['username']
                            userName=u['lastname']+u['firstname']
                            email=u['email']
                            group="user"
                            if u['user_rights'] == 1:
                                group="admin"
                            token=''
                            password1="23123456"
                            user = User.query.filter_by(account=account).first()
                            if user:
                                continue
                            else:
                                new_user = User(account=account, userName=userName, email=email, 
                                group=group, token=token, password=generate_password_hash(password1, method='sha256'))
                                db.session.add(new_user)
                                db.session.commit()
                        flash('已從Redcap匯入帳號，預設密碼為23123456', category='success')
                        return redirect(url_for('auth.sign_up'))
                    else:
                        flash(status, category='error')
                        return redirect(url_for('auth.sign_up'))
    else:
        flash('帳號無此權限!', category='error')
        return redirect(url_for('views.home'))
    return render_template("/users/sign_up.html", user=current_user)

def importRedcapUser():
    import requests
    data = {
        'token': current_user.token,
        'content': 'user',
        'format': 'json',
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

@auth.route('/edituser', methods=['GET', 'POST'])
@login_required
def edituser():
    user=current_user
    if request.method == 'POST':
        if request.form['btname'] == 'alterusr':
            userName = request.form.get('userName')
            email = request.form.get('email')
            token = request.form.get('token')
            if len(userName)<2:
                flash('姓名必須超過1個字', category='error')
            elif len(email)<4:
                flash('電子信箱必須超過4個字', category='error')
            else:
                user.userName = userName
                user.email = email
                user.token = token
                db.session.commit()
                flash('個資已成功更新!', category='success')
                return redirect(url_for('auth.edituser'))
        else:
            password_old = request.form.get('password_old')
            password1 = request.form.get('password1')
            password2 = request.form.get('password2')
            if check_password_hash(user.password, password_old):
                if password1 != password2:
                    flash('確認密碼不相符', category='error')
                else:
                    password_new = generate_password_hash(password1, method='sha256')
                    user.password = password_new
                    db.session.commit()
                    flash('密碼已更新成功!!', category='success')
                    return redirect(url_for('auth.edituser'))
            else:    
                flash('舊密碼輸入錯誤!', category='error')
    return render_template("/users/edituser.html", user=current_user)