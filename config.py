import os
from datetime import datetime
basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False


def check_num(sit: bool, ident=0, reg=()):
    if sit and (ident < 1 or not isinstance(ident, int)):
        return True
    elif not sit and \
            not reg or not (len(list(filter(lambda x: isinstance(x, int) and x > 0, reg))) == len(reg)):
        return True
    else:
        return False


def check_str(lst):
    for time in lst:
        x = [i.split(':') for i in time.split('-')]

        if len(x) != 2 or len(x[0]) != 2 or len(x[1]) != 2:
            return True

        try:
            x[0][0] = int(x[0][0])
            x[0][1] = int(x[0][1])
            x[1][0] = int(x[1][0])
            x[1][1] = int(x[1][1])
        except ValueError:
            return True

        a, b, c, d = int(x[0][0]), int(x[0][1]), int(x[1][0]), int(x[1][1])

        if not(-1 < a < 24) or not(-1 < c < 24) or \
                not(-1 < b < 60) or not(-1 < d < 60):
            return True

        return False


def check_type(value):
    return value in ['foot', 'car', 'bike']


def trans_regs(regs: str):
    return [int(i) for i in regs[1:-1].split(', ')]


def trans_minutes(hours: str):
    list_strings = [i for i in hours[1:-1].split(', ')]
    for i in range(len(list_strings)):
        s = list_strings[i][1:-1]
        s = [j.split(':') for j in s.split('-')]
        list_strings[i] = (int(s[0][0])*60 + int(s[0][1]), int(s[1][0])*60 + int(s[1][1]))
    return list_strings


def check_date(s: str):
    try:
        ret = datetime.fromisoformat(s[:-1]+'0000')
    except ValueError:
        return True

    return False


def trans_date(s: str):
    return [j[1:-1] for j in [i for i in s[1:-1].split(', ')]]


def get_weight(s: str):
    ex = {  # example
        'foot': 10,
        'bike': 15,
        'car': 50
    }
    for key, value in ex.items():
        if key == s:
            return ex[key]


def type_k(s: str):
    if s == 'foot':
        return 2
    elif s == 'bike':
        return 5
    else:
        return 9
