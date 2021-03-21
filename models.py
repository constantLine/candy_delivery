from app import db


class Courier(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    type = db.Column('type', db.Integer)
    regions = db.Column('regions', db.String(255))
    working_hours = db.Column('working_hours', db.String(128))
    orders = db.relationship('Order', backref='courier', lazy='dynamic')

    def __repr__(self):
        return f'Number - {self.id}'


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    weight = db.Column(db.Float)
    region = db.Column(db.Integer)
    delivery_hours = db.Column(db.String(128))
    courier_id = db.Column(db.Integer, db.ForeignKey('courier.id'))
