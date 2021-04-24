import os
import secrets
import sqlalchemy
import geocoder
import json
from datetime import datetime
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, jsonify
from . import app, db, bcrypt, socketio
from .forms import RegistrationForm, LoginForm, UpdateAccountForm, TravelSearchForm, CreateTravelForm, ScoreForm
from .models import User, Travel_request, Location, Travel, Alert, Scores
from .data import ALERT_STATUS
from flask_login import login_user, current_user, logout_user, login_required
from selenium import webdriver
import time
from sqlalchemy import desc


################################### INICIO_PANTALLA PRINCIPAL #####################################


@app.route("/")
@app.route("/home")
def home():
    travels = Travel.query.all()
    return render_template('home1.html', travels=travels)


################################### PANTALLA DE USUARIO##########################################
@app.route("/profile")
@login_required
def profile():
    travels = Travel.query.all()
    travels = [
        travel for travel in travels if travel.travel_driver_id != current_user.dni
        and travel.status == 'disponible']
    return render_template('profile.html', travels=travels)


@app.route("/generic")
def generic():
    return render_template('test.html')


<< << << < HEAD
  ################################### GUARDAR IMAGEN DE USUARIO #####################################


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(
        app.root_path, 'static/profile_pics', picture_fn)
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn

 ################################### PERFIL DE USUARIO #####################################


== == == =
>>>>>> > 2f00cac... add alerts


@app.route("/userprofile")
@login_required
def userprofile():
    users = User.query.all()
    scores = Scores.query.order_by(Scores.date_posted.desc()).all()
    scores = [score for score in scores if score.travel_driver_id ==
              current_user.dni]
    scores1 = [score for score in scores if score.travel_driver_id ==
               current_user.dni and score.point == 1]
    scores2 = [score for score in scores if score.travel_driver_id ==
               current_user.dni and score.point == 0]
    image_file = url_for(
        'static', filename='profile_pics/' + current_user.image_file)
    return render_template('userprofile.html', title='UserProfile',
                           image_file=image_file, scores=scores, scores1=scores1, users=users, scores2=scores2)


@app.route("/userprofile/<dni>/updateprofile", methods=['GET', 'POST'])
@login_required
def update_profile(dni):
    user = User.query.get_or_404(dni)
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        user.content = form.content.data
        user.username = form.username.data
        user.email = form.email.data
        user.phone = form.phone.data
        db.session.commit()
        flash('Se actualizo tu cuenta!', 'success')
        return redirect(url_for('userprofile'))
    elif request.method == 'GET':
        form.content.data = user.content
        form.username.data = user.username
        form.email.data = user.email
        form.phone.data = user.phone
    image_file = url_for(
        'static', filename='profile_pics/' + user.image_file)
    return render_template('formulario_profile.html', title='UserProfile',
                           image_file=image_file, form=form, user=user)
################################### REGISTRO #######################################################


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(
            form.password.data).decode('utf-8')
        user = User(name=form.name.data, surname=form.surname.data, email=form.email.data,
                    dni=form.dni.data, username=form.username.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        # flash('Your account has been created! You are now able to log in', 'success')
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


# SALIR #######################################################3
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

################################### SESSION VIAJES CREADOS ###############################################


@app.route("/usertravelcreate", methods=['GET', 'POST'])
@login_required
def usertravelcreate():
    travels = Travel.query.order_by(Travel.created_at.desc()).all()
    travels = [
        travel for travel in travels if travel.travel_driver_id == current_user.dni]
    travel_reqs = Travel_request.query.order_by(
        Travel_request.date_posted.desc()).all()
    travel_reqs = [
        travel_req for travel_req in travel_reqs if travel_req.dni_user == current_user.dni]
    print(travel_reqs)


<< << << < HEAD
== == == =
    alerts = Alert.query.filter(Alert.passenger_id == current_user.dni,
                                Alert.status != ALERT_STATUS[2]).all()
    print(alerts)
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form, travels=travels, travel_reqs=travel_reqs, alerts=alerts)


@app.route("/account/<int:travel_id>")
def travel(travel_id):
    travel = Travel.query.get_or_404(travel_id)
    return render_template('account.html', id=travel.id, travel=travel)


@app.route("/usertravelcreate", methods=['GET', 'POST'])
@login_required
def usertravelcreate():

    travels = Travel.query.order_by(Travel.created_at.desc()).all()
    travels = [
        travel for travel in travels if travel.travel_driver_id == current_user.dni]
    travel_reqs = Travel_request.query.order_by(
        Travel_request.date_posted.desc()).all()
    travel_reqs = [
        travel_req for travel_req in travel_reqs if travel_req.dni_user == current_user.dni]
    print(travel_reqs)


>>>>>> > 2f00cac... add alerts
    return render_template('usertravelcreate.html',
                           travels=travels, travel_reqs=travel_reqs)


@app.route("/usertravelcreate/<int:travel_id>/update", methods=['GET', 'POST'])
def update_travels(travel_id):
    travel = Travel.query.get_or_404(travel_id)
    form = CreateTravelForm()
    if form.validate_on_submit():
        travel.origin.location = form.origin.data
        travel.dest.location = form.destination.data
        travel.travel_date = form.travel_date.data
        travel.travel_hour = form.travel_time.data
        travel.seats = form.seats.data
        travel.seatsdec = form.seats.data
        db.session.commit()
        flash('Se actualizó su viaje!', 'success')
        return redirect(url_for('usertravelcreate', travel_id=travel_id))
    elif request.method == 'GET':
        form.origin.data = travel.origin.location
        form.destination.data = travel.dest.location
        form.travel_date.data = travel.travel_date
        form.travel_time.data = travel.travel_hour
        form.seats.data = travel.seatsdec
    return render_template('formulario.html', title='Update Travel',
                           form=form, legend='Update Travel', travel=travel)


@app.route("/usertravelcreate/<id_viaje>/delete", methods=['GET', 'POST'])
@login_required
def delete_post(id_viaje):
    travel = Travel.query.get_or_404(id_viaje)
    travel.status = "cancelado"
    db.session.commit()
    flash('Su viaje se elimino correctamente!', 'success')
    return redirect(url_for('profile'))


<< << << < HEAD


@app.route("/usertravelcreate/<id_passenger>/<id_travel>/add", methods=['GET', 'POST'])
def add_request(id_passenger, id_travel):
    travel_request = Travel_request.query.filter_by(
        dni_user=id_passenger, travel_id=id_travel).first()
    travel_request.acept()
    return redirect(url_for('usertravelcreate'))


@app.route("/usertravelcreate/<id_passenger>/<id_travel>/reject", methods=['GET', 'POST'])
def reject_request(id_passenger, id_travel):
    travel_request = Travel_request.query.filter_by(
        dni_user=id_passenger, travel_id=id_travel).first()
    travel_request.reject()
    return redirect(url_for('usertravelcreate'))


@app.route("/usertravelcreate/<id_passenger>/<id_travel>/downpassenger", methods=['GET', 'POST'])
def down_request_driver(id_passenger, id_travel):
    travel_request = Travel_request.query.filter_by(
        dni_user=id_passenger, travel_id=id_travel).first()
    travel_request.down()
    return redirect(url_for('usertravelcreate'))


@app.route("/usertravelcreate/<id_passenger>/<id_travel>/downme", methods=['GET', 'POST'])
def down_request_passenger(id_passenger, id_travel):
    travel_request = Travel_request.query.filter_by(
        dni_user=id_passenger, travel_id=id_travel).first()
    travel_request.down()
    return redirect(url_for('userrequesttravel'))

################################### FIN SESSION VIAJES CREADOS ###############################################


################################### SOLICITUD DE VIAJE #################################################

== == == =
>>>>>> > 2f00cac... add alerts


@app.route("/userrequesttravel", methods=['GET', 'POST'])
@login_required
def userrequesttravel():
    travel_reqs = Travel_request.query.order_by(
<< << << < HEAD
        Travel_request.state.asc(), Travel_request.date_posted.desc()).all()


== == == =
        Travel_request.date_posted.desc()).all()
>> >>>> > 2f00cac... add alerts
    travel_reqs=[
        travel_req for travel_req in travel_reqs if travel_req.dni_user == current_user.dni]
    return render_template('userrequesttravel.html',
                           travel_reqs = travel_reqs)

<< << << < HEAD
################################### FIN SOLICITUD DE VIAJE #################################################


################################### SESSION VIAJES FINALIZADOS ###############################################
== == ===
>>>>>> > 2f00cac... add alerts

@ app.route("/usertravelfin", methods = ['GET', 'POST'])
@ login_required
def usertravelfin():
    scores=Scores.query.all()
    scores=[score for score in scores if score.passenger_id == current_user.dni]
    form=ScoreForm()
    travel_reqs=Travel_request.query.order_by(
        Travel_request.date_posted.desc()).all()
<< << << < HEAD
    travel_reqs=[travel_req for travel_req in travel_reqs if travel_req.dni_user ==
                   current_user.dni and travel_req.state == 'finalizada']
== == ===
    travel_reqs = [
        travel_req for travel_req in travel_reqs if travel_req.dni_user == current_user.dni]
>> >>>> > 2f00cac... add alerts

    return render_template('usertravelfin.html',
                           travel_reqs = travel_reqs, form = form, scores = scores)


@ app.route("/usertravelfin/<int:travel_id>", methods = ['GET', 'POST'])
def new_post(travel_id):
    form=ScoreForm()
    travel=Travel.query.get_or_404(travel_id)
    score=Scores(travel_id = travel.id, passenger_id = current_user.dni,
                   travel_driver_id=travel.travel_driver_id, comment=form.comment.data, point=form.point.data)
    db.session.add(score)
    db.session.commit()
    flash('Your post has been created!', 'success')
    return redirect(url_for('userprofile'))

################################### FIN SESSION VIAJES CREADOS ###############################################

################################### BUSCAR VIAJE #######################################################


@app.route('/buscar_viajes', methods=['GET', 'POST'])
@login_required
def search_travels():
    # you can search for travels here
    form = TravelSearchForm()
    if form.validate_on_submit() and request.method == 'POST':
        origin = geocoder.arcgis(form.origin.data + ', argentina')
        dest = geocoder.arcgis(form.destination.data + ', argentina')
        radius = form.radius.data * 1000
        print(origin.address, origin.lat, origin.lng)
        print(dest.address, dest.lat, dest.lng, radius)
        if origin.address == None:
            error = "No se ha encontrado origen"
        else:
            new_origin = Location.get_location(origin.address,
                                               origin.lat, origin.lng)
            form.origin.data = new_origin.location
        if dest.address == None:
            error = "No se ha encontrado destino"
        else:
            new_dest = Location.get_location(location=dest.address,
                                             latitude=dest.lat, longitude=dest.lng)
            form.destination.data = new_dest.location
        travels = Travel.query.filter_by(
            travel_date=form.travel_date.data)
        travels_matched = []

        for travel in travels:
            if (travel.origin.is_in_radius(new_origin, 5000) and travel.dest.is_in_radius(new_dest, 5000)):
                print(travel)
                travels_matched.append(travel.to_json())

        if len(travels_matched) == 0:
            error = "No se han encontrado viajes"
        else:
            error = None

        travels_json = json.dumps({'travels': travels_matched})
        print(travels_json)

        return render_template('travel_search.html', form=form, error=error, travels=travels_json,
                               origin=new_origin, dest=new_dest)
    return render_template('travel_search.html', form=form)

################################### CREAR VIAJE #######################################################


@app.route('/crear_viaje', methods=['GET', 'POST'])
@login_required
def create_travel():
    error = None
    travels_json = None
    form = CreateTravelForm()

    if request.method == 'POST' and form.validate_on_submit():
        origin = geocoder.arcgis(form.origin.data + ', argentina')
        dest = geocoder.arcgis(form.destination.data + ', argentina')
        print(origin.address, origin.lat, origin.lng)
        print(dest.address, dest.lat, dest.lng)

        if origin.address == None:
            error = "No se ha encontrado origen"
        else:
            new_origin = Location.get_location(origin.address,
                                               origin.lat, origin.lng)

        if dest.address == None:
            error = "No se ha encontrado destino"
        else:
            new_dest = Location.get_location(dest.address,
                                             dest.lat, dest.lng)

        driver = User.query.filter_by(username=current_user.username).first()

        try:
            new_travel = Travel(travel_date=form.travel_date.data, travel_hour=form.travel_time.data, driver=driver,
                                origin=new_origin, dest=new_dest, seats=form.seats.data, seatsdec=form.seats.data)

            print(new_travel)
            db.session.add(new_travel)
            db.session.commit()
            TravelAlerts.alerts(new_travel)
            travels = [new_travel.to_json()]
            travel_alerts = [
                travel_alert.alert.id for travel_alert in new_travel.travels_alerts]
            flash('Se ha registrado un nuevo viaje')
            print(travel_alerts)
            socketio.emit(
                'message', {"id": 1, "mensaje": "Se ha creado un nuevo viaje"}, broadcast=True)
            return redirect(url_for('create_travel'))

        except sqlalchemy.exc.IntegrityError:
            error = "Ya se tienes un viaje creado para esa fecha y es hora"
            travels = {}
            print(error)
            db.session.rollback()
        except Exception as e:
            error = "Se ha producido un error al agregar viaje"
            travels = {}
            print(error)
            print(e)
        finally:
            travels_json = {"travels": travels}

    return render_template('create_travel.html', form=form, travels=travels_json, error=error)

################################### UNIRSE AL VIAJE #######################################################


@app.route('/unirme/<id_viaje>', methods=['GET', 'POST'])
@login_required
def join_travel(id_viaje):
    try:
        travel = Travel.query.filter_by(id=id_viaje).first()
        passanger = User.query.filter_by(
            username=current_user.username).first()
        travel_request = Travel_request(travel, passanger)
        db.session.add(travel_request)
        db.session.commit()
        print("se ha agregado el viaje")
    except Exception as e:
        print(e)
    return "Viaje {}".format(travel)


@app.route('/account/alert/create', methods=['GET', 'POST'])
@login_required
def create_alert():
    data = json.loads(request.get_data())
    origin = Location.get_location_by_name(data['origin'])
    dest = Location.get_location_by_name(data['dest'])
    travel_date = data["travel_date"]
    travel_time = data["travel_time"]
    alert = Alert(origin, dest, travel_date, travel_time, current_user)
    alert.save()
    # return {"error savig": str(e)}, 500
    return "Se ha generado una nueva alerta", 200


@app.route('/account/alert/<int:id>/update', methods=['GET', 'POST'])
@login_required
def update_alert(id):
    status = int(request.args.get("status"))
    alert = Alert.query.filter_by(id=id).first()
    alert.status = ALERT_STATUS[status]
    print(alert.status)
    db.session.commit()
    return f"Alerta {alert.id} updated", 200


@app.route('/account/alert/travels', methods=['GET', 'POST'])
@login_required
def get_travel_alerts():
    alerts = Alert.query.filter_by(passenger_id=current_user.dni)
    travel_alerts = []
    for alert in alerts:
        if alert.travels_alerts is not None:
            print(alert.travels_alerts)
            travel_alerts.append(alert)
    return travel_alerts
