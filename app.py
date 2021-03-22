from flask import Flask, request, jsonify, abort, make_response
from werkzeug.wrappers import BaseResponse as Response
from config import *
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

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


@app.errorhandler(400)
def say_error(err):
    global errors
    err = errors
    errors = []
    if request.path == '/couriers':
        return make_response(jsonify({'validation error': {'couriers': err}}))
    elif request.path == '/orders':
        return make_response(jsonify({'validation error': {'orders': err}}))
    else:
        return Response(response="HTTP 400 Bad Request", status=400, mimetype="application/json")


@app.route('/couriers', methods=['POST'])
def post_couriers():
    base, good_id = request.get_json()['data'], []
    global errors

    for man in base:
        if check_num(True, ident=man['courier_id']) or \
                check_num(False, reg=man['regions']) or \
                not (check_type(man['courier_type'])) or \
                check_str(man['working_hours']):
            errors.append({'id': man['courier_id']})
            continue

        good_id.append({'id': man['courier_id']})

    if errors:
        abort(400)

    for c in base:
        x = Courier(id=c['courier_id'],
                    type=c['courier_type'],
                    regions=str(c['regions']),
                    working_hours=str(c['working_hours']))
        if c['courier_type'] == 'foot':
            x.max_weight = 10
            x.weight_now = 0.0
        elif c['courier_type'] == 'car':
            x.max_weight = 15
            x.weight_now = 0.0
        elif c['courier_type'] == 'bike':
            x.max_weight = 50
            x.weight_now = 0.0

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
            if not (check_num(False, reg=value)):
                change.regions = value
            else:
                abort(400)
        elif key == 'working_hours':
            if not (check_str(value)):
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


@app.route('/orders', methods=['POST'])
def post_orders():
    base, good_id = request.get_json()['data'], []
    global errors

    for order in base:
        if check_num(True, ident=order['order_id']) or \
                check_num(True, ident=order['region']) or \
                not (isinstance(order['weight'], float) and 0.01 <= order['weight'] <= 50) or \
                check_str(order['delivery_hours']):
            errors.append({'id': order['order_id']})
            continue

        good_id.append({'id': order['order_id']})

    if errors:
        abort(400)

    for c in base:
        x = Order(id=c['order_id'],
                  weight=round(c['weight'], 2),
                  region=str(c['region']),
                  delivery_hours=str(c['delivery_hours']))
        db.session.add(x)
    db.session.commit()

    return make_response(jsonify({'orders': good_id}), 201)


@app.route('/orders/assign', methods=['POST'])
def orders_assign():
    c_id = request.get_json()['courier_id']
    good_id = []
    if check_num(True, ident=c_id):
        abort(400)

    courier = Courier.query.get(c_id)
    for order in Order.query.all():
        if courier is order.courier or order.courier is not None:
            continue
        if order.region in trans_regs(courier.regions) and \
                order.weight + courier.weight_now <= courier.max_weight:

            order_time = trans_minutes(order.delivery_hours)
            for ok_time in trans_minutes(courier.working_hours):
                if order.id in good_id:
                    break
                for q_time in order_time:
                    if ok_time[0] < q_time[0] < ok_time[1]:
                        order.courier = courier
                        courier.weight_now += order.weight
                        good_id.append({'id': order.id})
                        break

    assign_time = datetime.utcnow().isoformat()
    if not good_id:
        return make_response(jsonify({'orders': good_id}), 200)
    else:

        return make_response(jsonify({'orders': good_id, 'assign_time': assign_time}), 200)


if __name__ == '__main__':
    app.run()
