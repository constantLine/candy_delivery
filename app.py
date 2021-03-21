from flask import Flask, request, jsonify, abort, make_response, Response
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
import models
errors = []


@app.errorhandler(401)
def say_error(err):
    global errors
    err = errors
    errors = []
    return make_response(jsonify({'Validation error': {'couriers': err}}), 401)


def check_num(sit: bool, ident=0, reg=(0, 0)):
    if sit and (ident < 1 or not isinstance(ident, int)):
        return True
    elif not sit and reg or \
            (len(list(filter(lambda x: isinstance(x, int), reg))) == len(reg)):
        return True
    else:
        return False


def check_str(lst):
    for time in lst:
        x = [i.split(':') for i in time.split('-')]

        if len(x) != 2 or len(x[0]) != 2 or len(x[1]) != 2:
            return True

        try:
            int(x[0][0])
            int(x[0][1])
            int(x[1][0])
            int(x[1][1])
        except ValueError:
            return True

        a, b, c, d = int(x[0][0]), int(x[0][1]), int(x[1][0]), int(x[1][1])

        if not(-1 < a < 24) or not(-1 < c < 24) or \
                not(-1 < b < 60) or not(-1 < d > 60):
            return True

        return False


@app.route('/couriers', methods=['POST'])
def post_couriers():
    base, good = request.get_json()['data'], []
    global errors

    for man in base:
        if check_num(True, ident=man['courier_id']) or check_num(False, reg=man['regions']) or \
                man['courier_type'] not in ['foot', 'car', 'bike'] or check_str(man['working_hours']):
            errors.append({'id': man['courier_id']})
            continue
        good.append({'id': man['courier_id']})

    if errors:
        abort(401)



    return Response({'couriers': good}, status=201, mimetype='application/json')


if __name__ == '__main__':
    app.run()
