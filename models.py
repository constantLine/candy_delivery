from app import db


class Courier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Integer)
    regions = db.Column(db.String(255))
    working_hours = db.Column(db.String(128))
    orders = db.relationship('Order', backref='courier', lazy='dynamic')


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    weight = db.Column(db.Float)
    region = db.Column(db.Integer)
    delivery_hours = db.Column(db.String(128))
    courier_id = db.Column(db.Integer, db.ForeignKey('courier.id'))
