from geoalchemy2 import Geometry
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from datetime import datetime
from . import db, login_manager
from sqlalchemy import Column, BigInteger, Text, Sequence, Boolean, Float
from sqlalchemy import String, Date, Integer, ForeignKey, DateTime, Time, UniqueConstraint


@login_manager.user_loader
def load_user(dni):
    return User.query.get(int(dni))

################################### USUARIO #######################################################


class User(db.Model, UserMixin):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
    dni = Column(BigInteger,  unique=True,
                 primary_key=True, nullable=False)
    name = Column(String(20),  nullable=False)
    surname = Column(String(20), nullable=False)
    email = Column(String(120),  nullable=False)
    username = Column(String(20), unique=True, nullable=False)
    password = Column(String(60), nullable=False)
    image_file = Column(String(20), nullable=False,
                        default='default.jpg')
    travel_requests = relationship('Travel_request', backref='passenger')
    travelsuser = relationship('Travel', backref='driver')
    rating = Column(Integer)
    content = db.Column(db.String(200))
    phone = db.Column(db.BigInteger)

    def __init__(self, name, surname, email, dni, username, password):
        self.name = name
        self.surname = surname
        self.email = email
        self.dni = dni
        self.username = username
        self.password = password

    def __repr__(self):
        return f"User('{self.name}', '{self.surname}', '{self.email}', '{self.dni}','{self.username}', '{self.password}', '{self.image_file}')"

    def get_id(self):
        return (self.dni)

    def get_alerts(self):
        try:
            active_alerts = [alert for alert in self.alerts if alert.status!="ELIMINADA"]
            return active_alerts
        except Exception as e:
            return []

################################### USUARIO #######################################################

class Travel_request(db.Model):
    __tablename__ = "travel_request"
    __table_args__ = {'extend_existing': True}
    dni_user = Column(Integer, ForeignKey(
        'users.dni'), primary_key=True)
    travel_id = Column(Integer, ForeignKey(
        'travels.id'), primary_key=True)
    state = db.Column(db.String(60), default="activa")
    date_posted = Column(DateTime, nullable=False,
                         default=datetime.utcnow)
    travel = relationship("Travel", foreign_keys=[
        travel_id], backref='travel_requests')

    def __init__(self, travel, passenger):
        self.dni_user = passenger.dni
        self.travel_id = travel.id

    def __repr__(self):
        return f"Travel_request('{self.dni_user}', '{self.travel_id}')"

    def acept(self):
        if self.travel.status == 'disponible':
            self.state = 'aceptada'
            self.travel.addpassenger()
            db.session.commit()

    def reject(self):
        if self.travel.status != 'finalizado':
            self.state = 'rechazada'
            db.session.commit()

    def down(self):
        if self.travel.status != 'finalizado':
            if self.state == 'activa':
                self.state = 'cancelada'
                db.session.commit()
            elif self.state == 'aceptada':
                self.travel.downpassenger()
                self.state = 'cancelada'
                db.session.commit()

    def changestatus(self):
        if self.travel.status == 'finalizado':
            self.state = 'finalizada'
            db.session.commit()


################################### VIAJE #######################################################

class Travel(db.Model):
    __tablename__ = "travels"
    __table_args__ = {'extend_existing': True}
    __table_args__ = (UniqueConstraint(
        'travel_date', 'travel_hour', 'travel_driver_id', name='travels'), )
    id = Column(Integer, primary_key=True)
    travel_date = Column(Date)
    travel_hour = Column(Time)
    travel_driver_id = Column(Integer, ForeignKey('users.dni'))
    origin_id = Column(Integer, ForeignKey('locations.id'))
    dest_id = Column(Integer, ForeignKey('locations.id'))
    origin = relationship(
        "Location", backref="travel_origins", foreign_keys=[origin_id])
    dest = relationship(
        "Location", backref="travel_destinations", foreign_keys=[dest_id])
    # driver = relationship("TravelDriver",backref="travels",foreign_keys=[travel_driver_id])
    seats = Column(Integer)
    created_at = db.Column(db.DateTime, nullable=False,
                           default=datetime.utcnow)
    status = db.Column(db.String(60), default="disponible")
    seatsdec = Column(Integer)
    # pasajeros

    def to_json(self):
        travel = {"id": self.id,

                  "origen": {"nombre": self.origin.location, "lat": self.origin.latitude, "lon": self.origin.longitude},
                  "destino": {"nombre": self.dest.location, "lat": self.dest.latitude, "lon": self.dest.longitude},
                  "fecha": str(self.travel_date),
                  "hora": str(self.travel_hour),
                  "conductor": self.driver.name+' '+self.driver.surname,
                  "foto_conductor": '/static/profile_pics/'+self.driver.image_file,
                  "score_bueno": 0,
                  "score_malo": 0,
                  "asientos_disp": self.seats}
        return travel

    def addpassenger(self):
        self.seats -= 1
        if self.seats == 0:
            self.status = 'completo'

    def downpassenger(self):
        self.seats += 1
        if self.seats != 0:
            self.status = 'disponible'

    def getpending_request(self):
        return[request for request in self.travel_requests if request.state == "activa"]

    def getaccept_request(self):
        return[request for request in self.travel_requests if request.state == "aceptada"]

    def are_near(self, new_origin, new_dest):
        return self.origin.is_in_radius(new_origin, 5000) and self.dest.is_in_radius(new_dest, 5000)

    def match_alert(self, alert):
        if self.travel_hour != alert.travel_time:
            return False
        if self.travel_date != alert.travel_date:
            return False
        if not self.are_near(alert.origin, alert.dest):
            return False
        return True

    def get_destino(self):
        return self.dest.location.split(",")[0]


################################### LOCALIZACION #######################################################

class Location(db.Model):
    __tablename__ = "locations"
    __table_args__ = (UniqueConstraint(
        'latitude', 'longitude', name='lat_long'), )
    id = Column(Integer, primary_key=True, autoincrement=True)
    latitude = Column(Float)
    longitude = Column(Float)
    location = Column(String(200))
    geo = Column(Geometry(geometry_type='POINT', srid=4326))

    def __init__(self, location, latitude, longitude):
        self.location = location
        self.longitude = longitude
        self.latitude = latitude
        self.geo = 'SRID=4326; POINT({} {})'.format(longitude, latitude)

    def is_in_radius(self, loc, radius):
        """Return true if the distance between two points is less than the radius"""
        print(self.location, loc.location)
        print(self.latitude, self.longitude)
        print(loc.latitude, loc.longitude)
        distance = db.session.scalar(
            db.func.ST_Distance(self.geo, loc.geo, True))
        print(distance)
        if distance < radius:
            return True
        else:
            return False

    @classmethod
    def get_location(cls, location, latitude, longitude):
        """retun the location if not exists it save add to database"""
        loc = Location.query.filter_by(
            latitude=latitude, longitude=longitude).first()
        if loc == None:
            loc = Location.add_location(location, latitude, longitude)
        return loc

    @classmethod
    def get_location_by_name(cls, name):
        location = Location.query.filter_by(location=name).first()
        return location

    @classmethod
    def add_location(self, location, latitude, longitude):
        """Put a new city in the database."""

        #geo = 'SRID=4326; POINT({} {})'.format(longitude, latitude)
        loc = Location(longitude=longitude,
                       latitude=latitude,
                       location=location)

        db.session.add(loc)
        db.session.commit()
        return loc

    def save(self):
        db.session.add(self)
        db.session.commit()


class TravelAlerts(db.Model):
    __tablename__ = "travel_alerts"
    id_travel = Column(Integer,  db.ForeignKey('travels.id'), primary_key=True)
    id_alert = Column(Integer, db.ForeignKey('alerts.id'), primary_key=True)
    alert = relationship("Alert", foreign_keys=[
        id_alert], backref='travels_alerts')
    travel = relationship("Travel", foreign_keys=[
        id_travel], backref='travels_alerts')

    def __init__(self, travel, alert):
        print(travel)
        self.id_travel = travel.id
        self.id_alert = alert.id

    @classmethod
    def alerts(cls, travel):
        print(travel)
        alerts = Alert.query.all()
        for alert in alerts:
            if travel.match_alert(alert):
                travel_alert = TravelAlerts(travel, alert)
                user = alert.passenger
                notification = NewTravelNotification(travel, user)
                print(notification)
                db.session.add(travel_alert)
                db.session.add(notification)
        try:
            db.session.commit()
        except Exception as e:
            print(e)
            

class Alert(db.Model):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    travel_origin_id = Column(Integer, ForeignKey('locations.id'))
    travel_dest_id = Column(Integer, ForeignKey('locations.id'))
    travel_date = Column(Date)
    travel_time = Column(Time)
    passenger_id = Column(Integer, ForeignKey('users.dni'))
    passenger = relationship(
        "User", backref="alerts", foreign_keys=[passenger_id])
    status = Column(String(60), default="ACTIVA")
    created_at = Column(
        DateTime, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    last_modified = Column(
        DateTime, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    origin = relationship(
        "Location", backref="alert_origins", foreign_keys=[travel_origin_id])
    dest = relationship(
        "Location", backref="alert_destinations", foreign_keys=[travel_dest_id])

    def __init__(self, origin, dest, travel_date, travel_time, user):
        self.travel_origin_id = origin.id
        self.travel_dest_id = dest.id
        self.travel_date = travel_date
        self.travel_time = datetime.strptime(travel_time, "%H:%M").time()
        self.passenger_id = user.dni

    def save(self):
        db.session.add(self)
        db.session.commit()
################################### CALIFICACIONES #######################################################


class Scores(db.Model):
    __tablename__ = "scores"
    travel_id = Column(Integer, ForeignKey('travels.id'), primary_key=True)
    passenger_id = Column(Integer, ForeignKey('users.dni'), primary_key=True)
    travel_driver_id = Column(Integer, ForeignKey('users.dni'))
    date_posted = db.Column(db.DateTime, nullable=False,
                            default=datetime.utcnow)
    comment = Column(Text())
    point = Column(Integer)

    def __repr__(self):
        return f"Scores('{self.comment}', '{self.date_posted}')"


class NewTravelNotification(db.Model):
    __tablename__ = "travel_notifications"
    id = Column(Integer, autoincrement=True, primary_key=True)
    message = Column(String(120),  nullable=False)
    passenger_id = Column(Integer, ForeignKey('users.dni'))
    passenger = relationship(
        "User", backref="notifications", foreign_keys=[passenger_id])
    created_at = Column(
        DateTime, default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    viewed_at = Column(DateTime)
    deleted_at = Column(DateTime)
    travel_id = Column(Integer, ForeignKey(
        'travels.id'), primary_key=True)
    travel = relationship("Travel", foreign_keys=[
        travel_id])

    def __init__(self, travel, user):
        self.message = f"Nuevo viaje creado con destino a {travel.get_destino()}"
        self.passenger_id = user.dni
        self.travel_id = travel.id
