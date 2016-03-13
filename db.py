import datetime
import os
import sqlite3
import re
from markdown2 import Markdown
from passlib.hash import pbkdf2_sha512 as pbk

markdown = Markdown(extras=['fenced-code-blocks', 'footnotes', 'tables'])


def get_conn():
    return sqlite3.connect('bloggo.db')


if not os.path.exists('bloggo.db'):
    co = get_conn()
    cu = co.cursor()
    cu.execute('create table users (id integer primary key, \
                username text, password text, display text)')
    cu.execute('create table posts (id integer primary key, \
                title text, author text, content text, html text, \
                tags text, date text, url text)')
    co.commit()
    co.close()


class User(object):

    def __init__(self, data):
        self.id = data[0]
        self.username = data[1]
        self.password = data[2]
        self.display = data[3]


class Post(object):

    def __init__(self, data):
        self.id = data[0]
        self.title = data[1]
        self.author = data[2]
        self.content = data[3]
        self.html = data[4]
        self.tags = data[5]
        self.date = datetime.datetime.strptime(data[6], '%Y-%m-%d %H:%M:%S.%f')
        self.url = data[7]

    def get_display_name(self):
        user = get_user(self.author)
        return user.display if user else self.author


def get_users():
    co = get_conn()
    cu = co.cursor()
    users = cu.execute('select * from users').fetchall()
    co.close()
    return map(lambda u: User(u), users)


def get_user(username):
    co = get_conn()
    cu = co.cursor()
    cu.execute('select * from users where username=?', (username,))
    user = cu.fetchone()
    co.close()
    return User(user) if user else None


def get_user_with_pass(username, password):
    u = get_user(username)
    if u is not None and pbk.verify(password, u.password):
        return u
    else:
        return None


def new_user(username, password, display):
    co = get_conn()
    cu = co.cursor()
    vals = (username, pbk.encrypt(password), display)
    cu.execute('insert into users (username, password, display) \
                VALUES (?, ?, ?)', vals)
    id = cu.lastrowid
    co.commit()
    co.close()
    return id


def post_of_id(i):
    co = get_conn()
    cu = co.cursor()
    post = cu.execute('select * from posts where id=?', (i,)).fetchone()
    co.close()
    return Post(post) if post else None


def list_all_posts():
    co = get_conn()
    cu = co.cursor()
    posts = cu.execute('select * from posts').fetchall()
    co.close()
    return map(lambda p: Post(p), posts)


def new_post(title, author, content, tags, date):
    html = markdown.convert(content)
    url = '%s' % re.sub('[^a-zA-Z0-9 ]', '', title).replace(' ', '-').lower()
    co = get_conn()
    cu = co.cursor()
    post = (title, author, content, html, str(tags), date, url)
    cu.execute('insert into posts (title, author, content, html, tags, date, url) \
                VALUES (?, ?, ?, ?, ?, ?, ?)', post)
    id = cu.lastrowid
    co.commit()
    co.close()
    return id
