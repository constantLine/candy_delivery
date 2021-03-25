from flask import Flask, request, jsonify, abort, make_response
from werkzeug.wrappers import BaseResponse as Response
from flaskr.config import *
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
from flaskr.models import Courier, Order

errors = []
assign_time = datetime.utcnow().isoformat()


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
                    working_hours=str(c['working_hours']),
                    weight_now=0.0,
                    max_weight=get_weight(c['courier_type']))
        db.session.add(x)
    db.session.commit()

    return make_response(jsonify({'couriers': good_id}), 201)


@app.route('/couriers/<int:xid>', methods=['PATCH'])
def patch_courier(xid):
    json, change, response = request.get_json(), Courier.query.get(xid), {'courier_id': xid}

    for key, value in json.items():
        if key == 'courier_type':
            if not check_type(value):
                abort(400)

            if change.type == value:
                continue
            change.type = value
            change.max_weight = get_weight(change.type)
            if change.weight_now > change.max_weight:

                for order in change.orders.order_by(Order.weight).all()[::-1]:
                    order.courier = None
                    change.weight_now = change.weight_now - order.weight
                    if change.weight_now <= change.max_weight:
                        break

        elif key == 'regions':
            if check_num(False, reg=value):
                abort(400)

            if change.regions == str(value):
                continue
            change.regions = str(value)

            for order in change.orders.all():
                if order.region not in value:
                    order.courier = None
                    change.weight_now = change.weight_now - order.weight

        elif key == 'working_hours':
            if check_str(value):
                abort(400)

            change.working_hours = str(value)
            time = trans_minutes(str(value))
            for order in change.orders.all():
                change.weight_now = change.weight_now - order.weight

                for c_space in time:
                    for o_space in trans_minutes(order.delivery_hours):
                        if c_space[0] <= o_space[0] <= c_space[1] or c_space[0] <= o_space[1] <= c_space[1]:
                            order.courier = change
                            change.weight_now = change.weight_now + order.weight
                            break
                        else:
                            order.courier = None
                    if order.courier is not None:
                        break

        response['courier_type'] = change.type
        response['regions'] = trans_regs(change.regions)
        response['working_hours'] = trans_date(change.working_hours)

    db.session.commit()
    return make_response(response, 200)


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
    not_complete_ord = courier.orders.filter_by(complete=False)
    if not_complete_ord.first() is not None:
        return make_response(jsonify({'orders': [{'id': i.id} for i in not_complete_ord.all()],
                             'assign_time': assign_time[:22] + "Z"}), 200)

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
                        order.courier_type = courier.type
                        courier.weight_now = courier.weight_now + order.weight
                        good_id.append({'id': order.id})
                        break

    db.session.commit()
    if not good_id:
        return make_response(jsonify({'orders': good_id}), 200)
    else:

        return make_response(jsonify({'orders': good_id, 'assign_time': assign_time[:22] + "Z"}), 200)


@app.route('/orders/complete', methods=['POST'])
def complete_order():
    c_id, o_id = request.get_json()['courier_id'], request.get_json()['order_id']
    compl_time = request.get_json()['complete_time']
    global assign_time

    if check_num(True, ident=c_id) or check_num(True, ident=o_id) or \
            Courier.query.get(c_id) is None or Order.query.get(o_id) is None or \
            Order.query.get(o_id).courier is None or check_date(compl_time):
        abort(400)

    courier, order = Courier.query.get(c_id), Order.query.get(o_id)
    compl_time = datetime.fromisoformat(compl_time[:-1]+'0000')
    if order.courier is courier:
        if courier.orders.filter_by(complete=True).first() is None:
            k = compl_time - datetime.fromisoformat(assign_time)
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
    if check_num(True, ident=xid) or Courier.query.get(xid) is None:
        abort(400)

    courier, td, average = Courier.query.get(xid), [], []
    r = {'courier_id': xid,
         'courier_type': courier.type,
         'regions': trans_regs(courier.regions),
         'working_hours': trans_date(courier.working_hours),
         'earnings': 0}

    if courier.orders.filter_by(complete=True).first() is None:
        return make_response(r, 200)

    for order in courier.orders.filter_by(complete=True):
        r['earnings'] += 500 * type_k(order.courier_type)

    for region in trans_regs(courier.regions):
        for order in courier.orders.filter_by(complete=True,  region=region):
            td.append(order.delta_time)
        average.append(sum(td)/len(td))

    r['rating'] = round((60*60 - min(min(average), 60*60))/(60*60) * 5, 2)
    return make_response(r, 200)


if __name__ == '__main__':
    app.run()
