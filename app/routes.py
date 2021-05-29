import os
import secrets
import sqlalchemy
import geocoder
import json
from datetime import datetime, timedelta
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, jsonify
from . import app, db, bcrypt, socketio, mail
from .forms import RegistrationForm, LoginForm, UpdateAccountForm, TravelSearchForm, CreateTravelForm, ScoreForm, ScoreForm,RequestResetForm,ResetPasswordForm
from .models import User, Travel_request, Location, Travel, Alert, Scores, TravelAlerts, NewTravelNotification
from .data import ALERT_STATUS
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message
import time
from sqlalchemy import desc


@app.before_request
def tasks_travels():
    travels = Travel.query.filter(~Travel.status.in_(["cancelado","finalizado"])).all()
    for travel in travels: 
        if travel.travel_date == datetime.now().date() and travel.travel_hour <= datetime.now().time():
            if travel.status in ["completo", "disponible"]:
                travel.status="en_transito"
                socketio.emit('message', {"id": 2, "mensaje": f"viaje {travel.id} actualizado"}, broadcast=True)
            elif travel.travel_hour_f <= datetime.now().time():
                travel.status="finalizado"
                for request in travel.travel_requests:
                    if request.state=="aceptada":
                        request.state="finalizada"
                        for request_travel in travel.travel_requests:
                            notification = NewTravelNotification(travel=travel,user=request_travel.passenger,type="Finauto")
                            db.session.add(notification)
    db.session.commit()
    



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
    travels = Travel.query.filter(Travel.created_at>=datetime.now()-timedelta(days=7)).order_by(Travel.created_at.desc()).all()
    travels = [
        travel for travel in travels if travel.travel_driver_id != current_user.dni
        and travel.status == 'disponible']
    return render_template('profile.html', travels=travels)


@app.route("/generic")
def generic():
    return render_template('generic.html')

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



@app.route("/usertravelcreate/<dni>/passengerprofile")
@login_required
def passenger_profile(dni):
    user = User.query.get_or_404(dni)
    scores = Scores.query.order_by(Scores.date_posted.desc()).all()
    scores  = [score for score in scores if score.travel_driver_id == user.dni]
    scores1 = [score for score in scores if score.travel_driver_id == user.dni and score.point==1]
    scores2 = [score for score in scores if score.travel_driver_id== user.dni and score.point==0]
    image_file = url_for(
        'static', filename='profile_pics/' + user.image_file)
    return render_template('passengerprofile.html', title='passengerProfile',
                           image_file=image_file,scores=scores,scores1=scores1,user=user,scores2=scores2)


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


# SALIR #######################################################3
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

################################### SESSION VIAJES CREADOS ###############################################

@app.route("/usertravelcreate", methods=['GET', 'POST'])
@login_required
def usertravelcreate():

    scores = Scores.query.all() 
    scores = [score for score in scores if score.passenger_id == current_user.dni]
    form = ScoreForm()
    travels = Travel.query.order_by(Travel.created_at.desc()).all()
    travels = [
        travel for travel in travels if travel.travel_driver_id == current_user.dni]
    travel_reqs = Travel_request.query.order_by(
        Travel_request.date_posted.desc()).all()
    travel_reqs = [
        travel_req for travel_req in travel_reqs if travel_req.dni_user == current_user.dni]
    return render_template('usertravelcreate.html',
                            travels=travels, travel_reqs=travel_reqs,form=form,scores=scores)

@app.route("/usertravelcreate/<int:travel_id>/update", methods=['GET', 'POST'])
def update_travels(travel_id):
    travel = Travel.query.get_or_404(travel_id)
    form = CreateTravelForm()
    if form.validate_on_submit():
        travel.origin.location = form.origin.data
        travel.dest.location = form.destination.data
        travel.travel_date = form.travel_date.data
        travel.travel_hour = form.travel_time.data
        travel.travel_hour_f = form.travel_time_f.data
        travel.seats = form.seats.data
        travel.seatsdec = form.seats.data
        for request_travel in travel.travel_requests:
            if request_travel.state in ("aceptada", "pendiente"):
                notification = NewTravelNotification(travel=travel,user=request_travel.passenger,type="Update")
                db.session.add(notification)
        db.session.commit()
        flash('Se actualizó su viaje!', 'success')
    elif request.method == 'GET':
        form.origin.data = travel.origin.location
        form.destination.data = travel.dest.location
        form.travel_date.data = travel.travel_date
        form.travel_time.data = travel.travel_hour
        form.travel_time_f.data = travel.travel_hour_f
        form.seats.data = travel.seatsdec
    return render_template('formulario.html', title='Update Travel',
                           form=form, legend='Update Travel', travel=travel)



@app.route("/usertravelcreate/<id_viaje>/delete", methods=['GET', 'POST'])
@login_required
def delete_post(id_viaje):
    travel = Travel.query.get_or_404(id_viaje)
    travel.status = "cancelado"
    for request_travel in travel.travel_requests:
            notification = NewTravelNotification(travel=travel,user=request_travel.passenger,type="Delete")
            db.session.add(notification)
    db.session.commit()
    flash('Su viaje se elimino correctamente!', 'success')
    return redirect(url_for('usertravelcreate'))

@app.route("/usertravelcreate/<id_travel>/fin", methods=['GET', 'POST'])
@login_required
def fin_travel(id_travel):
    travel = Travel.query.get_or_404(id_travel)
    travel.status = "finalizado"
    for request_travel in travel.travel_requests:
            if request_travel.state=="aceptada":
                request_travel.state="finalizada"
                notification = NewTravelNotification(travel=travel,user=request_travel.passenger,type="Fin")
                db.session.add(notification)
    db.session.commit()
    return redirect(url_for('usertravelcreate'))


@app.route("/usertravelcreate/<id_passenger>/<id_travel>/add", methods=['GET', 'POST'])
def add_request(id_passenger, id_travel):
    travel = Travel.query.get_or_404(id_travel)
    travel_request = Travel_request.query.filter_by(dni_user=id_passenger, travel_id=id_travel).first()
    notification = NewTravelNotification(travel=travel,user=travel_request.passenger,type="Accept")
    db.session.add(notification)
    travel_request.acept()
    #socketio.emit('message', {"id": 1, "mensaje": "pasajero aceptado"}, broadcast=True)
    return redirect(url_for('usertravelcreate'))


@app.route("/usertravelcreate/<id_passenger>/<id_travel>/reject", methods=['GET', 'POST'])
def reject_request(id_passenger, id_travel):
    travel = Travel.query.get_or_404(id_travel)
    travel_request = Travel_request.query.filter_by(
        dni_user=id_passenger, travel_id=id_travel).first()
    notification = NewTravelNotification(travel=travel,user=travel_request.passenger,type="Reject")
    db.session.add(notification)
    travel_request.reject()
    return redirect(url_for('usertravelcreate'))


@app.route("/usertravelcreate/<id_passenger>/<id_travel>/downpassenger", methods=['GET', 'POST'])
def down_request_driver(id_passenger, id_travel):
    travel = Travel.query.get_or_404(id_travel)
    travel_request = Travel_request.query.filter_by(
        dni_user=id_passenger, travel_id=id_travel).first()
    notification = NewTravelNotification(travel=travel,user=travel_request.passenger,type="Downpassenger")
    db.session.add(notification)
    travel_request.down()
    return redirect(url_for('usertravelcreate'))


@app.route("/usertravelcreate/<id_passenger>/<id_travel>/downme", methods=['GET', 'POST'])
def down_request_passenger(id_passenger, id_travel):
    travel = Travel.query.get_or_404(id_travel)
    travel_request = Travel_request.query.filter_by(
        dni_user=id_passenger, travel_id=id_travel).first()
    notification = NewTravelNotification(travel=travel,user=travel_request.passenger,type="Downme")
    db.session.add(notification)    
    travel_request.down()
    return redirect(url_for('userrequesttravel'))

################################### FIN SESSION VIAJES CREADOS ###############################################


################################### SOLICITUD DE VIAJE #################################################

@app.route("/userrequesttravel", methods=['GET', 'POST'])
@login_required
def userrequesttravel():
    travel_reqs = Travel_request.query.order_by(
        Travel_request.state.asc(), Travel_request.date_posted.desc()).all()
    travel_reqs = [
        travel_req for travel_req in travel_reqs if travel_req.dni_user == current_user.dni and travel_req.state != "finalizada"]
    return render_template('userrequesttravel.html',
                           travel_reqs=travel_reqs)

################################### FIN SOLICITUD DE VIAJE #################################################


################################### SESSION VIAJES FINALIZADOS ###############################################

@app.route("/usertravelfin", methods=['GET', 'POST'])
@login_required
def usertravelfin():
    scores = Scores.query.all()
    scores = [score for score in scores if score.passenger_id == current_user.dni]
    form = ScoreForm()
    travel_reqs = Travel_request.query.order_by(
        Travel_request.date_posted.desc()).all()
    travel_reqs = [travel_req for travel_req in travel_reqs if travel_req.dni_user ==
                   current_user.dni and travel_req.state == 'finalizada']

    return render_template('usertravelfin.html',
                           travel_reqs=travel_reqs, form=form, scores=scores)



@app.route("/usertravelfin/<id_passenger>/<travel_id>", methods=['GET', 'POST'])
def new_post(id_passenger,travel_id):
    form = ScoreForm()
    travel_request = Travel_request.query.filter_by(dni_user=id_passenger, travel_id=travel_id).first()
    travel = Travel.query.get_or_404(travel_id)
    score = Scores(travel_id=travel.id, passenger_id=current_user.dni,
                   travel_driver_id=travel.travel_driver_id, comment=form.comment.data, point=form.point.data)
    db.session.add(score)
    s=Scores.query.filter_by(passenger_id=id_passenger, travel_id=travel_id).first()
    travel_request.score_id=s.id
    notification = NewTravelNotification(travel=travel,user=travel_request.passenger,type="Scoresend")
    db.session.add(notification)
    db.session.add(travel_request)
    db.session.commit()
    flash('Calificacion enviada!', 'success')
    return redirect(url_for('usertravelfin'))

################################### FIN SESSION VIAJES CREADOS ###############################################

################################### BUSCAR VIAJE #######################################################


@app.route('/buscar_viajes', methods=['GET', 'POST'])
@login_required
def search_travels():
    # you can search for travels here
    form = TravelSearchForm()
    last_created_travels = Travel.query.filter(Travel.travel_date>=datetime.now().date(),Travel.status=="disponible")
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
        print("time=",form.travel_time.data, type(form.travel_time.data))
        if form.travel_time.data == "":
            travels = Travel.query.filter_by(
                travel_date=form.travel_date.data,status="disponible")
        else:
            travels = Travel.query.filter_by(
                travel_date=form.travel_date.data,travel_hour=form.travel_time.data,status="disponible")

        travels_matched = []

        for travel in travels:
            if (travel.origin.is_in_radius(new_origin, 5000) and travel.dest.is_in_radius(new_dest, 5000)):
                print(travel)
                travels_matched.append(travel.to_json())

        if len(travels_matched) == 0:
            flash('No se encontraron viajes', 'danger')
            error= 'No se encontraron viajes'
        else:
            error = None

        travels_json = json.dumps({'travels': travels_matched})
        print(travels_json)

        return render_template('travel_search.html', form=form, error=error, travels=travels_json,
                               origin=new_origin, dest=new_dest)
    lastest_travels = json.dumps({'travels': [travel.to_json() for travel in last_created_travels]})
    return render_template('travel_search.html', form=form, travels=lastest_travels)

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
            new_travel = Travel(travel_date=form.travel_date.data, travel_hour=form.travel_time.data,travel_hour_f=form.travel_time_f.data,driver=driver,
                                origin=new_origin, dest=new_dest, seats=form.seats.data, seatsdec=form.seats.data)

            print(new_travel)
            db.session.add(new_travel)
            db.session.commit()
            TravelAlerts.alerts(new_travel)
            travels = [new_travel.to_json()]
            travel_alerts = [
                travel_alert.alert.id for travel_alert in new_travel.travels_alerts]
            flash('Se ha registrado un nuevo viaje', 'success')
            socketio.emit('message', {"id": 1, "mensaje": "Se ha creado un nuevo viaje"}, broadcast=True)
            return redirect(url_for('create_travel'))

        except sqlalchemy.exc.IntegrityError:
            flash("Ya se tienes un viaje creado para esa fecha y esa hora","danger") 
            travels = {}
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


@app.route('/profile/<id_viaje>/unirme', methods=['GET', 'POST'])
@login_required
def join_travel(id_viaje):
    try:
        travel = Travel.query.filter_by(id=id_viaje).first()
        passanger = User.query.filter_by(
            username=current_user.username).first()
        travel_request = Travel_request(travel, passanger)
        notification = NewTravelNotification(travel=travel, user=current_user,type="NewPassengerUp")
        db.session.add(notification)
        db.session.add(travel_request)
        db.session.commit()
        print("se ha agregado el viaje")
        flash("Success",category="success")
    except sqlalchemy.exc.IntegrityError:
        flash("Error",category="danger")
        return redirect(url_for('profile',_anchor="banner1"))
    return redirect(url_for('profile',_anchor="banner1"))



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
    flash("Success",category="success")
    return {"mensaje": "Se ha creado una alerta"}, 200

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


@app.route("/notificaciones", methods=["GET"])
def get_notifications():
    notifications = current_user.get_notifications()
    data = []
    for notification in notifications:
        data.append({"id":notification.id,
        "type": type(notification).__name__,
        "message": notification.message,
        "tipo":notification.type,
        "viewed_at":notification.viewed_at,
        "url":notification.url})
    return {"notificaciones": data}, 200

@app.route("/viewnotificaciones/<id>", methods=["GET","POST"])
def view_notifications(id):
    notification= NewTravelNotification.query.filter_by(id=id).first()
    notification.viewed_at=datetime.now()
    db.session.commit()
    return "", 200

@app.route("/setvisible/<int:val>", methods=["GET","POST"])
def set_visible(val):
    current_user.phone_visible = val
    db.session.commit()
    return "Se ha actulizado la visibilidad del telefono", 200


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Solicitud de cambio de contraseña',
                  sender='info.ecotravel.utn@gmail.com',
                  recipients=[user.email])
    msg.body = f'''Para cambiar su contraseña, por favor visite el siguiente link:
{url_for('reset_token', token=token, _external=True)}

Si no realizó esta solicitud, simplemente ignore este correo electrónico y no se realizarán cambios.
'''
    mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('Se ha enviado un correo electrónico con instrucciones para restablecer su contraseña.', 'info')
    return render_template('reset_request.html', title='Restablecer contraseña', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('Token inválido o caducado', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('¡Tu contraseña ha sido actualizada! Ahora podes iniciar sesión.', 'success')
    return render_template('reset_token.html', title='Restablecer contraseña', form=form)
