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
assign_time = datetime.utcnow().isoformat()
example_json = {
    'courier_id': 0,
    'courier_type': '_',
    'regions': [],
    'working_hours': '_'
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
    global assign_time
    if check_num(True, ident=c_id) or Courier.query.get(c_id) is None:  # проверка на валидность данного id
        abort(400)

    courier = Courier.query.get(c_id)
    if courier.orders.filter_by(complete=False).first() is not None:
        resp = make_response(jsonify({'orders': courier.orders.filter_by(complete=False).all(),
                                      'assign_time': assign_time}), 200)
        resp.headers = {'Content-Type': 'application/json'}
        return resp

    assign_time = datetime.utcnow().isoformat()

    for order in Order.query.order_by(Order.weight).all():  # перебор всех заказов от меньшего веса к наибольшему
        if order.courier is not None:  # если у заказа уже есть доставщик тот же/другой, то пропускаем его
            continue
        if order.region in trans_regs(courier.regions) and \
                order.weight + courier.weight_now <= courier.max_weight:  # проверка на валидность региона и веса

            order_time = trans_minutes(order.delivery_hours)  # перевод str из бд в [tuple(start:int, end:int),..,tuple]
            for ok_time in trans_minutes(courier.working_hours):  # перебор рабочих часов курьера

                if order.id in good_id:  # если на предыдущей итерации нижнего for был добавлен данный заказ, то выход
                    break                # из верхнего фора

                for q_time in order_time:  # перебор времён заказа
                    if ok_time[0] < q_time[0] < ok_time[1] or\
                            ok_time[0] < q_time[1] < ok_time[1]:  # проверка на валидность времени
                        # исполнение присваивания заказа курьеру и указание assign time
                        order.courier = courier
                        order.assign_time = assign_time
                        courier.weight_now = courier.weight_now + order.weight
                        good_id.append({'id': order.id})
                        break

    db.session.commit()
    response1 = make_response(jsonify({'orders': good_id, 'assign_time': assign_time[:22] + "Z"}), 200)
    response1.headers = {'Content-Type': 'application/json'}
    response2 = make_response(jsonify({'orders': good_id}), 200)
    response2.headers = {'Content-Type': 'application/json'}
    if not good_id:
        return response2
    else:

        return response1


@app.route('/orders/complete', methods=['POST'])
def complete_order():
    c_id, o_id = request.get_json()['courier_id'], request.get_json()['order_id']
    compl_time = request.get_json()['complete_time']
    global assign_time

    if check_num(True, ident=c_id) or check_num(True, ident=o_id) or \
            Courier.query.get(c_id) is None or Order.query.get(o_id) is None or \
            Order.query.get(o_id).courier is None or check_date(compl_time):
        abort(400)

    courier, order, compl_time = Courier.query.get(c_id), Order.query.get(o_id), datetime.fromisoformat(compl_time)
    if order.courier is courier:
        if courier.orders.filter_by(complete=True).first() is None:
            k = compl_time - datetime.fromisoformat(assign_time)
            order.delta_time = k.total_seconds()
        else:
            k = compl_time - datetime.fromisoformat(order.assign_time)
            order.delta_time = k.total_seconds()
            order.complete = True
            courier.weight_now = courier.weight_now - order.weight
            db.session.commit()
        return make_response(jsonify({'order_id': o_id}), 200)
    else:
        abort(400)


@app.route('/couriers/<int:xid>', methods=['GET'])
def get_courier(xid):
    pass


if __name__ == '__main__':
    app.run()
