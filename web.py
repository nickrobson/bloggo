#!/usr/bin/env python

from datetime import datetime as date
import json
import os
import sys
import db
from flask import Flask, request, session, g, redirect, url_for, abort, \
                    render_template, flash

months = ['January', 'February', 'March', 'April', 'May', 'June',
          'July', 'August', 'September', 'October', 'November', 'December']

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
    elif dt.seconds >= 60:
        return '%d minutes ago' % (dt.seconds // 60)
    elif dt.seconds >= 2:
        return '%d seconds ago' % dt.seconds
    elif dt.seconds == 1:
        return '1 second ago'
    else:
        return 'Just now'

app = Flask('bloggo')
app.config['name'] = os.environ.get('BLOGGO_NAME', 'bloggo')
app.secret_key = os.environ.get('BLOGGO_SECRET', 'super secret key')
app.jinja_env.globals.update(rel_date=rel_date)


@app.route('/')
def show_all():
    all_posts = db.list_all_posts()
    return render_template('show_all.html',
                           name=app.config['name'], posts=all_posts)


@app.route('/post/<int:postid>/')
@app.route('/post/<int:postid>/<path:ignored>')
def show_post(postid, ignored=None):
    post = db.post_of_id(postid)
    if post:
        if request.path != '/post/%d/%s' % (post.id, post.url):
            return redirect('/post/%d/%s' % (post.id, post.url))
    return render_template('show_post.html',
                           name=app.config['name'], post=post, postid=postid)


@app.route('/new/', methods=['GET', 'POST'])
@app.route('/create/', methods=['GET', 'POST'])
def create():
    if request.method == 'GET':
        if True or session.get('username'):
            return render_template('create.html', name=app.config['name'])
        else:
            abort(401)
    else:
        form = request.form
        if 'username' in session and 'title' in form and 'content' \
           in form and 'tags' in form:
            i = db.new_post(form['title'], session['username'],
                            form['content'], form['tags'], date.today())
            return redirect(url_for('show_post', postid=i))
        else:
            return redirect(url_for('create'))


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if session.get('username'):
            return redirect(url_for('show_all'))
        else:
            return render_template('login.html', name=app.config['name'])
    else:
        if 'username' in request.form and 'password' in request.form:
            username = request.form['username']
            password = request.form['password']

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
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('show_all'))

if __name__ == "__main__":
    app.run(debug=True, port=8080)
