import datetime
import os
import re
import auth
import markdown2

base_dir = 'posts'
markdown = markdown2.Markdown(extras=['fenced-code-blocks',
                                      'footnotes',
                                      'tables'])


class Content(object):

    def __init__(self, i, title, author, content, tags, date):
        super(Content, self).__init__()
        self.i = i
        self.title = title
        self.author = author
        self.content = content
        self.html = markdown.convert(content)
        self.tags = tags
        self.date = date
        self.url = '/%d/%s' % (i, re.sub('[^a-zA-Z0-9\\s]',
                                         '', title).replace(' ', '-'))

    def save(self):
        dname = '%s/%s/' % (base_dir, self.i)
        if not os.path.exists(dname):
            os.mkdir(dname)
        if os.path.exists(dname + 'title'):
            os.remove(dname + 'title')
        with open(dname + 'title', 'w+') as f:
            f.write(self.title)
        if os.path.exists(dname + 'author'):
            os.remove(dname + 'author')
        with open(dname + 'author', 'w+') as f:
            f.write(self.author)
        if os.path.exists(dname + 'content'):
            os.remove(dname + 'content')
        with open(dname + 'content', 'w+') as f:
            f.write(self.content)
        if os.path.exists(dname + 'tags'):
            os.remove(dname + 'tags')
        with open(dname + 'tags', 'w+') as f:
            f.write('\n'.join(self.tags) + '\n')
        if os.path.exists(dname + 'date'):
            os.remove(dname + 'date')
        with open(dname + 'date', 'w+') as f:
            f.write(str(self.date))

    def get_display_name(self):
        user = auth.get_user(self.author)
        return user.display if user else self.author


def find_next_id():
    i = 1
    if os.path.isfile('next_id'):
        with open('next_id', 'r') as f:
            i = int(f.read())
    while os.path.exists('%s/%s/' % (base_dir, i)):
        i += 1
    with open('next_id', 'w+') as f:
        f.write(str(i + 1))
    return i


def new_post(title, author, content, tags, date):
    i = find_next_id()
    ctx = Content(i, title, author, content, tags, date)
    ctx.save()
    return i


def read_of_id(i):
    dname = '%s/%s/' % (base_dir, i)
    if os.path.isdir(dname):
        with open(dname + 'title', 'r') as f:
            title = f.read()
        with open(dname + 'author', 'r') as f:
            author = f.read()
        with open(dname + 'content', 'r') as f:
            content = f.read()
        with open(dname + 'tags', 'r') as f:
            tags = f.read().splitlines()
        with open(dname + 'date', 'r') as f:
            date = datetime.datetime.strptime(f.read(), '%Y-%m-%d %H:%M:%S.%f')
        return Content(i, title, author, content, tags, date)


def toInt(s):
    try:
        return int(s)
    except Exception, e:
        return None


def list_all_ids():
    dname = '%s' % base_dir
    return filter(None, map(toInt, os.listdir(dname)))


def list_all_posts():
    posts = []
    for i in list_all_ids():
        posts.append(read_of_id(i))
    return posts
