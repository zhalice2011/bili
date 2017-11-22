#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @File    : forms.py
# @author  : Jaxon
# @software: PyCharm
# @datetime: 9/26 026 下午 07:34

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, Email, Regexp, ValidationError
from app.models import User
from flask import session


class RegistForm(FlaskForm):
    """会员注册表单"""
    name = StringField(
        label="昵称",
        validators=[
            DataRequired("请输入昵称！")
        ],
        description="昵称",
        render_kw={  # 附加选项
            "class": "form-control input-lg",
            "placeholder": "请输入昵称！",
            "autofocus": ""
            # "required": "required"  # 添加强制属性，H5会在前端验证
        }
    )
    email = StringField(
        label="邮箱",
        validators=[
            DataRequired("请输入邮箱！"),
            Email("邮箱格式不正确！")
        ],
        description="邮箱",
        render_kw={
            "class": "form-control input-lg",
            "placeholder": "请输入邮箱！"
        }
    )
    phone = StringField(
        label="手机",
        validators=[
            DataRequired("请输入手机号码！"),
            Regexp("^1[3|4|5|7|8][0-9]{9}$", message="手机号码格式不正确！")
        ],
        description="手机",
        render_kw={
            "class": "form-control input-lg",
            "placeholder": "请输入手机号码！"
        }
    )
    pwd = PasswordField(
        label="密码",
        validators=[
            DataRequired("请输入密码！")
        ],
        description="密码",
        render_kw={
            "class": "form-control input-lg",
            "placeholder": "请输入密码！"
        }
    )
    re_pwd = PasswordField(
        label="确认密码",
        validators=[
            DataRequired("请再次输入密码！"),
            EqualTo('pwd', message="两次密码输入不一致！")
        ],
        description="确认密码",
        render_kw={
            "class": "form-control input-lg",
            "placeholder": "请再次输入密码！"
        }
    )
    submit = SubmitField(
        '注册',
        render_kw={
            "class": "btn btn-lg btn-success btn-block"
        }
    )

    # 昵称验证
    def validate_name(self, field):
        name = field.data
        if User.query.filter_by(name=name).count() == 1:
            raise ValidationError("昵称已经存在！")

    def validate_email(self, field):
        email = field.data
        if User.query.filter_by(email=email).count() == 1:
            raise ValidationError("邮箱已经存在！")

    def validate_phone(self, field):
        phone = field.data
        if User.query.filter_by(phone=phone).count() == 1:
            raise ValidationError("手机号码已经存在！")


class LoginForm(FlaskForm):
    """会员登录表单"""
    name = StringField(
        label="账号",
        validators=[
            DataRequired("请输入账号！")
        ],
        description="账号",
        render_kw={
            "class": "form-control input-lg",
            "placeholder": "请输入账号！",
            "autofocus": ""
        }
    )
    pwd = PasswordField(
        label="密码",
        validators=[
            DataRequired("请输入密码！")
        ],
        description="密码",
        render_kw={
            "class": "form-control input-lg",
            "placeholder": "请输入密码！"
        }
    )
    submit = SubmitField(
        '登录',
        render_kw={
            "class": "btn btn-lg btn-primary btn-block"
        }
    )

    # 账号验证
    def validate_name(self, field):
        name = field.data
        if User.query.filter_by(name=name).count() == 0:
            raise ValidationError("账号不存在！")


class UserdetailForm(FlaskForm):
    """会员中心表单"""
    name = StringField(
        label="昵称",
        validators=[
            DataRequired("请输入昵称！")
        ],
        description="昵称",
        render_kw={
            "class": "form-control",
            "placeholder": "请输入昵称！"
        }
    )
    email = StringField(
        label="邮箱",
        validators=[
            DataRequired("请输入邮箱！"),
            Email("邮箱格式不正确！")
        ],
        description="邮箱",
        render_kw={
            "class": "form-control",
            "placeholder": "请输入邮箱！"
        }
    )
    phone = StringField(
        label="手机",
        validators=[
            DataRequired("请输入手机号码！"),
            Regexp("^1[3|4|5|7|8][0-9]{9}$", message="手机号码格式不正确！")
        ],
        description="手机",
        render_kw={
            "class": "form-control",
            "placeholder": "请输入手机号码！"
        }
    )
    face = FileField(
        label="头像",
        validators=[
            DataRequired("请上传头像！")
        ],
        description="头像",
        render_kw={
            "id": "input_face"
        }
    )
    info = TextAreaField(
        label="简介",
        validators=[
            DataRequired("请输入简介！")
        ],
        description="简介",
        render_kw={
            "class": "form-control",
            "rows": 10,
            "autofocus": ""
        }
    )
    submit = SubmitField(
        '保存修改',
        render_kw={
            "class": "btn btn-success"
        }
    )

    def validate_name(self, field):
        if User.query.filter_by(name=field.data).count() == 1:
            if User.query.get(int(session["user_id"])).name != field.data:
                raise ValidationError("名称已经存在！")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).count() == 1:
            if User.query.get(int(session["user_id"])).email != field.data:
                raise ValidationError("邮箱已经存在！")

    def validate_phone(self, field):
        if User.query.filter_by(phone=field.data).count() == 1:
            if User.query.get(int(session["user_id"])).phone != field.data:
                raise ValidationError("手机号码已经存在！")


class PwdForm(FlaskForm):
    """修改密码"""
    old_pwd = PasswordField(
        label="旧密码",
        validators=[
            DataRequired("请输入旧密码！")
        ],
        description="旧密码",
        render_kw={
            "class": "form-control",
            "placeholder": "请输入旧密码！",
            "autofocus": ""
        }
    )
    new_pwd = PasswordField(
        label="新密码",
        validators=[
            DataRequired("请输入新密码！")
        ],
        description="新密码",
        render_kw={
            "class": "form-control",
            "placeholder": "请输入新密码！"
        }
    )
    submit = SubmitField(
        '修改密码',
        render_kw={
            "class": "btn btn-success"
        }
    )

    # 旧密码验证
    def validate_old_pwd(self, field):
        from flask import session
        old_pwd = field.data
        name = session["user"]
        user = User.query.filter_by(name=name).first()
        if not user.check_pwd(old_pwd):
            raise ValidationError("旧密码错误！")


class CommentForm(FlaskForm):
    """评论表单"""
    content = TextAreaField(
        label="内容",
        validators=[
            DataRequired("请输入内容！")
        ],
        description="内容",
        render_kw={
            "id": "input_content",
            "autofocus": ""
        }
    )
    submit = SubmitField(
        '提交评论',
        render_kw={
            "class": "btn btn-success",
            "id": "btn-sub"
        }
    )
