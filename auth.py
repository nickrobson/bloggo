import os


class User(object):
    def __init__(self, username, password, display):
        super(User, self).__init__()
        self.username = username
        self.password = password
        self.display = display


users = None


def init(config):
    global users
    users = map(lambda u: User(u['username'], u['password'],
                u['display']), config['auth'])


def get_user(username):
    u = filter(lambda u: u.username.lower() == username.lower(), users)
    return None if len(u) == 0 else u[0]


def get_user_with_pass(username, password):
    u = get_user(username)
    if u is not None and u.password == password:
        return u
    else:
        return None
