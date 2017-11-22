#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @File    : __init__.py
# @author  : Jaxon
# @software: PyCharm
# @datetime: 9/26 026 下午 07:32


from flask import Blueprint

# 定义蓝图
home = Blueprint("home", __name__)
import app.home.views
