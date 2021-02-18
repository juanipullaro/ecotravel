import os
import secrets
import sqlalchemy
import geocoder
import json
from datetime import datetime
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, jsonify
from ecotravel import app, db, bcrypt
from ecotravel.forms import RegistrationForm, LoginForm, UpdateAccountForm,TravelSearchForm,CreateTravelForm
from ecotravel.models import User,Travel_request, Location, Travel
from flask_login import login_user, current_user, logout_user, login_required

################################### INICIO_PANTALLA PRINCIPAL #####################################
@app.route("/")
@app.route("/home1")
def home():
   travels = Travel.query.all()
   return render_template('home1.html', travels=travels)
################################### PANTALLA DE USUARIO##########################################
@app.route("/profile")
def profile():
    travels = Travel.query.all()
    return render_template('profile.html', travels=travels)
   
@app.route("/generic")
def generic():
    return render_template('generic.html')
################################### REGISTRO #######################################################

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(name=form.name.data, surname=form.surname.data, email=form.email.data,dni=form.dni.data, username=form.username.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        #flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

################################### INICIO SESIÓN #######################################################

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('profile'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('profile'))
        else:
            flash('Contraseña incorrecta.', 'danger')
    return render_template('login.html', title='Login', form=form)


################################### SALIR #######################################################3
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

################################### GUARDAR IMAGEN DE USUARIO #####################################

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

################################### CUENTA DE USUARIO ###############################################

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    posts = Travel_request.query.all()
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)


################################### BUSCAR VIAJE #######################################################

@app.route('/buscar_viajes', methods=['GET', 'POST'])
def search_travels():
    #you can search for travels here
    form = TravelSearchForm()
    if form.validate_on_submit() and request.method == 'POST':
        origin = geocoder.arcgis(form.origin.data + ', argentina')
        dest = geocoder.arcgis(form.destination.data + ', argentina')
        print(origin.address,origin.lat, origin.lng)
        print(dest.address,dest.lat,dest.lng)
        if origin.address == None:
            error = "No se ha encontrado origen"
        else:
            new_origin = Location(location=origin.address,
                                  latitude=origin.lat, longitude=origin.lng)

        if dest.address == None:
            error = "No se ha encontrado destino"
        else:
            new_dest = Location(location=dest.address,
                                latitude=dest.lat, longitude=dest.lng)

        travels = Travel.query.filter_by(
                travel_date=form.travel_date.data, travel_hour=form.travel_time.data)
        travels_matched = []
        
        for travel in travels:
            if (travel.origin.is_in_radius(new_origin, 5000) and travel.dest.is_in_radius(new_dest, 5000)):
                print(travel)
                travels_matched.append(travel.to_json())
        
        if len(travels_matched) ==0:
            error = "No se han encontrado viajes"
        else:
            error = None

        travels_json = json.dumps({'travels': travels_matched})
        print(travels_json)
    
        return render_template('travel_search.html', form=form, error=error, travels=travels_json)
    return render_template('travel_search.html', form=form)

################################### CREAR VIAJE #######################################################

@app.route('/crear_viaje', methods=['GET', 'POST'])
def create_travel():
    error=None
    travels_json = None
    form = CreateTravelForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        origin = geocoder.arcgis(form.origin.data + ', argentina')
        dest = geocoder.arcgis(form.destination.data + ', argentina')
        print(origin.address,origin.lat, origin.lng)
        print(dest.address,dest.lat,dest.lng)
        
        if origin.address == None:
            error = "No se ha encontrado origen"
        else:
            new_origin = Location.get_location(location=origin.address,
                                  latitude=origin.lat, longitude=origin.lng)

        if dest.address == None:
            error = "No se ha encontrado destino"
        else:
            new_dest = Location.get_location(location=dest.address,
                                latitude=dest.lat, longitude=dest.lng)

        driver = User.query.filter_by(username=current_user.username).first()

        try:
            new_travel = Travel(travel_date=form.travel_date.data, travel_hour=form.travel_time.data, driver=driver,
                            origin=new_origin, dest=new_dest, seats=form.seats.data)
        
            print(new_travel)
            db.session.add(new_travel)
            db.session.commit()
            travels = [new_travel.to_json()]
            flash('Se ha registrado un nuevo viaje')
            return redirect(url_for('create_travel'))

        except sqlalchemy.exc.IntegrityError:
            error  = "Ya se tienes un viaje creado para esa fecha y es hora"
            travels = {}
            print(error)
            db.session.rollback()
        except Exception as e:
            error = "Se ha producido un error al agregar viaje" 
            travels = {}
            print(error)
            print(e)
        finally:
            travels_json = {"travels":travels}
    
        
    else:
        print("fail")
    return render_template('create_travel.html', form=form,travels=travels_json,error=error)

################################### UNIRSE AL VIAJE #######################################################

@app.route('/unirme/<id_viaje>',methods=['GET', 'POST'])
def join_travel(id_viaje):
    try:
        travel = Travel.query.filter_by(id=id_viaje).first()
        passanger = User.query.filter_by(username=current_user.username).first()
        travel_request = Travel_request(travel,passanger)
        db.session.add(travel_request)
        db.session.commit()
        print("se ha agregado el viaje")
    except Exception as e:
        print(e)
    return "Viaje {}".format(travel)