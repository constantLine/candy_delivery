from app import db


class Courier(db.Model):
    courier_id = db.Column(db.Integer, primary_key=True)
    courier_type = db.Column(db.Integer)
    regions = db.Column(db.String(255))
    working_hours = db.Column(db.String(128))


class Order(db.Model):
    order_id = db.Column(db.Integer, primary_key=True)
    weight = db.Column(db.Float)
    region = db.Column(db.Integer)
    delivery_hours = db.Column(db.String(128))
