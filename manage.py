#!/usr/bin/env python
# -*- coding:utf-8 -*-
# @File    : manage.py
# @author  : Jaxon
# @software: PyCharm
# @datetime: 9/26 026 下午 07:29


from app import app
from flask_script import Manager

manage = Manager(app)

# 项目入口
if __name__ == "__main__":
    manage.run()
