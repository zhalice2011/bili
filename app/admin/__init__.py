#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @File    : __init__.py
# @author  : Jaxon
# @software: PyCharm
# @datetime: 9/26 026 下午 07:34


from flask import Blueprint

# 定义蓝图
admin = Blueprint("admin", __name__)
import app.admin.views
