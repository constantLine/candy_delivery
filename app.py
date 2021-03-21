from flask import Flask, request, jsonify, abort, make_response
from werkzeug.wrappers import BaseResponse as Response
from config import Config, check_num, check_str, check_type
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
from models import Courier, Order
errors = []
example_json = {
    'courier_id': 0,
    'courier_type': 'a',
    'regions': [],
    'working_hours': 'a'
}


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
                not(check_type(man['courier_type'])) or\
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

    return make_response(jsonify({'couriers': good_id}), 201)


@app.route('/couriers/<int:xid>', methods=['PATCH'])
def patch_courier(xid):
    json, change = request.get_json(), Courier.query.get(xid)
    global example_json
    response = example_json
    response['courier_id'] = xid
    for key, value in json.items():
        if key == 'courier_type':
            if check_type(value):
                change.type = value
            else:
                abort(400)
        elif key == 'regions':
            if not(check_num(False, reg=value)):
                change.regions = value
            else:
                abort(400)
        elif key == 'working_hours':
            if not(check_str(value)):
                change.working_hours = value
            else:
                abort(400)

        response['courier_type'] = change.type
        response['regions'] = change.regions
        response['working_hours'] = change.working_hours
    change.regions = str(change.regions)
    change.working_hours = str(change.working_hours)
    db.session.add(change)
    db.session.commit()
    return make_response(jsonify(response), 200)


if __name__ == '__main__':
    app.run()
