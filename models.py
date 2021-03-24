from datetime import datetime
from ecotravel import db, login_manager
from sqlalchemy import Column, BigInteger, Text, Sequence, Boolean, String, Date, Integer, ForeignKey
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

@login_manager.user_loader
def load_user(dni):
    return User.query.get(int(dni))

################################### USUARIO #######################################################

class User(db.Model, UserMixin):
    __tablename__="users"
    __table_args__ = {'extend_existing':True}
    dni= db.Column(db.BigInteger,  unique=True, primary_key =True, nullable=False)
    name= db.Column(db.String(20),  nullable=False)
    surname= db.Column(db.String(20),nullable=False)
    email = db.Column(db.String(120),  nullable=False)
    username = db.Column(db.String(20),unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    travel_requests = db.relationship('Travel_request', backref='passenger')
    travels = db.relationship('Travel',backref='driver')
    rating = db.Column(db.Integer)
  
   

    def __init__(self, name,surname,email,dni,username,password ):
        self.name=name
        self.surname=surname
        self.email=email
        self.dni=dni
        self.username=username
        self.password=password
        

    def __repr__(self):
        return f"User('{self.name}', '{self.surname}', '{self.email}', '{self.dni}','{self.username}', '{self.password}', '{self.image_file}')"

    def get_id(self):
           return (self.dni)


################################### USUARIO #######################################################

class Travel_request(db.Model):
    __tablename__="travel_request"
    __table_args__ = {'extend_existing':True}
    dni_user = db.Column(db.Integer, db.ForeignKey('users.dni'), primary_key=True)
    travel_id = db.Column(db.Integer,db.ForeignKey('travels.id'),primary_key=True)
    state = db.Column(db.String(60),default="Pendiente")
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,primary_key=True)
    travel = db.relationship("Travel", foreign_keys=[travel_id],backref='travel_requests')
   


    def __init__(self,travel,passenger):
        self.dni_user = passenger.dni
        self.travel_id = travel.id
    
    

    def __repr__(self):
      return f"Travel_request('{self.dni_user}', '{self.travel_id}')"


################################### VIAJE #######################################################

class Travel(db.Model):
    __tablename__= "travels"
    __table_args__ = {'extend_existing':True}
    __table_args__ = (db.UniqueConstraint('travel_date', 'travel_hour','travel_driver_id', name='travelS'), )
    id =db.Column(db.Integer,primary_key=True)
    travel_date = db.Column(db.Date)
    travel_hour = db.Column(db.Time)
    travel_driver_id = db.Column(db.Integer,db.ForeignKey('users.dni'))
    origin_id = db.Column(db.Integer,db.ForeignKey('locations.id'))
    dest_id = db.Column(db.Integer,db.ForeignKey('locations.id'))
    origin = db.relationship("Location",backref = "travel_origins",foreign_keys=[origin_id])
    dest = db.relationship("Location",backref="travel_destinations",foreign_keys=[dest_id])
    #driver = db.relationship("TravelDriver",backref="travels",foreign_keys=[travel_driver_id])
    seats = db.Column(db.Integer)
    created_at = db.Column(db.DateTime,default = datetime.now())
    #pasajeros

    def to_json(self):
        travel = {"id":self.id,
                    
                    "origen": {"nombre": self.origin.location, "lat": self.origin.latitude, "lon": self.origin.longitude},
                    "destino": {"nombre": self.dest.location, "lat": self.dest.latitude, "lon": self.dest.longitude},
                    "fecha": str(self.travel_date),
                    "hora": str(self.travel_hour),
                    "conductor": self.driver.name+' '+self.driver.surname,
                    "foto_conductor":'/static/profile_pics/'+self.driver.image_file,
                    "rating": self.driver.rating,
                    "asientos_disp": self.seats}
        return travel


################################### LOCALIZACION #######################################################

class Location(db.Model):
    __tablename__ = "locations"
    __table_args__ = (db.UniqueConstraint('latitude', 'longitude', name='lat_long'), )
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    location = db.Column(db.String(200))
    geo =  db.Column(Geometry(geometry_type='POINT', srid=4326))

    def __init__(self,location,latitude,longitude):
        self.location = location
        self.longitude = longitude
        self.latitude = latitude
        self.geo = 'SRID=4326; POINT({} {})'.format(longitude, latitude)
        
    
    def is_in_radius(self,loc,radius):
        """Return true if the distance between two points is less than the radius"""
        print(self.location,loc.location)
        print(self.latitude,self.longitude)
        print(loc.latitude,loc.longitude)
        distance = db.session.scalar(db.func.ST_Distance(self.geo,loc.geo,True))
        print(distance)
        if distance<radius:
            return True
        else:
            return False
    
    def get_location(location,latitude,longitude):
        """retun the location if not exists it save add to database"""
        loc = Location.query.filter_by(latitude=latitude,longitude=longitude).first()
        if loc == None:
            loc = Location.add_location(location,latitude,longitude)
        return loc



    @classmethod
    def add_location(self,location, latitude, longitude):
        """Put a new city in the database."""

        #geo = 'SRID=4326; POINT({} {})'.format(longitude, latitude)
        loc = Location( longitude=longitude,
                        latitude=latitude,
                        location=location)

        db.session.add(loc)
        db.session.commit()
        return loc



