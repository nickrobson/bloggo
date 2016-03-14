#!/usr/bin/env python

from datetime import datetime as date
import json
import os
import re
import sys
import db
from flask import Flask, request, session, g, redirect, url_for, abort, \
                    render_template, flash

months = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
          'August', 'September', 'October', 'November', 'December']

weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday',
            'Friday', 'Saturday', 'Sunday']


def rel_date(date):
    now = date.today()
    dt = now - date
    ampm = 'am' if date.hour < 12 else 'pm'
    hour = '%02d' % (date.hour % 12 if date.hour % 12 > 0 else 12)
    time = '%s:%02d %s' % (hour, date.minute, ampm)
    if date.year != now.year:
        return '%s, %s, %d %s %d' % (time, weekdays[date.weekday()], date.day,
                                     months[date.month - 1], date.year)
    elif dt.days >= 7:
        return '%s, %s, %d %s' % (time, weekdays[date.weekday()], date.day,
                                  months[date.month - 1])
    elif dt.days >= 1:
        return '%d days ago' % dt.days
    elif dt.seconds >= 3600:
        return '%d hours ago' % (dt.seconds // 3600)
    elif dt.seconds >= 120:
        return '%d minutes ago' % (dt.seconds // 60)
    elif dt.seconds >= 60:
        return '1 minute ago'
    elif dt.seconds >= 2:
        return '%d seconds ago' % dt.seconds
    elif dt.seconds == 1:
        return '1 second ago'
    else:
        return 'Just now'


def parseInt(s, n):
    try:
        return int(s)
    except Exception, e:
        return n


app = Flask('bloggo')


def app_cfg():
    return app.config


with open('config.json', 'r') as f:
    app.config.update(json.loads(f.read()))
app.secret_key = app.config['secret']
app.jinja_env.globals.update(rel_date=rel_date)
app.jinja_env.globals.update(app_cfg=app_cfg)

@app.route('/')
def show_all():
    all_posts = db.list_all_posts()
    return render_template('show_all.html', name=app.config['name'],
                           posts=all_posts)


@app.route('/post/<int:postid>/')
@app.route('/post/<int:postid>/<path:ignored>')
def show_post(postid, ignored=None):
    post = db.get_post(postid)
    if post:
        if request.path != '/post/%d/%s' % (post.id, post.url):
            return redirect('/post/%d/%s' % (post.id, post.url))
    return render_template('show_post.html', name=app.config['name'],
                           post=post, postid=postid)


@app.route('/new/', methods=['GET', 'POST'])
@app.route('/create/', methods=['GET', 'POST'])
def create():
    if request.method == 'GET':
        if session.get('username'):
            return render_template('create.html', name=app.config['name'])
        else:
            abort(401)
    else:
        form = request.form
        if 'title' in form and 'content' in form and 'tags' in form and \
           len(form['title']) and len(form['content']):
            i = db.new_post(form['title'], session['username'],
                            form['content'], form['tags'], date.today())
            return redirect(url_for('show_post', postid=i))
        else:
            return redirect(url_for('show_all'))


@app.route('/edit/<int:postid>/', methods=['GET', 'POST'])
@app.route('/edit/<int:postid>/<path:ignored>', methods=['GET', 'POST'])
def edit(postid, ignored=None):
    post = db.get_post(postid)
    if request.method == 'GET':
        if not post or session.get('username') == post.author:
            return render_template('edit.html', name=app.config['name'],
                                   post=post, postid=postid)
        else:
            abort(401)
    else:
        form = request.form
        if 'title' in form and 'content' in form and 'tags' in form and \
           session.get('username') == post.author:
            if len(form['title']) and len(form['content']):
                db.edit_post(post, form['title'], form['content'],
                             form['tags'], date.today())
                return redirect(url_for('show_post', postid=postid))
            else:
                missing = []
                if len(form['title']) == 0:
                    missing.append('title')
                if len(form['content']) == 0:
                    missing.append('content')
                flash('Missing ' + ' & '.join(missing) + '!')
                post.title = form['title']
                post.content = form['content']
                post.tags = form['tags'].split(' ')
                return render_template('edit.html', name=app.config['name'],
                                       post=post, postid=postid)
        else:
            return redirect(url_for('show_all'))


@app.route('/delete/<int:postid>/', methods=['GET', 'POST'])
@app.route('/delete/<int:postid>/<path:ignored>', methods=['GET', 'POST'])
def delete(postid, ignored=None):
    post = db.get_post(postid)
    if request.method == 'GET':
        if not post or session.get('username') == post.author:
            return render_template('delete.html', name=app.config['name'],
                                   post=post, postid=postid)
        else:
            abort(401)
    else:
        form = request.form
        if post and session.get('username') == post.author:
            db.delete_post(post)
            flash('Deleted post')
        return redirect(url_for('show_all'))


@app.route('/comment/', methods=['POST'])
def comment():
    form = request.form
    if form.get('postid') and form.get('author') and form.get('content'):
        postid = form.get('postid')
        author = form.get('author')
        content = form.get('content')
        post = db.get_post(postid)
        if post:
            reply_to = parseInt(form.get('reply_to', 0), 0)
            db.new_comment(postid, author, content, date.today(), reply_to)
            return redirect(url_for('show_post', postid=postid))
        else:
            abort(404)
    else:
        abort(400)


@app.route('/register/', methods=['GET', 'POST'])
def register():
    if not app.config['allow_register']:
        abort(401)
    if request.method == 'GET':
        if session.get('username'):
            return redirect(url_for('show_all'))
        else:
            return render_template('register.html', name=app.config['name'],
                                   username='', display='')
    else:
        form = request.form
        if session.get('username'):
            return redirect(url_for('show_all'))
        elif len(form.get('username', '')) and len(form.get('password', '')) \
                and len(form.get('display', '')):
            username = form['username']
            password = form['password']
            display = form['display']

            if not re.match('^[a-zA-Z]{3,20}$', username):
                flash('Invalid username. Must be alphabetic with ' +
                      '3-20 characters.')
                return render_template('register.html',
                                       name=app.config['name'],
                                       username=username, display=display)

            user = db.get_user(username)
            if user:
                flash('Username is taken!')
                return render_template('register.html',
                                       name=app.config['name'],
                                       username=username, display=display)
            else:
                db.new_user(username, password, display, True)
                flash('Registered new account: ' + username + ', ' + display)
                return redirect(url_for('show_all'))
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
            return redirect(url_for('register'))


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if session.get('username'):
            return redirect(url_for('show_all'))
        else:
            return render_template('login.html', name=app.config['name'])
    else:
        form = request.form
        if session.get('username'):
            return redirect(url_for('show_all'))
        elif len(form.get('username', '')) and len(form.get('password', '')):
            username = form['username']
            password = form['password']

            user = db.get_user_with_pass(username, password)
            if user:
                session['username'] = username
                session['display'] = user.display
                flash('Logged in as: ' + user.display)
                return redirect(url_for('show_all'))
            else:
                flash('Invalid username or password!')
                return render_template('login.html', name=app.config['name'])
        return redirect(url_for('login'))


@app.route('/logout/')
def logout():
    if session.pop('username', None):
        flash('You have been logged out.')
    return redirect(url_for('show_all'))

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=app.config['port'])
