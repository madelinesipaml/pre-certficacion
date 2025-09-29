from flask import Flask, render_template, redirect, url_for, request, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')
# Prefer MySQL (pymysql) when DB_* env vars are provided; otherwise fallback to SQLite for local dev
DB_HOST = os.environ.get('DB_HOST')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_NAME = os.environ.get('DB_NAME')
if DB_HOST and DB_USER and DB_PASSWORD and DB_NAME:
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# association table matching your MySQL schema name 'usuarios_viajes'
usuarios_viajes = db.Table('usuarios_viajes',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuarios.id')),
    db.Column('viaje_id', db.Integer, db.ForeignKey('viajes.id'))
)


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    apellido = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # hashed
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    viajes_creados = db.relationship('Viaje', backref='creador', lazy=True)

    def set_password(self, password_plain):
        self.password = generate_password_hash(password_plain)

    def check_password(self, password_plain):
        return check_password_hash(self.password, password_plain)


class Viaje(db.Model):
    __tablename__ = 'viajes'
    id = db.Column(db.Integer, primary_key=True)
    destino = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    creador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)

    participants = db.relationship('Usuario', secondary=usuarios_viajes, backref=db.backref('viajes_unidos', lazy='dynamic'))


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


def init_db():
    db.create_all()


@app.route('/')
def index():
    if current_user.is_authenticated:
        # viajes creados por el usuario y viajes unidos
        my_created = Viaje.query.filter_by(creador_id=current_user.id).all()
        my_joined = current_user.viajes_unidos.all()
        # planes de otros usuarios (no creados por el usuario)
        others = Viaje.query.filter(Viaje.creador_id != current_user.id).all()
        return render_template('index.html', my_created=my_created, my_joined=my_joined, others=others)
    else:
        trips = Viaje.query.order_by(Viaje.fecha_inicio.asc()).all()
        return render_template('index_public.html', trips=trips)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        apellido = request.form.get('apellido', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        errors = []
        if not nombre or not apellido:
            errors.append('Nombre y apellido son requeridos.')
        if not email:
            errors.append('El email es requerido.')
        confirm = request.form.get('confirm', '')
        if not password or len(password) < 8:
            errors.append('La contraseña debe tener al menos 8 caracteres.')
        if password != confirm:
            errors.append('Las contraseñas no coinciden.')
        if Usuario.query.filter_by(email=email).first():
            errors.append('El correo ya está registrado.')
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('register.html')
        user = Usuario(nombre=nombre, apellido=apellido, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Registro exitoso', 'success')
        return redirect(url_for('index'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = Usuario.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash('Credenciales inválidas', 'danger')
            return render_template('login.html')
        login_user(user)
        flash('Inicio de sesión exitoso', 'success')
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada', 'info')
    return redirect(url_for('index'))


@app.route('/trips/new', methods=['GET', 'POST'])
@login_required
def new_trip():
    if request.method == 'POST':
        destino = request.form.get('destino', '').strip()
        descripcion = request.form.get('descripcion', '').strip()
        fecha_inicio_str = request.form.get('fecha_inicio', '').strip()
        fecha_fin_str = request.form.get('fecha_fin', '').strip()
        errors = []
        if not destino:
            errors.append('El destino es requerido.')
        if not fecha_inicio_str or not fecha_fin_str:
            errors.append('Fechas de inicio y fin son requeridas.')
        try:
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
            if fecha_fin < fecha_inicio:
                errors.append('La fecha de fin debe ser posterior o igual a la fecha de inicio.')
        except Exception:
            errors.append('Formato de fecha inválido. Use YYYY-MM-DD.')
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('new_trip.html')
        trip = Viaje(destino=destino, descripcion=descripcion, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, creador_id=current_user.id)
        db.session.add(trip)
        db.session.commit()
        flash('Viaje creado', 'success')
        # redirect to index and include new_id so the frontend can animate the new row
        return redirect(url_for('index', new_id=trip.id))
    return render_template('new_trip.html')


@app.route('/trips/<int:trip_id>')
def trip_detail(trip_id):
    trip = Viaje.query.get_or_404(trip_id)
    joined_users = [u for u in trip.participants if u.id != trip.creador_id]
    return render_template('trip_detail.html', trip=trip, joined_users=joined_users)


@app.route('/trips/<int:trip_id>/join')
@login_required
def join_trip(trip_id):
    trip = Viaje.query.get_or_404(trip_id)
    if current_user in trip.participants:
        flash('Ya estás en este viaje', 'info')
    else:
        trip.participants.append(current_user)
        db.session.commit()
        flash('Te has unido al viaje', 'success')
    return redirect(url_for('index'))


@app.route('/trips/<int:trip_id>/cancel')
@login_required
def cancel_trip(trip_id):
    trip = Viaje.query.get_or_404(trip_id)
    if current_user in trip.participants:
        trip.participants.remove(current_user)
        db.session.commit()
        flash('Has cancelado tu participación', 'info')
    else:
        flash('No estabas unido a este viaje', 'warning')
    return redirect(url_for('index'))


@app.route('/trips/<int:trip_id>/delete', methods=['POST'])
@login_required
def delete_trip(trip_id):
    trip = Viaje.query.get_or_404(trip_id)
    if trip.creador_id != current_user.id:
        abort(403)
    db.session.delete(trip)
    db.session.commit()
    flash('Viaje eliminado', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    # Ensure we create tables inside the application context
    with app.app_context():
        init_db()

    app.run(host='0.0.0.0', port=5000, debug=True)
