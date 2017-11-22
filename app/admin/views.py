#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @File    : views.py
# @author  : Jaxon
# @software: PyCharm
# @datetime: 9/26 026 下午 07:34


from app import db, app
from app.admin import admin
from flask import render_template, redirect, url_for, flash, session, request, abort
from app.admin.forms import LoginForm, TagForm, MovieForm, PreviewForm, PwdForm, AuthForm, RoleForm, AdminForm
from app.models import Admin, Tag, Movie, Preview, User, Comment, Moviecol, Oplog, Adminlog, Userlog, Auth, Role
from functools import wraps
from werkzeug.utils import secure_filename
import os, uuid, datetime

page_data = None  # 存储分页数据以便返回使用
edit_role_name = None  # 存储编辑角色页的旧角色名称


# 上下文处理器（将变量直接提供给模板使用）
@admin.context_processor
def tpl_extra():
    if "admin_id" in session and Adminlog.query.filter_by(admin_id=session["admin_id"]).count() > 0:
        adminlog = Adminlog.query.filter_by(admin_id=session["admin_id"]).order_by(
            Adminlog.addtime.desc()
        ).first()
        login_time = adminlog.addtime
    else:
        # 登陆前是看不到页面的，所以给空值
        login_time = None

    data = dict(
        login_time=login_time
    )
    return data


# 定义登录判断装饰器
def admin_login_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # session不存在时请求登录
        if "admin" not in session:
            return redirect(url_for("admin.login", next=request.url))
        return f(*args, **kwargs)

    return decorated_function


# 定义权限控制装饰器
def admin_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_id" in session:
            # 查询出权限ID，然后查出对应的路由地址
            admin = Admin.query.join(Role).filter(
                Admin.role_id == Role.id,
                Admin.id == session["admin_id"]
            ).first()
            auths = list(map(lambda v: int(v), admin.role.auths.split(",")))
            auth_list = Auth.query.all()
            urls = [v.url for v in auth_list for var in auths if var == v.id]

            # 判断是否有权限访问
            if app.config['AUTH_SWITCH'] and str(request.url_rule) is not urls:
                abort(404)
        return f(*args, **kwargs)

    return decorated_function


# 修改文件名称
def change_filename(filename):
    fileinfo = os.path.splitext(filename)  # 对名字进行前后缀分离
    filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + "_" + uuid.uuid4().hex + fileinfo[-1]  # 生成新文件名
    return filename


# 调用蓝图（定义视图）
# 定义控制面板视图
@admin.route("/")
@admin_login_req
@admin_auth
def index():
    return render_template("admin/index.html")


# 定义登录视图
@admin.route("/login/", methods=["GET", "POST"])
def login():
    form = LoginForm()  # 导入登录表单
    if form.validate_on_submit():  # 验证是否有提交表单
        data = form.data
        admin = Admin.query.filter_by(name=data["account"]).first()
        if not admin.check_pwd(data["pwd"]):
            flash("密码错误！", "err")
            return redirect(url_for("admin.login"))
        session["admin"] = data["account"]
        session["admin_id"] = admin.id
        adminlog = Adminlog(
            admin_id=admin.id,
            ip=request.remote_addr
        )
        db.session.add(adminlog)
        db.session.commit()
        return redirect(request.args.get("next") or url_for("admin.index"))
    return render_template("admin/login.html", form=form)


# 定义登出视图
@admin.route("/logout/")
@admin_login_req
def logout():
    session.pop("admin")  # 移除用户session
    session.pop("admin_id")
    return redirect(url_for("admin.login"))


# 定义修改密码视图
@admin.route("/pwd/", methods=["GET", "POST"])
@admin_login_req
def pwd():
    form = PwdForm()
    if form.validate_on_submit():
        data = form.data
        admin = Admin.query.filter_by(name=session["admin"]).first()
        from werkzeug.security import generate_password_hash
        admin.pwd = generate_password_hash(data["new_pwd"])
        db.session.add(admin)
        db.session.commit()
        flash("修改密码成功，请重新登录！", "ok")
        oplog = Oplog(
            admin_id=session["admin_id"],
            ip=request.remote_addr,
            reason="修改了密码"
        )
        db.session.add(oplog)
        db.session.commit()
        return redirect(url_for("admin.logout"))
    return render_template("admin/pwd.html", form=form)


# 定义添加标签视图
@admin.route("/tag/add/", methods=["GET", "POST"])
@admin_login_req
@admin_auth
def tag_add():
    form = TagForm()
    if form.validate_on_submit():
        data = form.data
        tag = Tag.query.filter_by(name=data["name"]).count()
        if tag == 1:
            flash("名称已经存在！", "err")
            return redirect(url_for("admin.tag_add"))
        tag = Tag(
            name=data["name"]
        )
        db.session.add(tag)
        db.session.commit()
        flash("添加标签成功！", "ok")
        oplog = Oplog(
            admin_id=session["admin_id"],
            ip=request.remote_addr,
            reason="添加新标签：%s" % data["name"]
        )
        db.session.add(oplog)
        db.session.commit()
        return redirect(url_for("admin.tag_add"))
    return render_template("admin/tag_add.html", form=form)


# 定义编辑标签视图
@admin.route("/tag/edit/<int:id>/", methods=["GET", "POST"])
@admin_login_req
@admin_auth
def tag_edit(id=None):
    form = TagForm()
    tag = Tag.query.get_or_404(id)
    page = page_data.page if page_data is not None else 1
    if form.validate_on_submit():
        data = form.data
        tag_count = Tag.query.filter_by(name=data["name"]).count()
        if tag_count == 1 and tag.name != data['name']:
            flash("名称已经存在！", "err")
            return redirect(url_for("admin.tag_edit", id=id))
        oplog = Oplog(
            admin_id=session["admin_id"],
            ip=request.remote_addr,
            reason="修改标签“%s”为“%s”" % (tag.name, data["name"])
        )
        db.session.add(oplog)
        db.session.commit()

        tag.name = data["name"]
        db.session.add(tag)
        db.session.commit()
        flash("修改标签成功！", "ok")
        return redirect(url_for("admin.tag_list", page=page))
    return render_template("admin/tag_edit.html", form=form, tag=tag, page=page)


# 定义标签列表视图
@admin.route("/tag/list/<int:page>/", methods=["GET"])
@admin_login_req
@admin_auth
def tag_list(page=None):
    global page_data
    if page is None:
        page = 1
    page_data = Tag.query.order_by(
        Tag.addtime.desc()
    ).paginate(page=page, per_page=app.config['PAGE_SET'])
    return render_template("admin/tag_list.html", page_data=page_data)


# 定义标签删除视图
@admin.route("/tag/del/<int:id>/", methods=["GET"])
@admin_login_req
@admin_auth
def tag_del(id=None):
    if page_data.pages == 1 or page_data is None:
        page = 1
    else:
        page = page_data.page if page_data.page < page_data.pages or page_data.total % page_data.per_page != 1 else page_data.pages - 1
    tag = Tag.query.filter_by(id=id).first_or_404()
    db.session.delete(tag)
    db.session.commit()
    flash("删除标签成功！", "ok")
    oplog = Oplog(
        admin_id=session["admin_id"],
        ip=request.remote_addr,
        reason="删除标签：%s" % tag.name
    )
    db.session.add(oplog)
    db.session.commit()
    return redirect(url_for("admin.tag_list", page=page))


# 定义添加电影视图
@admin.route("/movie/add/", methods=["GET", "POST"])
@admin_login_req
@admin_auth
def movie_add():
    form = MovieForm()
    if form.validate_on_submit():
        data = form.data
        if Movie.query.filter_by(title=data["title"]).count() == 1:
            flash("影片已经存在！", "err")
            return redirect(url_for("admin.movie_add"))
        file_url = secure_filename(form.url.data.filename)  # 获取并转化为安全的电影文件名
        file_logo = secure_filename(form.logo.data.filename)
        if not os.path.exists(app.config['UP_DIR']):  # 存放目录不存在则创建
            os.makedirs(app.config['UP_DIR'])
            os.chmod(app.config['UP_DIR'], "rw")
        url = change_filename(file_url)  # 调用函数生成新的文件名
        logo = change_filename(file_logo)
        form.url.data.save(app.config['UP_DIR'] + url)  # 保存上传的数据
        form.logo.data.save(app.config['UP_DIR'] + logo)
        movie = Movie(
            title=data["title"],
            url=url,
            info=data["info"],
            logo=logo,
            star=int(data["star"]),
            playnum=0,
            commentnum=0,
            tag_id=int(data["tag_id"]),
            area=data["area"],
            release_time=data["release_time"],
            length=data["length"]
        )
        db.session.add(movie)
        db.session.commit()
        flash("添加电影成功！", "ok")
        oplog = Oplog(
            admin_id=session["admin_id"],
            ip=request.remote_addr,
            reason="添加新电影：%s" % data["title"]
        )
        db.session.add(oplog)
        db.session.commit()
        return redirect(url_for("admin.movie_add"))
    return render_template("admin/movie_add.html", form=form)


# 定义编辑电影视图
@admin.route("/movie/edit/<int:id>/", methods=["GET", "POST"])
@admin_login_req
@admin_auth
def movie_edit(id=None):
    form = MovieForm()
    form.url.validators = []  # 因为可以不做更改，所以不需要校验
    form.logo.validators = []
    movie = Movie.query.get_or_404(id)
    page = page_data.page if page_data is not None else 1
    if request.method == "GET":
        form.info.data = movie.info
        form.star.data = movie.star
        form.tag_id.data = movie.tag_id
    if form.validate_on_submit():
        data = form.data
        movie_count = Movie.query.filter_by(title=data["title"]).count()
        if movie_count == 1 and movie.title != data['title']:
            flash("片名已经存在！", "err")
            return redirect(url_for("admin.movie_edit", id=id))

        if not os.path.exists(app.config['UP_DIR']):  # 存放目录不存在则创建
            os.makedirs(app.config['UP_DIR'])
            os.chmod(app.config['UP_DIR'], "rw")

        if form.url.data.filename != '':
            old_url = movie.url
            file_url = secure_filename(form.url.data.filename)  # 获取并转化为安全的电影文件名
            movie.url = change_filename(file_url)  # 调用函数生成新的文件名
            form.url.data.save(app.config['UP_DIR'] + movie.url)  # 保存上传的数据
            if os.path.exists(app.config['UP_DIR'] + old_url):  # 删除旧文件
                os.remove(app.config['UP_DIR'] + old_url)

        if form.logo.data.filename != '':
            old_logo = movie.logo
            file_logo = secure_filename(form.logo.data.filename)
            movie.logo = change_filename(file_logo)
            form.logo.data.save(app.config['UP_DIR'] + movie.logo)
            if os.path.exists(app.config['UP_DIR'] + old_logo):
                os.remove(app.config['UP_DIR'] + old_logo)

        oplog = Oplog(
            admin_id=session["admin_id"],
            ip=request.remote_addr,
            reason="修改电影：%s（原名：%s）" % (data["title"], movie.title)
        )
        db.session.add(oplog)
        db.session.commit()

        movie.title = data["title"]
        movie.info = data["info"]
        movie.star = int(data["star"])
        movie.tag_id = int(data["tag_id"])
        movie.area = data["area"]
        movie.release_time = data["release_time"]
        movie.length = data["length"]
        db.session.add(movie)
        db.session.commit()
        flash("修改电影成功！", "ok")
        return redirect(url_for("admin.movie_list", page=page))
    return render_template("admin/movie_edit.html", form=form, movie=movie, page=page)


# 定义电影列表视图
@admin.route("/movie/list/<int:page>/", methods=["GET"])
@admin_login_req
@admin_auth
def movie_list(page=None):
    global page_data
    if page is None:
        page = 1
    page_data = Movie.query.join(Tag).filter(
        Movie.tag_id == Tag.id
    ).order_by(
        Movie.addtime.desc()
    ).paginate(page=page, per_page=app.config['PAGE_SET'])
    return render_template("admin/movie_list.html", page_data=page_data)


# 定义电影删除视图
@admin.route("/movie/del/<int:id>/", methods=["GET"])
@admin_login_req
@admin_auth
def movie_del(id=None):
    if page_data.pages == 1 or page_data is None:
        page = 1
    else:
        page = page_data.page if page_data.page < page_data.pages or page_data.total % page_data.per_page != 1 else page_data.pages - 1
    movie = Movie.query.filter_by(id=id).first_or_404()
    db.session.delete(movie)
    db.session.commit()
    if os.path.exists(app.config['UP_DIR'] + movie.url):  # 删除文件
        os.remove(app.config['UP_DIR'] + movie.url)
    if os.path.exists(app.config['UP_DIR'] + movie.logo):
        os.remove(app.config['UP_DIR'] + movie.logo)
    flash("删除电影成功！", "ok")
    oplog = Oplog(
        admin_id=session["admin_id"],
        ip=request.remote_addr,
        reason="删除电影：%s" % movie.title
    )
    db.session.add(oplog)
    db.session.commit()
    return redirect(url_for("admin.movie_list", page=page))


# 定义添加预告视图
@admin.route("/preview/add/", methods=["GET", "POST"])
@admin_login_req
@admin_auth
def preview_add():
    form = PreviewForm()
    if form.validate_on_submit():
        data = form.data
        preview = Preview.query.filter_by(title=data["title"]).count()
        if preview == 1:
            flash("预告标题已经存在！", "err")
            return redirect(url_for("admin.preview_add"))
        file_logo = secure_filename(form.logo.data.filename)
        if not os.path.exists(app.config['UP_DIR']):
            os.makedirs(app.config['UP_DIR'])
            os.chmod(app.config['UP_DIR'], "rw")
        logo = change_filename(file_logo)
        form.logo.data.save(app.config['UP_DIR'] + logo)
        preview = Preview(
            title=data["title"],
            logo=logo
        )
        db.session.add(preview)
        db.session.commit()
        flash("添加预告成功！", "ok")
        oplog = Oplog(
            admin_id=session["admin_id"],
            ip=request.remote_addr,
            reason="添加新电影预告：%s" % data["title"]
        )
        db.session.add(oplog)
        db.session.commit()
        return redirect(url_for("admin.preview_add"))
    return render_template("admin/preview_add.html", form=form)


# 定义编辑预告视图
@admin.route("/preview/edit/<int:id>/", methods=["GET", "POST"])
@admin_login_req
@admin_auth
def preview_edit(id=None):
    form = PreviewForm()
    form.logo.validators = []
    preview = Preview.query.get_or_404(id)
    page = page_data.page if page_data is not None else 1
    if form.validate_on_submit():
        data = form.data
        preview_count = Preview.query.filter_by(title=data["title"]).count()
        if preview_count == 1 and preview.title != data['title']:
            flash("预告标题已经存在！", "err")
            return redirect(url_for("admin.preview_edit", id=id))

        if not os.path.exists(app.config['UP_DIR']):
            os.makedirs(app.config['UP_DIR'])
            os.chmod(app.config['UP_DIR'], "rw")

        if form.logo.data.filename != '':
            old_logo = preview.logo
            file_logo = secure_filename(form.logo.data.filename)
            preview.logo = change_filename(file_logo)
            form.logo.data.save(app.config['UP_DIR'] + preview.logo)
            if os.path.exists(app.config['UP_DIR'] + old_logo):
                os.remove(app.config['UP_DIR'] + old_logo)

        oplog = Oplog(
            admin_id=session["admin_id"],
            ip=request.remote_addr,
            reason="修改电影预告：%s（原名：%s）" % (data["title"], preview.title)
        )
        db.session.add(oplog)
        db.session.commit()

        preview.title = data["title"]
        db.session.add(preview)
        db.session.commit()
        flash("修改预告成功！", "ok")
        return redirect(url_for("admin.preview_list", page=page))
    return render_template("admin/preview_edit.html", form=form, preview=preview, page=page)


# 定义预告列表视图
@admin.route("/preview/list/<int:page>/", methods=["GET", "POST"])
@admin_login_req
@admin_auth
def preview_list(page=None):
    global page_data
    if page is None:
        page = 1
    page_data = Preview.query.order_by(
        Preview.addtime.desc()
    ).paginate(page=page, per_page=app.config['PAGE_SET'])
    return render_template("admin/preview_list.html", page_data=page_data)


# 定义预告删除视图
@admin.route("/preview/del/<int:id>/", methods=["GET"])
@admin_login_req
@admin_auth
def preview_del(id=None):
    if page_data.pages == 1 or page_data is None:
        page = 1
    else:
        page = page_data.page if page_data.page < page_data.pages or page_data.total % page_data.per_page != 1 else page_data.pages - 1
    preview = Preview.query.filter_by(id=id).first_or_404()
    db.session.delete(preview)
    db.session.commit()
    if os.path.exists(app.config['UP_DIR'] + preview.logo):
        os.remove(app.config['UP_DIR'] + preview.logo)
    flash("删除预告成功！", "ok")
    oplog = Oplog(
        admin_id=session["admin_id"],
        ip=request.remote_addr,
        reason="删除电影预告：%s" % preview.title
    )
    db.session.add(oplog)
    db.session.commit()
    return redirect(url_for("admin.preview_list", page=page))


# 定义会员列表视图
@admin.route("/user/list/<int:page>/", methods=["GET"])
@admin_login_req
@admin_auth
def user_list(page=None):
    global page_data
    if page is None:
        page = 1
    page_data = User.query.order_by(
        User.addtime.desc()
    ).paginate(page=page, per_page=app.config['PAGE_SET'])
    return render_template("admin/user_list.html", page_data=page_data)


# 定义查看会员视图
@admin.route("/user/view/<int:id>/", methods=["GET"])
@admin_login_req
@admin_auth
def user_view(id=None):
    user = User.query.get_or_404(id)
    page = page_data.page if page_data is not None else 1
    return render_template("admin/user_view.html", user=user, page=page)


# 定义会员删除视图
@admin.route("/user/del/<int:id>/", methods=["GET"])
@admin_login_req
@admin_auth
def user_del(id=None):
    if page_data.pages == 1 or page_data is None:
        page = 1
    else:
        page = page_data.page if page_data.page < page_data.pages or page_data.total % page_data.per_page != 1 else page_data.pages - 1
    user = User.query.filter_by(id=id).first_or_404()
    db.session.delete(user)
    db.session.commit()
    if os.path.exists(app.config['UP_DIR'] + "users" + os.sep + user.face):
        os.remove(app.config['UP_DIR'] + "users" + os.sep + user.face)
    flash("删除会员成功！", "ok")
    oplog = Oplog(
        admin_id=session["admin_id"],
        ip=request.remote_addr,
        reason="删除会员：%s" % user.name
    )
    db.session.add(oplog)
    db.session.commit()
    return redirect(url_for("admin.user_list", page=page))


# 定义评论列表视图
@admin.route("/comment/list/<int:page>/", methods=["GET"])
@admin_login_req
@admin_auth
def comment_list(page=None):
    global page_data
    if page is None:
        page = 1
    page_data = Comment.query.join(Movie).join(User).filter(
        Comment.movie_id == Movie.id,
        Comment.user_id == User.id
    ).order_by(
        Comment.addtime.desc()
    ).paginate(page=page, per_page=app.config['PAGE_SET'])
    return render_template("admin/comment_list.html", page_data=page_data)


# 定义评论删除视图
@admin.route("/comment/del/<int:id>/", methods=["GET"])
@admin_login_req
@admin_auth
def comment_del(id=None):
    if page_data.pages == 1 or page_data is None:
        page = 1
    else:
        page = page_data.page if page_data.page < page_data.pages or page_data.total % page_data.per_page != 1 else page_data.pages - 1
    comment = Comment.query.filter_by(id=id).first_or_404()
    user = User.query.filter_by(id=comment.user_id).first_or_404()
    movie = Movie.query.filter_by(id=comment.movie_id).first_or_404()
    db.session.delete(comment)
    db.session.commit()
    flash("删除评论成功！", "ok")
    oplog = Oplog(
        admin_id=session["admin_id"],
        ip=request.remote_addr,
        reason="删除会员「%s(%s)」在《%s》的评论：%s" % (user.name, user.id, movie.title, comment.content)
    )
    db.session.add(oplog)
    db.session.commit()
    return redirect(url_for("admin.comment_list", page=page))


# 定义收藏列表视图
@admin.route("/moviecol/list/<int:page>/", methods=["GET"])
@admin_login_req
@admin_auth
def moviecol_list(page=None):
    global page_data
    if page is None:
        page = 1
    page_data = Moviecol.query.join(Movie).join(User).filter(
        Moviecol.movie_id == Movie.id,
        Moviecol.user_id == User.id
    ).order_by(
        Moviecol.addtime.desc()
    ).paginate(page=page, per_page=app.config['PAGE_SET'])
    return render_template("admin/moviecol_list.html", page_data=page_data)


# 定义收藏删除视图
@admin.route("/moviecol/del/<int:id>/", methods=["GET"])
@admin_login_req
@admin_auth
def moviecol_del(id=None):
    if page_data.pages == 1 or page_data is None:
        page = 1
    else:
        page = page_data.page if page_data.page < page_data.pages or page_data.total % page_data.per_page != 1 else page_data.pages - 1
    moviecol = Moviecol.query.filter_by(id=id).first_or_404()
    user = User.query.filter_by(id=moviecol.user_id).first_or_404()
    movie = Movie.query.filter_by(id=moviecol.movie_id).first_or_404()
    db.session.delete(moviecol)
    db.session.commit()
    flash("删除收藏成功！", "ok")
    oplog = Oplog(
        admin_id=session["admin_id"],
        ip=request.remote_addr,
        reason="删除会员「%s(%s)」对电影《%s》的收藏" % (user.name, user.id, movie.title)
    )
    db.session.add(oplog)
    db.session.commit()
    return redirect(url_for("admin.moviecol_list", page=page))


# 定义操作日志列表视图
@admin.route("/oplog/list/<int:page>/", methods=["GET"])
@admin_login_req
@admin_auth
def oplog_list(page=None):
    global page_data
    if page is None:
        page = 1
    page_data = Oplog.query.join(Admin).filter(
        Oplog.admin_id == Admin.id
    ).order_by(
        Oplog.addtime.desc()
    ).paginate(page=page, per_page=app.config['PAGE_SET'])
    return render_template("admin/oplog_list.html", page_data=page_data)


# 定义管理员登录日志列表视图
@admin.route("/adminloginlog/list/<int:page>/", methods=["GET"])
@admin_login_req
@admin_auth
def adminloginlog_list(page=None):
    global page_data
    if page is None:
        page = 1
    page_data = Adminlog.query.join(Admin).filter(
        Adminlog.admin_id == Admin.id
    ).order_by(
        Adminlog.addtime.desc()
    ).paginate(page=page, per_page=app.config['PAGE_SET'])
    return render_template("admin/adminloginlog_list.html", page_data=page_data)


# 定义会员登录日志列表视图
@admin.route("/userloginlog/list/<int:page>/", methods=["GET"])
@admin_login_req
@admin_auth
def userloginlog_list(page=None):
    global page_data
    if page is None:
        page = 1
    page_data = Userlog.query.join(User).filter(
        Userlog.user_id == User.id
    ).order_by(
        Userlog.addtime.desc()
    ).paginate(page=page, per_page=app.config['PAGE_SET'])
    return render_template("admin/userloginlog_list.html", page_data=page_data)


# 定义添加权限视图
@admin.route("/auth/add/", methods=["GET", "POST"])
@admin_login_req
@admin_auth
def auth_add():
    form = AuthForm()
    if form.validate_on_submit():
        data = form.data
        auth = Auth(
            name=data["name"],
            url=data["url"]
        )
        db.session.add(auth)
        db.session.commit()
        flash("添加权限成功！", "ok")
        oplog = Oplog(
            admin_id=session["admin_id"],
            ip=request.remote_addr,
            reason="添加新权限：%s" % data["name"]
        )
        db.session.add(oplog)
        db.session.commit()
        return redirect(url_for("admin.auth_add"))
    return render_template("admin/auth_add.html", form=form)


# 定义编辑权限视图
@admin.route("/auth/edit/<int:id>/", methods=["GET", "POST"])
@admin_login_req
@admin_auth
def auth_edit(id=None):
    form = AuthForm()
    auth = Auth.query.get_or_404(id)
    page = page_data.page if page_data is not None else 1
    if request.method == "GET":
        form.name.data = auth.name
        form.url.data = auth.url
    if form.validate_on_submit():
        data = form.data
        oplog = Oplog(
            admin_id=session["admin_id"],
            ip=request.remote_addr,
            reason="修改权限：%s（原名：%s）" % (data["name"], auth.name)
        )
        db.session.add(oplog)
        db.session.commit()

        auth.name = data["name"]
        auth.url = data["url"]
        db.session.add(auth)
        db.session.commit()
        flash("修改权限成功！", "ok")
        return redirect(url_for("admin.auth_list", page=page))
    return render_template("admin/auth_edit.html", form=form, page=page)


# 定义权限列表视图
@admin.route("/auth/list/<int:page>/", methods=["GET"])
@admin_login_req
@admin_auth
def auth_list(page=None):
    global page_data
    if page is None:
        page = 1
    page_data = Auth.query.order_by(
        Auth.addtime.desc()
    ).paginate(page=page, per_page=app.config['PAGE_SET'])
    return render_template("admin/auth_list.html", page_data=page_data)


# 定义权限删除视图
@admin.route("/auth/del/<int:id>/", methods=["GET"])
@admin_login_req
@admin_auth
def auth_del(id=None):
    if page_data.pages == 1 or page_data is None:
        page = 1
    else:
        page = page_data.page if page_data.page < page_data.pages or page_data.total % page_data.per_page != 1 else page_data.pages - 1
    auth = Auth.query.filter_by(id=id).first_or_404()
    db.session.delete(auth)
    db.session.commit()
    flash("删除权限成功！", "ok")
    oplog = Oplog(
        admin_id=session["admin_id"],
        ip=request.remote_addr,
        reason="删除权限：%s" % auth.name
    )
    db.session.add(oplog)
    db.session.commit()
    return redirect(url_for("admin.auth_list", page=page))


# 定义添加角色视图
@admin.route("/role/add/", methods=["GET", "POST"])
@admin_login_req
@admin_auth
def role_add():
    form = RoleForm()
    if form.validate_on_submit():
        data = form.data
        role = Role(
            name=data["name"],
            auths=",".join(map(lambda v: str(v), data["auths"]))
        )
        db.session.add(role)
        db.session.commit()
        flash("添加角色成功！", "ok")
        oplog = Oplog(
            admin_id=session["admin_id"],
            ip=request.remote_addr,
            reason="添加新角色：%s" % data["name"]
        )
        db.session.add(oplog)
        db.session.commit()
        return redirect(url_for("admin.role_add"))
    return render_template("admin/role_add.html", form=form)


# 定义编辑角色视图
@admin.route("/role/edit/<int:id>/", methods=["GET", "POST"])
@admin_login_req
@admin_auth
def role_edit(id=None):
    global edit_role_name
    form = RoleForm()
    role = Role.query.get_or_404(id)
    edit_role_name = role.name
    page = page_data.page if page_data is not None else 1
    if request.method == "GET":
        form.name.data = role.name
        form.auths.data = list(map(lambda v: int(v), role.auths.split(",")))
    if form.validate_on_submit():
        data = form.data
        oplog = Oplog(
            admin_id=session["admin_id"],
            ip=request.remote_addr,
            reason="修改角色：%s（原名：%s）" % (data["name"], role.name)
        )
        db.session.add(oplog)
        db.session.commit()

        role.name = data["name"]
        role.auths = ",".join(map(lambda v: str(v), data["auths"]))
        db.session.add(role)
        db.session.commit()
        flash("修改角色成功！", "ok")
        return redirect(url_for("admin.role_list", page=page))
    return render_template("admin/role_edit.html", form=form, page=page)


# 定义角色列表视图
@admin.route("/role/list/<int:page>/", methods=["GET"])
@admin_login_req
@admin_auth
def role_list(page=None):
    global page_data
    if page is None:
        page = 1
    page_data = Role.query.order_by(
        Role.addtime.desc()
    ).paginate(page=page, per_page=app.config['PAGE_SET'])
    return render_template("admin/role_list.html", page_data=page_data)


# 定义角色删除视图
@admin.route("/role/del/<int:id>/", methods=["GET"])
@admin_login_req
@admin_auth
def role_del(id=None):
    if page_data.pages == 1 or page_data is None:
        page = 1
    else:
        page = page_data.page if page_data.page < page_data.pages or page_data.total % page_data.per_page != 1 else page_data.pages - 1
    role = Role.query.filter_by(id=id).first_or_404()
    db.session.delete(role)
    db.session.commit()
    flash("删除角色成功！", "ok")
    oplog = Oplog(
        admin_id=session["admin_id"],
        ip=request.remote_addr,
        reason="删除角色：%s" % role.name
    )
    db.session.add(oplog)
    db.session.commit()
    return redirect(url_for("admin.role_list", page=page))


# 定义添加管理员视图
@admin.route("/admin/add/", methods=["GET", "POST"])
@admin_login_req
@admin_auth
def admin_add():
    form = AdminForm()
    if form.validate_on_submit():
        data = form.data
        from werkzeug.security import generate_password_hash
        admin = Admin(
            name=data["name"],
            pwd=generate_password_hash(data["pwd"]),
            role_id=data["role_id"],
            is_super=1
        )
        db.session.add(admin)
        db.session.commit()
        flash("添加管理员成功！", "ok")
        oplog = Oplog(
            admin_id=session["admin_id"],
            ip=request.remote_addr,
            reason="添加新管理员：%s" % data["name"]
        )
        db.session.add(oplog)
        db.session.commit()
        return redirect(url_for("admin.admin_add"))
    return render_template("admin/admin_add.html", form=form)


# 定义管理员列表视图
@admin.route("/admin/list/<int:page>/", methods=["GET", "POST"])
@admin_login_req
@admin_auth
def admin_list(page=None):
    global page_data
    if page is None:
        page = 1
    page_data = Admin.query.join(Role).filter(
        Admin.role_id == Role.id
    ).order_by(
        Admin.addtime.desc()
    ).paginate(page=page, per_page=app.config['PAGE_SET'])
    return render_template("admin/admin_list.html", page_data=page_data)
