from flask import Flask, request, jsonify, abort, make_response, Response
from config import Config, check_num, check_str
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
from models import Courier, Order
errors = []


@app.errorhandler(401)
def say_error(err):
    global errors
    err = errors
    errors = []
    return make_response(jsonify({'Validation error': {'couriers': err}}), 401)


@app.route('/couriers', methods=['POST'])
def post_couriers():
    base, good_id = request.get_json()['data'], []
    global errors

    for man in base:
        if check_num(True, ident=man['courier_id']) or\
                check_num(False, reg=man['regions']) or \
                man['courier_type'] not in ['foot', 'car', 'bike'] or\
                check_str(man['working_hours']):
            errors.append({'id': man['courier_id']})
            continue

        good_id.append({'id': man['courier_id']})

    if errors:
        abort(401)

    for c in base:
        x = Courier(id=c['courier_id'],
                    type=c['courier_type'],
                    regions=str(c['regions']),
                    working_hours=str(c['working_hours']))
        db.session.add(x)
    db.session.commit()

    return Response({'couriers': good_id}, status=201, mimetype='application/json')


if __name__ == '__main__':
    app.run()
