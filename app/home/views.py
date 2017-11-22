#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @File    : views.py
# @author  : Jaxon
# @software: PyCharm
# @datetime: 9/26 026 下午 07:34


from app import db, app
from app.home import home
from app.home.forms import RegistForm, LoginForm, UserdetailForm, PwdForm, CommentForm
from app.models import User, Userlog, Preview, Tag, Movie, Comment, Moviecol
from flask import render_template, redirect, url_for, flash, session, request, abort
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import uuid, os, datetime


# 定义登录判断装饰器
def user_login_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # session不存在时请求登录
        if "user" not in session:
            return redirect(url_for("home.login", next=request.url))
        return f(*args, **kwargs)

    return decorated_function


# 修改文件名称
def change_filename(filename):
    fileinfo = os.path.splitext(filename)  # 对名字进行前后缀分离
    filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "_" + uuid.uuid4().hex + fileinfo[-1]  # 生成新文件名
    return filename


# 定义首页列表视图
@home.route("/")
def index():
    tags = Tag.query.all()
    # 通过url获取参数
    tid = request.args.get("tid", '')
    star = request.args.get("star", '')
    time = request.args.get("time", '')
    pm = request.args.get("pm", '')
    cm = request.args.get("cm", '')
    pg = request.args.get("pg", '')

    # 保存获取的参数
    p = dict(
        tid=tid,
        star=star,
        time=time,
        pm=pm,
        cm=cm
    )

    # 根据获取的参数查询数据
    page_data = Movie.query
    if tid.isdigit() and tid is not None:
        page_data = page_data.filter_by(tag_id=int(tid))
    if star.isdigit() and star is not None:
        page_data = page_data.filter_by(star=int(star))
    if time.isdigit() and time is not None:
        page_data = page_data.order_by(
            Movie.addtime.desc() if int(time) == 1 else Movie.addtime.asc()
        )
    if pm.isdigit() and pm is not None:
        page_data = page_data.order_by(
            Movie.playnum.desc() if int(pm) == 1 else Movie.playnum.asc()
        )
    if cm.isdigit() and cm is not None:
        page_data = page_data.order_by(
            Movie.commentnum.desc() if int(cm) == 1 else Movie.commentnum.asc()
        )

    # 分页处理
    pages = page_data.count() // app.config['PAGE_SET'] if page_data.count() % app.config[
        'PAGE_SET'] == 0 else page_data.count() // app.config['PAGE_SET'] + 1
    page = int(pg) if pg.isdigit() and pg is not None and int(pg) <= pages else 1
    page_data = page_data.paginate(page=page, per_page=app.config['PAGE_SET'])

    return render_template("home/index.html", tags=tags, p=p, page_data=page_data)


# 定义上映预告视图（首页动画）
@home.route("/animation/")
def animation():
    data = Preview.query.all()
    return render_template("home/animation.html", data=data)


# 定义电影搜索视图
@home.route("/search/")
def search():
    key = request.args.get("key", '')
    pg = request.args.get("pg", '')

    if key == '':
        abort(404)

    p = dict(key=key)

    # 模糊匹配
    page_data = Movie.query.filter(
        Movie.title.ilike('%' + key + '%')
    ).order_by(
        Movie.playnum.desc()
    )

    pages = page_data.count() // app.config['PAGE_SET'] if page_data.count() % app.config[
        'PAGE_SET'] == 0 else page_data.count() // app.config['PAGE_SET'] + 1
    page = int(pg) if pg.isdigit() and pg is not None and int(pg) <= pages else 1
    page_data = page_data.paginate(page=page, per_page=app.config['PAGE_SET'])

    return render_template("home/search.html", p=p, page_data=page_data)


# 定义电影详情视图
@home.route("/play/", methods=["GET", "POST"])
def play():
    form = CommentForm()
    mv = request.args.get("mv", '')
    pg = request.args.get("pg", '')

    p = dict(mv=mv)

    if not mv.isdigit() or mv is None:
        abort(404)

    movie = Movie.query.get_or_404(int(mv))
    # 提交评论
    if form.validate_on_submit():
        comment = Comment(
            content=form.data["content"],
            movie_id=int(mv),
            user_id=session["user_id"]
        )
        movie.commentnum += 1  # 增加评论数量
        db.session.add(comment)
        db.session.add(movie)
        db.session.commit()
        flash("评论提交成功！", "ok")

    # 增加播放数量
    movie.playnum += 1
    db.session.add(movie)
    db.session.commit()

    # 查询电影信息用于网页显示
    movie = Movie.query.join(Tag).filter(
        Movie.id == int(mv),
        Movie.tag_id == Tag.id
    ).first_or_404()

    # 查询评论数据
    page_data = Comment.query.join(User).filter(
        Comment.movie_id == int(mv),
        Comment.user_id == User.id
    ).order_by(
        Comment.addtime.desc()
    )
    # 分页显示
    pages = page_data.count() // app.config['PAGE_SET'] if page_data.count() % app.config[
        'PAGE_SET'] == 0 else page_data.count() // app.config['PAGE_SET'] + 1
    page = int(pg) if pg.isdigit() and pg is not None and int(pg) <= pages else 1
    page_data = page_data.paginate(page=page, per_page=app.config['PAGE_SET'])

    return render_template("home/play.html", p=p, form=form, movie=movie, page_data=page_data)


# 定义注册视图
@home.route("/regist/", methods=["GET", "POST"])
def regist():
    form = RegistForm()
    if form.validate_on_submit():
        data = form.data
        user = User(
            name=data["name"],
            pwd=generate_password_hash(data["pwd"]),
            email=data["email"],
            phone=data["phone"],
            uuid=uuid.uuid4().hex
        )
        db.session.add(user)
        db.session.commit()
        flash("注册成功，请登录！", "ok")
        return redirect(url_for("home.login"))
    return render_template("home/regist.html", form=form)


# 定义登录视图
@home.route("/login/", methods=["GET", "POST"])
def login():
    form = LoginForm()  # 导入登录表单
    if form.validate_on_submit():  # 验证是否有提交表单
        data = form.data
        user = User.query.filter_by(name=data["name"]).first()
        if not user.check_pwd(data["pwd"]):
            flash("密码错误！", "err")
            return redirect(url_for("home.login"))
        session["user"] = data["name"]
        session["user_id"] = user.id
        userlog = Userlog(
            user_id=user.id,
            ip=request.remote_addr
        )
        db.session.add(userlog)
        db.session.commit()
        return redirect(request.args.get("next") or url_for("home.user"))
    return render_template("home/login.html", form=form)


# 定义登出视图
@home.route("/logout/")
@user_login_req
def logout():
    session.pop("user")
    session.pop("user_id")
    return redirect(url_for("home.login"))


# 定义会员中心视图
@home.route("/user/", methods=["GET", "POST"])
@user_login_req
def user():
    form = UserdetailForm()
    user = User.query.get(int(session["user_id"]))
    if user.face is not None:
        form.face.validators = []
    if request.method == "GET":
        form.name.data = user.name
        form.email.data = user.email
        form.phone.data = user.phone
        form.info.data = user.info
    if form.validate_on_submit():
        data = form.data

        if not os.path.exists(app.config['UP_DIR'] + "users" + os.sep):
            os.makedirs(app.config['UP_DIR'] + "users" + os.sep)
            os.chmod(app.config['UP_DIR'] + "users" + os.sep, "rw")

        if form.face.data.filename != '':
            old_face = user.face
            file_face = secure_filename(form.face.data.filename)
            user.face = change_filename(file_face)
            form.face.data.save(app.config['UP_DIR'] + "users" + os.sep + user.face)
            if old_face is not None and os.path.exists(app.config['UP_DIR'] + "users" + os.sep + old_face):
                os.remove(app.config['UP_DIR'] + "users" + os.sep + old_face)

        user.name = data["name"]
        user.email = data["email"]
        user.phone = data["phone"]
        user.info = data["info"]
        db.session.add(user)
        db.session.commit()
        flash("修改成功！", "ok")
    return render_template("home/user.html", form=form, user=user)


# 定义修改密码视图
@home.route("/pwd/", methods=["GET", "POST"])
@user_login_req
def pwd():
    form = PwdForm()
    if form.validate_on_submit():
        data = form.data
        user = User.query.filter_by(name=session["user"]).first()
        user.pwd = generate_password_hash(data["new_pwd"])
        db.session.add(user)
        db.session.commit()
        flash("修改密码成功，请重新登录！", "ok")
        return redirect(url_for("home.logout"))
    return render_template("home/pwd.html", form=form)


# 定义评论记录视图
@home.route("/comments/")
@user_login_req
def comments():
    pg = request.args.get("pg", '')

    # 查询评论数据
    page_data = Comment.query.join(User).join(Movie).filter(
        Comment.user_id == session["user_id"],
        Comment.user_id == User.id,
        Comment.movie_id == Movie.id
    ).order_by(
        Comment.addtime.desc()
    )
    # 分页显示
    pages = page_data.count() // app.config['PAGE_SET'] if page_data.count() % app.config[
        'PAGE_SET'] == 0 else page_data.count() // app.config['PAGE_SET'] + 1
    page = int(pg) if pg.isdigit() and pg is not None and int(pg) <= pages else 1
    page_data = page_data.paginate(page=page, per_page=app.config['PAGE_SET'])
    return render_template("home/comments.html", page_data=page_data)


# 定义登录日志视图
@home.route("/loginlog/", methods=["GET"])
@user_login_req
def loginlog():
    userlog = Userlog.query.filter_by(
        user_id=session["user_id"]
    ).order_by(
        Userlog.addtime.desc()
    ).limit(15).all()
    return render_template("home/loginlog.html", userlog=userlog)


# 定义添加收藏视图
@home.route("/moviecol/add/", methods=["GET"])
@user_login_req
def moviecol_add():
    uid = request.args.get("uid", '')
    mid = request.args.get("mid", '')
    if not uid.isdigit() or uid is None or not mid.isdigit() or mid is None:
        abort(404)
    moviecol = Moviecol.query.filter_by(
        user_id=int(uid),
        movie_id=int(mid)
    ).count()
    if moviecol == 1:
        data = dict(ok=0)
    elif moviecol == 0:
        moviecol = Moviecol(
            user_id=int(uid),
            movie_id=int(mid)
        )
        db.session.add(moviecol)
        db.session.commit()
        data = dict(ok=1)

    import json
    return json.dumps(data)


# 定义取消收藏视图
@home.route("/moviecol/del")
@user_login_req
def moviecol_del():
    mv = request.args.get("mv", '')
    if not mv.isdigit() or mv is None:
        abort(404)
    moviecol = Moviecol.query.filter_by(
        movie_id=int(mv),
        user_id=session["user_id"]
    ).first_or_404()
    db.session.delete(moviecol)
    db.session.commit()
    flash("删除收藏成功！", "ok")
    return redirect(url_for("home.moviecol"))


# 定义收藏电影视图
@home.route("/moviecol/")
@user_login_req
def moviecol():
    pg = request.args.get("pg", '')

    # 查询评论数据
    page_data = Moviecol.query.join(Movie).filter(
        Moviecol.user_id == session["user_id"],
        Moviecol.movie_id == Movie.id
    ).order_by(
        Moviecol.addtime.desc()
    )
    # 分页显示
    pages = page_data.count() // app.config['PAGE_SET'] if page_data.count() % app.config[
        'PAGE_SET'] == 0 else page_data.count() // app.config['PAGE_SET'] + 1
    page = int(pg) if pg.isdigit() and pg is not None and int(pg) <= pages else 1
    page_data = page_data.paginate(page=page, per_page=app.config['PAGE_SET'])
    return render_template("home/moviecol.html", page_data=page_data)
