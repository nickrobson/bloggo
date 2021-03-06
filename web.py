#!/usr/bin/env python3

from datetime import datetime as date
import json
import os
import re
import ssl
import sys

import db
from flask import Flask, request, session, redirect, url_for, abort, render_template, flash, Blueprint, g

months = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
          'August', 'September', 'October', 'November', 'December']
weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
            'Friday', 'Saturday', 'Sunday']

app = Flask('bloggo')


def rel_date(date):
    now = date.today()
    dt = now - date
    ampm = 'am' if date.hour < 12 else 'pm'
    hour = '%d' % (date.hour % 12 if date.hour % 12 > 0 else 12)
    time = '%s:%02d %s' % (hour, date.minute, ampm)
    if date.year != now.year:
        return '%s, %s, %d %s %d' % (time, weekdays[date.weekday()], date.day,
                                     months[date.month - 1], date.year)
    elif dt.days >= 7:
        return '%s, %s, %d %s' % (time, weekdays[date.weekday()], date.day,
                                  months[date.month - 1])
    elif dt.days > 1:
        return '%d days ago' % dt.days
    elif dt.days == 1:
        return '1 day ago'
    elif dt.seconds >= 7200:
        return '%d hours ago' % (dt.seconds // 3600)
    elif dt.seconds >= 3600:
        return '1 hour ago'
    elif dt.seconds >= 120:
        return '%d minutes ago' % (dt.seconds // 60)
    elif dt.seconds >= 60:
        return '1 minute ago'
    elif dt.seconds >= 2:
        return '%d seconds ago' % dt.seconds
    elif dt.seconds == 1:
        return '1 second ago'
    return 'Just now'


def get_user_info(username):
    user = db.get_user(username)
    if user is None:
        return {'error': 'Invalid username!'}
    res = dict()
    res['username'] = user.username
    res['display'] = user.display
    res['info'] = user.info
    res['image'] = user.image
    return res


def parseInt(s, n):
    try:
        return int(s)
    except Exception as e:
        return n


with open('config.json', 'r') as f:
    app.config.update(json.loads(f.read()))
app.secret_key = app.config['secret']
app.jinja_env.globals.update({
    'rel_date': rel_date,
    'get_user_info': get_user_info
})

bp = Blueprint('main', __name__)
prefix = app.config.get('prefix', '')


@bp.route('/')
@bp.route('/tag/<tag>/')
@bp.route('/user/<user>/')
@bp.route('/user/<user>/tag/<tag>/')
def show_all(user=None, tag=None):
    all_posts = db.list_all_posts(user=user, tag=tag)
    return render_template('show_all.html', posts=all_posts)


@bp.route('/post/<int:postid>/')
@bp.route('/post/<int:postid>/<path:ignored>')
def show_post(postid, ignored=None):
    post = db.get_post(postid)
    if not post:
        abort(404)
    url = url_for('.show_post', postid=postid)
    if request.path != url + post.url:
        return redirect(url + post.url)
    if post.deleted:
        g.postauthor = post.author
        abort(410)
    return render_template('show_post.html', post=post, postid=postid)


@bp.route('/new/', methods=['GET', 'POST'])
@bp.route('/create/', methods=['GET', 'POST'])
def create():
    if request.method == 'GET':
        if not session.get('username'):
            abort(401)
        return render_template('create.html')
    else:
        if not session.get('username'):
            abort(401)
        form = request.form
        if 'title' in form and 'content' in form and 'tags' in form and len(form['title']) and len(form['content']):
            i = db.new_post(form['title'], session['username'], form['content'], form['tags'], date.today())
            return redirect(url_for('.show_post', postid=i))
        return redirect(url_for('.show_all'))


@bp.route('/edit/<int:postid>/', methods=['GET', 'POST'])
@bp.route('/edit/<int:postid>/<path:ignored>', methods=['GET', 'POST'])
def edit(postid, ignored=None):
    post = db.get_post(postid)
    if request.method == 'GET':
        if not post:
            abort(404)
        if post.deleted:
            abort(400)
        if session.get('username') != post.author:
            abort(401)
        return render_template('edit.html', post=post, postid=postid)
    else:
        form = request.form
        if 'title' in form and 'content' in form and 'tags' in form and session.get('username') == post.author:
            if len(form['title']) and len(form['content']):
                db.edit_post(post, form['title'], form['content'], form['tags'])
                return redirect(url_for('.show_post', postid=postid))
            missing = []
            if len(form['title']) == 0:
                missing.append('title')
            if len(form['content']) == 0:
                missing.append('content')
            flash('Missing ' + ' & '.join(missing) + '!')
            post.title = form['title']
            post.content = form['content']
            post.tags = form['tags'].split(' ')
            return render_template('edit.html', post=post, postid=postid)
        return redirect(url_for('.show_all'))


@bp.route('/delete/<int:postid>/', methods=['GET', 'POST'])
@bp.route('/delete/<int:postid>/<path:ignored>', methods=['GET', 'POST'])
def delete(postid, ignored=None):
    post = db.get_post(postid)
    if request.method == 'GET':
        if not post:
            abort(404)
        if post.deleted:
            abort(400)
        if session.get('username') == post.author:
            return render_template('delete.html', post=post, postid=postid)
        abort(401)
    form = request.form
    if post and not post.deleted and session.get('username') == post.author:
        db.delete_post(post)
        flash('Deleted post')
        return redirect(url_for('.show_all'))
    abort(400)


@bp.route('/restore/<int:postid>/', methods=['GET', 'POST'])
@bp.route('/restore/<int:postid>/<path:ignored>', methods=['GET', 'POST'])
def restore(postid, ignored=None):
    post = db.get_post(postid)
    if not post.deleted:
        return redirect(url_for('.show_post', postid=postid))
    if request.method == 'GET':
        if not post:
            abort(404)
        if not post.deleted:
            abort(400)
        if session.get('username') != post.author:
            abort(401)
        return render_template('restore.html', post=post, postid=postid)
    form = request.form
    if post and session.get('username') == post.author:
        db.restore_post(post)
        flash('Restored post ' + post.title)
        return redirect(url_for('.show_post', postid=postid))
    abort(403)


@bp.route('/comment/', methods=['POST'])
def comment():
    if not app.config.get('allow_comments', True):
        abort(403)
    form = request.form
    if form.get('postid') and form.get('author') and form.get('content'):
        postid = form.get('postid')
        author = form.get('author')
        content = form.get('content')
        post = db.get_post(postid)
        if post:
            reply_to = parseInt(form.get('reply_to', 0), 0)
            db.new_comment(postid, author, content, date.today(), reply_to)
            return redirect(url_for('.show_post', postid=postid))
        abort(404)
    abort(400)


@bp.route('/register/', methods=['GET', 'POST'])
def register():
    if not app.config['allow_register']:
        abort(403)
    if request.method == 'GET':
        if session.get('username'):
            return redirect(url_for('.show_all'))
        else:
            return render_template('register.html', username='', display='')
    else:
        form = request.form
        if session.get('username'):
            return redirect(url_for('.show_all'))
        elif len(form.get('username', '')) and len(form.get('password', '')) \
                and len(form.get('display', '')):
            username = form['username']
            password = form['password']
            display = form['display']

            if not re.match('^[a-zA-Z]{3,20}$', username):
                flash('Invalid username. Must be alphabetic with ' +
                      '3-20 characters.')
                return render_template('register.html',
                                       username=username, display=display)

            user = db.get_user(username)
            if user:
                flash('Username is taken!')
                return render_template('register.html',
                                       username=username, display=display)
            else:
                db.new_user(username, password, display, True)
                flash('Registered new account: ' + username + ', ' + display)
                return redirect(url_for('.show_all'))
        else:
            missing = []
            if len(form.get('username', '')) == 0:
                missing.append('username')
            if len(form.get('password', '')) == 0:
                missing.append('password')
            if len(form.get('display', '')) == 0:
                missing.append('display name')
            joined = ' & '.join(missing) if len(missing) < 3 else \
                     '%s, %s & %s' % (missing[0], missing[1], missing[2])
            flash('Missing ' + joined + '!')
            return redirect(url_for('.register'))


@bp.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if session.get('username'):
            return redirect(url_for('.show_all'))
        else:
            return render_template('login.html')
    else:
        form = request.form
        if session.get('username'):
            return redirect(url_for('.show_all'))
        elif len(form.get('username', '')) and len(form.get('password', '')):
            username = form['username']
            password = form['password']

            user = db.get_user_with_pass(username, password)
            if user:
                session['username'] = username
                session['display'] = user.display
                flash('Logged in as: ' + user.display)
                return redirect(url_for('.show_all'))
            else:
                flash('Invalid username or password!')
        return redirect(url_for('.login'))


@bp.route('/logout/')
def logout():
    session.pop('display', None)
    if session.pop('username', None):
        flash('You have been logged out.')
    return redirect(url_for('.show_all'))

@bp.route('/settings/', methods=['GET', 'POST'])
def settings():
    username = session.get('username')
    if not username:
        abort(401)
    user_info = get_user_info(username)
    if request.method == 'GET':
        return render_template('settings.html', user_info = user_info)
    form = request.form
    files = request.files
    to_update = {}
    new_display = form.get('display')
    new_description = form.get('description')
    new_password = form.get('npassword')
    if new_password and len(new_password):
        curr_password = form.get('password')
        if not curr_password or not len(curr_password):
            flash('You need to enter your current password!')
        elif new_password == form.get('cnpassword'):
            to_update['password'] = new_password
            to_update['old_password'] = curr_password
        else:
            flash('The "new" passwords that you entered do not match!')
    if new_display and len(new_display) and new_display != user_info['display']:
        to_update['display'] = new_display
    if new_description and len(new_description) and new_description != user_info['info']:
        to_update['info'] = new_description
    if db.update_user(username, to_update, flash):
        flash('Successfully updated!')
        if 'display' in to_update:
            session['display'] = to_update['display']
    return redirect(url_for('.settings'))


@app.errorhandler(400)
def error_bad_request(e):
    return render_template('error400.html'), 400


@app.errorhandler(401)
def error_unauthorized(e):
    return render_template('error401.html'), 401


@app.errorhandler(403)
def error_forbidden(e):
    return render_template('error403.html'), 403


@app.errorhandler(404)
def error_page_not_found(e):
    return render_template('error404.html'), 404


@app.errorhandler(410)
def error_page_gone(e):
    return render_template('error410.html'), 410


@app.errorhandler(500)
def error_server_error(e):
    return render_template('error500.html'), 500


app.register_blueprint(bp, url_prefix=prefix)

if __name__ == "__main__":
    sslctx = None
    if 'ssl' in app.config:
        sslconfig = app.config['ssl']
        sslctx = ssl.SSLContext(protocol = ssl.PROTOCOL_SSLv23)
        sslctx.load_cert_chain(sslconfig['certfile'], sslconfig.get('keyfile'), sslconfig.get('password'))
    app.run(host='0.0.0.0', port=app.config.get('port', 5000), debug=app.config.get('debug', False), ssl_context=sslctx)
