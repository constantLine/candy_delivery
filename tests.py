import unittest
from app import app, db
from app.models import Courier, Order, get_weight
from datetime import datetime


class CourierModelCase(unittest.TestCase):
    def setUP(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        db.create_all()

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()

    def test_add_couriers(self):
        c1 = Courier(id=1, type='foot', regions='[1, 2, 3]', working_hours='[08:00-09:00]')
        c2 = Courier(id=2, type='car', regions='[4, 5, 6]', working_hours='[09:00-10:00, 11:00-12:00]')
        c3 = Courier(id=3, type='bike', regions='[7]', working_hours='[09:00-10:00, 11:00-12:00,  13:00-14:00]')
        db.session.add(c1)
        db.session.add(c2)
        db.session.add(c3)
        db.session.commit()

        self.assertEqual(isinstance(c1, Courier), True)
        self.assertEqual(isinstance(c2, Courier), True)
        self.assertEqual(isinstance(c3, Courier), True)

    def test_add_orders(self):
        o1 = Order(id=1, weight=1.7, region=1, delivery_hours='[08:00-09:00]')
        o2 = Order(id=2, weight=2.7, region=4, delivery_hours='[11:00-12:00]')
        o3 = Order(id=3, weight=3.7, region=7, delivery_hours='[13:00-14:00]')

        db.session.add(o1)
        db.session.add(o2)
        db.session.add(o3)
        db.session.commit()

        self.assertEqual(isinstance(o1, Order), True)
        self.assertEqual(isinstance(o2, Order), True)
        self.assertEqual(isinstance(o3, Order), True)

    def test_courier_assign(self):
        c1 = Courier(id=1, type='foot', regions='[1, 2, 3]', working_hours='[08:00-09:00]')
        c2 = Courier(id=2, type='car', regions='[4, 5, 6]', working_hours='[09:00-10:00, 11:00-12:00]')
        c3 = Courier(id=3, type='bike', regions='[7]', working_hours='[09:00-10:00, 11:00-12:00,  13:00-14:00]')
        db.session.add(c1)
        db.session.add(c2)
        db.session.add(c3)
        db.session.commit()

        self.assertEqual(c1.orders.all(), [])
        self.assertEqual(c2.orders.all(), [])
        self.assertEqual(c3.orders.all(), [])

        o1 = Order(id=1, weight=1.7, region=1, delivery_hours='[08:00-09:00]')
        o2 = Order(id=2, weight=2.7, region=4, delivery_hours='[11:00-12:00]')
        o3 = Order(id=3, weight=3.7, region=7, delivery_hours='[13:00-14:00]')

        db.session.add(o1)
        db.session.add(o2)
        db.session.add(o3)
        db.session.commit()

        o1.courier = c1
        o2.courier = c2
        o3.courier = c3

        self.assertEqual(c1.orders.all(), [o1])
        self.assertEqual(c2.orders.all(), [o2])
        self.assertEqual(c3.orders.all(), [o3])
        self.assertEqual(o1.courier, c1)
        self.assertEqual(o2.courier, c2)
        self.assertEqual(o3.courier, c3)

        # check assign time
        o1.assign_time = datetime.now().isoformat()

        self.assertEqual(type(o1.assign_time), str)
        self.assertEqual(isinstance(datetime.fromisoformat(o1.assign_time), datetime), True)

        # check type inherit
        o1.courier_type = c1.type
        c1.type = c2.type

        self.assertEqual(o1.courier_type, 'foot')

        # check weights
        c1.max_weight = get_weight(c1.type)

        self.assertEqual(c1.max_weight, get_weight(c1.type))
        self.assertEqual(type(c1.max_weight), int)

        c1.weight_now = c1.weight_now + 0.3

        self.assertEqual(c1.weight_now, 0.3)
        self.assertEqual(type(c1.weight_now), float)

if __name__ == '__main__':
    unittest.main(verbosity=2)
