from app import db


class Courier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(5), nullable=False)
    regions = db.Column(db.String(255), nullable=False)
    working_hours = db.Column(db.String(128), unique=True, nullable=False)
    max_weight = db.Column(db.Integer)
    weight_now = db.Column(db.Float, default=0.0)
    orders = db.relationship('Order', backref='courier', lazy='dynamic')

    def __repr__(self):
        return f'Number - {self.id}'


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    weight = db.Column(db.Float)
    region = db.Column(db.Integer)
    delivery_hours = db.Column(db.String(128))
    assign_time = db.Column(db.String(128))
    delta_time = db.Column(db.Float, default=0.0)
    complete = db.Column(db.Boolean, default=False)
    courier_type = db.Column(db.String(5))
    courier_id = db.Column(db.Integer, db.ForeignKey('courier.id'))

    def __repr__(self):
        return f'Number - {self.id}'
