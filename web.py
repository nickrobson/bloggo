#!/usr/bin/env python

from datetime import datetime as date
import json
import os
import sys
import markdown2
import auth
import posts
from flask import Flask, request, session, g, redirect, url_for, abort, \
                    render_template, flash

app = Flask('bloggo')

if not os.path.isfile('config.json..'):
    print '############################'
    print '### Missing config.json! ###'
    print '############################'
    sys.exit(1)

with open('config.json', 'r') as f:
    app.config.update(json.loads(f.read()))

@app.route('/')
def show_all():
    all_posts = posts.list_all_posts()
    return render_template('show_all.html',
                           name=app.config['name'], posts=all_posts)


@app.route('/post/<int:postid>/')
@app.route('/post/<int:postid>/<path:ignored>')
def show_post(postid, ignored=None):
    post = posts.read_of_id(postid)
    if post:
        app.logger.debug(request.path)
        app.logger.debug(post.url)
        if request.path != '/post' + post.url:
            return redirect('/post' + post.url)
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
        if 'title' in form and 'content' in form and 'tags' in form:
            i = posts.new_post(form['title'], session['username'],
                               form['content'], form['tags'].split(' '),
                               date.today())
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

            user = auth.get_user_with_pass(username, password)
            if user:
                return render_template('login.html',
                                       name=app.config['name'],
                                       error='Invalid username or password')
            else:
                session['username'] = username
                session['display'] = user.display
                flash('Logged in as: ' + user.display)
                return redirect(url_for('show_all'))
        return redirect(url_for('login'))


@app.route('/logout/')
def logout():
    session.pop('username', None)
    flash('You have been logged out')
    return redirect(url_for('show_all'))


if os.path.isfile('secret'):
    app.secret_key = os.urandom(24)
    with open('secret', 'w+') as f:
        f.write(repr(app.secret_key))
else:
    with open('secret', 'r') as f:
        app.secret_key = eval(f.read())

auth.init(app.config)

if __name__ == "__main__":
    app.run(port=80)
