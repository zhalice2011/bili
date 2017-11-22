# 微电影网站搭建手册

## 简介

> 这是一个使用Python语言和Flask框架搭建的微电影网站。网站分前台和后台，前台面向用户，主要功能有注册会员、搜索电影、观看电影、收藏及评论电影；后台面向网站管理人员，主要有标签、电影、预告等针对前台功能的管理以及后台管理员和权限的管理。下方是一个索引目录，可以快速定位到你想看的地方。赶快试试吧~（Github竟然不支持，以后再试吧！）

[TOC]

## 搭建前准备

> 准备？你觉得要准备啥呢，当然是下载各种文件咯。当然，可别把自己丢了，哈哈。

- 点击Logo跳转至对应的官网下载页面

  [![image](https://github.com/caozhiqiango/movie_project/raw/master/picture/CentOS_Logo.PNG "CentOS")](https://www.centos.org/download/)&emsp;[![image](https://github.com/caozhiqiango/movie_project/raw/master/picture/Python_Logo.PNG "Python")](https://www.python.org/downloads/)&emsp;[![image](https://github.com/caozhiqiango/movie_project/raw/master/picture/Nginx_Logo.PNG "Nginx")](http://nginx.org/en/download.html)

- **备注**：
  - CentOS建议选择7.x，官网是否有点慢？[点我传送到网易镜像站](http://mirrors.163.com/centos/7.4.1708/isos/x86_64/)
  - Python选择3.x版本，点击‘Gzipped source tarball’下载即可
  - Nginx点击对应版本即可下载，如：`nginx-1.12.1`


## 安装LNMP环境

> 看着好高级的样子？其实是Linux + Nginx + MySQL + Python 啦，是不是差点被迷惑了呢。

### 1.CentOS安装

> 这个度娘一下有大把，本文档就不再做演示，下方给个参考链接

- [centos7.0安装教程](https://jingyan.baidu.com/article/a3aad71aa180e7b1fa009676.html)

### 2. 安装Python

1. 安装python3.6可能使用的依赖（有就不装，不确定就执行一下，反正又不会怀孕不是？）
```
yum -y install openssl-devel bzip2-devel expat-devel gdbm-devel readline-devel sqlite-devel
```
![Python_depend](https://github.com/caozhiqiango/movie_project/raw/master/picture/Python_depend.PNG)

2. 安装Python
```
# 先解包，然后进入Python目录
tar -zxf Python-3.6.3.tgz
cd Python-3.6.3/
# 指定安装位置并安装
./configure --prefix=/usr/local
# 从图中报错提示可知没装C编译器，安装它，然后再执行前一条语句
yum -y install gcc gcc-c++
# 接下来进行编译和安装
make
make altinstall
# 最后进入安装目录确认一下
ls /usr/local/bin
```
![Python_install01](https://github.com/caozhiqiango/movie_project/raw/master/picture/Python_install01.PNG)
![Python_install02](https://github.com/caozhiqiango/movie_project/raw/master/picture/Python_install02.PNG)

3. 将Python指定为系统默认
```
# 将自带的Python2.7备份，然后创建3.6的软链接
cd /usr/bin
mv python python.bak
ln -s /usr/local/bin/python3.6 ./python
ln -s /usr/local/bin/python3.6 ./python3
```
![Python_install03](https://github.com/caozhiqiango/movie_project/raw/master/picture/Python_install03.PNG)

4. 修复指定默认后带来的问题（有的系统软件使用的是Python2.7）
```
# 修改受影响文件的文件头（vim用`:wq`保存）
ls yum*
vim yum
vim yum-config-manager
vim yum-debug-restore
vim yum-groups-manager
vim yum-builddep
vim yum-debug-dump
vim yumdownloader
vim gnome-tweak-tool
vim /usr/libexec/urlgrabber-ext-down
```
![Python_install04](https://github.com/caozhiqiango/movie_project/raw/master/picture/Python_install04.PNG)

### 3. 安装数据库

> 接下来安装Mariadb，偷个懒啦，这个安装方便嘛！至于这货和MySQL什么关系？自己问度娘去。滑稽

```
# 安装Mariadb
yum -y install mariadb-server
# 启动Mariadb
systemctl start mariadb.service
# 设置开机自启
systemctl enable mariadb.service
# 接下来修改数据库字符集
vim /etc/my.cnf
# 在[mysqld_safe]上面新增下方语句
character-set-server=utf8
# 重启Mariadb
systemctl restart mariadb.service
# 然后我们修改数据库密码
mysqladmin -uroot password "root"
# 登录数据库验证下
mysql -uroot -proot
\s;
```
![Mariadb_install01](https://github.com/caozhiqiango/movie_project/raw/master/picture/Mariadb_install01.PNG)
![Mariadb_install02](https://github.com/caozhiqiango/movie_project/raw/master/picture/Mariadb_install02.PNG)
![Mariadb_install03](https://github.com/caozhiqiango/movie_project/raw/master/picture/Mariadb_install03.PNG)

### 4. 安装Nginx

1. 安装依赖
```
yum -y install gcc gcc-c++ openssl-devel pcre-devel httpd-tools
```
![Nginx_install01](https://github.com/caozhiqiango/movie_project/raw/master/picture/Nginx_install01.PNG)

2. 安装软件
```
# 创建用户
useradd nginx
# 解包、配置、编译、安装一气呵成，滑稽
./configure --prefix=/usr/local/nginx --user=nginx --group=nginx --with-http_ssl_module --with-http_mp4_module --with-http_flv_module
make && make install
# 创建软链接
ln -s /usr/local/nginx/sbin/nginx /usr/sbin/
# 启动Nginx并查看端口，通过浏览器验证
nginx
netstat -anptu | grep nginx
```
![Nginx_install02](https://github.com/caozhiqiango/movie_project/raw/master/picture/Nginx_install02.PNG)
![Nginx_install03](https://github.com/caozhiqiango/movie_project/raw/master/picture/Nginx_install03.PNG)

## 部署网站

> 呼~ 到部署咯，看官莫慌马上就结束了，感谢您耐心观看

### 1. 安装依赖包

```
cd ~/movie_project
pip3 install -r req.txt
```
![Movie_deploy01](https://github.com/caozhiqiango/movie_project/raw/master/picture/Movie_deploy01.PNG)

### 2. 导入数据

```
# 登录数据库
mysql -uroot -proot
# 创建数据库
create database movie;
use movie;
# 导入数据
source /root/movie_project/movie.sql;
```
![Movie_deploy02](https://github.com/caozhiqiango/movie_project/raw/master/picture/Movie_deploy02.PNG)

### 3. 最后部署

```
# 复制代码到指定目录
cp -r movie_project /usr/local/nginx/html/
# 复制配置文件到指定目录
cp movie_project/nginx.conf /usr/local/nginx/conf/
# 重启Nginx
nginx -s stop
nginx
netstat -anptu | grep nginx
# 运行程序
cd /usr/local/nginx/html/movie_project/
nohup python manage.py runserver -h 127.0.0.1 -p 5001 &
```
![Movie_deploy03](https://github.com/caozhiqiango/movie_project/raw/master/picture/Movie_deploy03.PNG)
![Movie_deploy04](https://github.com/caozhiqiango/movie_project/raw/master/picture/Movie_deploy04.png)
![Movie_deploy05](https://github.com/caozhiqiango/movie_project/raw/master/picture/Movie_deploy05.png)

## 参考致谢

- **在整个部署过程中有参考以下资料，对我帮助很大，在此表示感谢！最后感谢慕课网和主讲老师的辛苦付出，提供这么好的课程，谢谢！**
- CentOS
  - [centos7.0安装教程](https://jingyan.baidu.com/article/a3aad71aa180e7b1fa009676.html)

- Python
  - [CentOS7.3安装Python3.6](http://blog.csdn.net/hobohero/article/details/54381475)
  - [centos 7.3 安装配置python3.6.1](http://www.cnblogs.com/cloud-80808174-sea/p/6902934.html)

- Nginx
  - [【Web】Nginx下载与安装](http://www.cnblogs.com/h--d/p/5756795.html)

- Github图片加载问题
  - [Github：在README.md中插入并显示图片](http://blog.csdn.net/linwh8/article/details/52775374)
  - [在Github的README.md中显示一张图片](http://blog.csdn.net/kongying19910218/article/details/50515990)

[TOC]