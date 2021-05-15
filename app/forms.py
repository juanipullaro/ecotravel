from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, DateField, TextAreaField, TimeField,RadioField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from .models import User 


class RegistrationForm(FlaskForm):
    name = StringField('Nombre',
                       validators=[DataRequired(), Length(min=2, max=20)])
    surname = StringField('Apellido',
                          validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email(message='Email Invalido')])
    dni = IntegerField('DNI', validators=[DataRequired(message='Ingrese solo numeros'), NumberRange(
        min=1000000, max=100000000, message='Ingrese un DNI válido')])

    username = StringField('Usuario',
                           validators=[DataRequired(), Length(min=2, max=20)])

    password = PasswordField('Contraseña', validators=[DataRequired()])
    confirm_password = PasswordField('Confirmar Contraseña',
                                     validators=[DataRequired(), EqualTo('password', message='Las contraseñas no coinciden')])
    submit = SubmitField('Registrarse')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError(
                'El usuario ya existe. Por favor ingrese uno distinto.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError(
                'Este email ya existe. Por favor ingrese uno distinto.')


class LoginForm(FlaskForm):
    username = StringField('Usuario',
                           validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])
    submit = SubmitField('Iniciar Sesión')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user == None:
            raise ValidationError('El usuario no existe.')


class UpdateAccountForm(FlaskForm):
    content = TextAreaField('Contanos sobre vos')
    username = StringField('Usuario',validators=[Length(min=2, max=20)])
    email = StringField('Email', validators=[Email()])
    phone = StringField('Telefono')
    picture = FileField('Cambiar foto de perfil', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Actualizar Perfil')


    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError(
                    'El usuario ya existe. Por favor ingrese uno distinto.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError(
                    'Este email ya existe. Por favor ingrese uno distinto.')


class TravelSearchForm(FlaskForm):
    origin = StringField('Origen', validators=[DataRequired()])
    destination = StringField('Destino', validators=[DataRequired()])
    travel_date = DateField('Fecha', validators=[DataRequired()])
    travel_time = TimeField('Hora', validators=[DataRequired()])
    radius = IntegerField('Ampliar búsquda (Kms)', default=5)
    submit = SubmitField('Buscar')


class CreateTravelForm(FlaskForm):
    origin = StringField('Origen', validators=[DataRequired()])
    destination = StringField('Destino', validators=[DataRequired()])
    travel_date = DateField('Fecha', validators=[DataRequired()])
    travel_time = TimeField('Hora', validators=[DataRequired()])
    seats = IntegerField('Asientos', validators=[DataRequired()])
    submit = SubmitField('Crear Viaje')
    submit1 = SubmitField('Actualizar Viaje')

class ScoreForm(FlaskForm):
    point=RadioField('Calificacion',choices=[(1,'good'),(0,'bad')])
    comment= TextAreaField('Comentario')
    submit2 = SubmitField('Calificar')  
