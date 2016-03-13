import datetime
import os
import re
from flask.ext.sqlalchemy import SQLAlchemy
from sqlalchemy_utils.types.password import PasswordType as PasswordType
from markdown2 import Markdown
from web import app

markdown = Markdown(extras=['fenced-code-blocks',
                            'footnotes',
                            'tables'])

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(PasswordType(schemes=['pbkdf2_sha512']))
    display = db.Column(db.String(120))

    def __init__(self, username, password, display):
        self.username = name
        self.password = password
        self.display = display

    def __repr__(self):
        return self.display


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    author = db.Column(db.String(120))
    content = db.Column(db.Text())
    html = db.Column(db.Text())
    tags = db.Column(db.String(120))
    date = db.Column(db.DateTime())
    url = db.Column(db.String(120))

    def __init__(self, title, author, content, html, tags, date, url):
        super(Post, self).__init__()
        self.title = title
        self.author = author
        self.content = content
        self.html = html
        self.tags = tags
        self.date = date
        self.url = url

    def get_display_name(self):
        user = get_user(self.author)
        return user.display if user else self.author


def get_users():
    return User.query.all()


def get_user(username):
    u = filter(lambda u: u.username.lower() == username.lower(), get_users())
    return None if len(u) == 0 else u[0]


def get_user_with_pass(username, password):
    u = get_user(username)
    if u is not None and u.password == password:
        return u
    else:
        return None


def new_post(title, author, content, tags, date):
    ctx = Content(i, title, author, content, tags, date)
    db.session.add(ctx)
    db.session.commit()


def post_of_id(i):
    return Post.query.filter_by(id=i)


def list_all_posts():
    return Post.query.all()
