from flask import Flask, render_template, request, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# 1. Crear la aplicacion y configurarla
app = Flask(__name__)
app.config['SECRET_KEY'] = 'pon_una_contraseña_secreta_aqui' # Necesario para usar session
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///portal.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 2. Inicializar la base de datos
db = SQLAlchemy(app)

# 3. Definir los Modelos (Tablas)
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    contraseña = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), nullable=False)  # "profesor" o "estudiante"

    def establecer_contraseña(self, contraseña):
        self.contraseña = generate_password_hash(contraseña)

    def verificar_contraseña(self, contraseña):
        return check_password_hash(self.contraseña, contraseña)

    def __repr__(self):
        return f'<Usuario {self.usuario}>'

class Tarea(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    fecha_entrega = db.Column(db.Date, nullable=False)
    creada_por = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=db.func.now())

    profesor = db.relationship('Usuario', backref='tareas')

    def __repr__(self):
        return f'<Tarea {self.titulo}>'

class Estudiante(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    programa = db.Column(db.String(50), nullable=False)
    fecha_inscripcion = db.Column(db.DateTime, default=db.func.now())

    def __repr__(self):
        return f'<Estudiante {self.nombre}>'

# 4. Crear la base de datos y el usuario inicial (Dentro del contexto)
# 4. Crear la base de datos y el usuario inicial (Dentro del contexto)
with app.app_context():
    db.create_all()
    
    # Crear profesor si no existe
    if not Usuario.query.filter_by(usuario="henry").first():
        profesor = Usuario(usuario="henry", rol="profesor")
        profesor.establecer_contraseña("password123")
        db.session.add(profesor)
        db.session.commit()
        print("Profesor creado exitosamente")

    # --- ¡NUEVO CÓDIGO AQUÍ! ---
    # Crear un estudiante de prueba si no existe
    if not Usuario.query.filter_by(usuario="estudiante1").first():
        alumno = Usuario(usuario="estudiante1", rol="estudiante")
        alumno.establecer_contraseña("estudiante123") # Esta será la contraseña
        db.session.add(alumno)
        db.session.commit()
        print("Estudiante de prueba creado exitosamente")

# 5. Rutas de la aplicacion
@app.route("/")
def inicio():
    # Datos del portal
    nombre_profesor = "Henry"
    email_profesor = "hortegon@gmail.com"
    horario = "Miercoles 4:45-6:10 | Jueves 12:30-2:20"
    aula = "215"
    descripcion = "Aprenderemos Python, Flask y construiremos un portal web real"
    
    # Pasar los datos a la plantilla
    return render_template(
        "index.html",
        profesor=nombre_profesor,
        email=email_profesor,
        horario=horario,
        aula=aula,
        descripcion=descripcion
    )

@app.route("/inscripcion", methods=["GET", "POST"])
def inscripcion():
    mensaje = None
    
    if request.method == "POST":
        nombre = request.form.get("nombre")
        email = request.form.get("email")
        programa = request.form.get("programa")
        
        # Validacion
        if not nombre or not email or not programa:
            mensaje = "Por favor completa todos los campos."
        else:
            try:
                # Crear nuevo estudiante
                nuevo_estudiante = Estudiante(
                    nombre=nombre,
                    email=email,
                    programa=programa
                )
                
                # Guardar en BD
                db.session.add(nuevo_estudiante)
                db.session.commit()
                
                mensaje = f"Bienvenido {nombre}! Te hemos registrado."
            except Exception as e:
                db.session.rollback()
                mensaje = f"Error: Este email ya esta registrado."
    
    return render_template("inscripcion.html", mensaje=mensaje)

@app.route("/informacion")
def informacion():
    datos = {
        "aula": "215",
        "profesor": "Henry Ortegon",
        "horario": "Miercoles 16:45-18:10 | Jueves 12:30-14:20",
        "objetivos": [
            "Aprender Python basico",
            "Entender Flask y aplicaciones web",
            "Construir un portal web real"
        ]
    }
    return render_template("informacion.html", **datos)

@app.route("/recursos")
def recursos():
    enlaces = [
        {"nombre": "Documentacion Flask", "url": "https://flask.palletsprojects.com"},
        {"nombre": "Tutorial Python", "url": "https://docs.python.org"},
        {"nombre": "GitHub del Profesor", "url": "https://github.com/hortegon"},
        {"nombre": "MDN - HTML y CSS", "url": "https://developer.mozilla.org"}
    ]
    return render_template("recursos.html", enlaces=enlaces)

@app.route("/tareas")
def tareas():
    lista_tareas = [
        {"numero": 1, "titulo": "Portal base", "fecha": "25/05/2026"},
        {"numero": 2, "titulo": "Datos dinamicos", "fecha": "30/05/2026"},
        {"numero": 3, "titulo": "Multiple paginas", "fecha": "05/06/2026"},
        {"numero": 4, "titulo": "Nuevo", "fecha": "06/06/2026"}
    ]
    return render_template("tareas.html", tareas=lista_tareas)

@app.route("/estudiantes")
def estudiantes():
    if 'rol' not in session or session['rol'] != 'profesor':
        return redirect(url_for("login"))

    lista_estudiantes = Estudiante.query.all()
    return render_template("estudiantes.html", estudiantes=lista_estudiantes)

@app.route("/login", methods=["GET", "POST"])
def login():
    mensaje = None
    
    if request.method == "POST":
        usuario = request.form.get("usuario")
        contraseña = request.form.get("contraseña")
        
        user = Usuario.query.filter_by(usuario=usuario).first()
        
        if user and user.verificar_contraseña(contraseña):
            session['usuario_id'] = user.id
            session['usuario_nombre'] = user.usuario
            session['rol'] = user.rol
            
            if user.rol == "profesor":
                return redirect(url_for("panel_profesor"))
            else:
                return redirect(url_for("panel_estudiante"))
        else:
            mensaje = "Usuario o contraseña incorrectos."
    
    return render_template("login.html", mensaje=mensaje)

@app.route("/panel-profesor")
def panel_profesor():
    if 'usuario_id' not in session or session['rol'] != 'profesor':
        return redirect(url_for("login"))
    
    return render_template("panel_profesor.html", usuario=session['usuario_nombre'])

@app.route("/crear-tarea", methods=["GET", "POST"])
def crear_tarea():
    # Solo profesor
    if 'rol' not in session or session['rol'] != 'profesor':
        return redirect(url_for("login"))
    
    if request.method == "POST":
        titulo = request.form.get("titulo")
        descripcion = request.form.get("descripcion")
        fecha_texto = request.form.get("fecha_entrega")
        
        # Convertir el string de fecha a un objeto datetime.date
        fecha_obj = None
        if fecha_texto:
            fecha_obj = datetime.strptime(fecha_texto, '%Y-%m-%d').date()
        
        nueva_tarea = Tarea(
            titulo=titulo,
            descripcion=descripcion,
            fecha_entrega=fecha_obj,
            creada_por=session['usuario_id']
        )
        
        db.session.add(nueva_tarea)
        db.session.commit()
        
        return redirect(url_for("mis_tareas"))
    
    return render_template("crear_tarea.html")

@app.route("/mis-tareas")
def mis_tareas():
    if 'rol' not in session or session['rol'] != 'profesor':
        return redirect(url_for("login"))
    
    tareas = Tarea.query.all()
    return render_template("mis_tareas.html", tareas=tareas)

@app.route("/editar-tarea/<int:id>", methods=["GET", "POST"])
def editar_tarea(id):
    if 'rol' not in session or session['rol'] != 'profesor':
        return redirect(url_for("login"))
    
    tarea = Tarea.query.get_or_404(id)
    
    if request.method == "POST":
        tarea.titulo = request.form.get("titulo")
        tarea.descripcion = request.form.get("descripcion")
        
        # Convertir el string de fecha a un objeto datetime.date al actualizar
        fecha_texto = request.form.get("fecha_entrega")
        if fecha_texto:
            tarea.fecha_entrega = datetime.strptime(fecha_texto, '%Y-%m-%d').date()
        
        db.session.commit()
        return redirect(url_for("mis_tareas"))
    
    return render_template("editar_tarea.html", tarea=tarea)

@app.route("/eliminar-tarea/<int:id>")
def eliminar_tarea(id):
    if 'rol' not in session or session['rol'] != 'profesor':
        return redirect(url_for("login"))
    
    tarea = Tarea.query.get_or_404(id)
    db.session.delete(tarea)
    db.session.commit()
    
    return redirect(url_for("mis_tareas"))

@app.route("/panel-estudiante")
def panel_estudiante():
    if 'usuario_id' not in session or session['rol'] != 'estudiante':
        return redirect(url_for("login"))
    
    tareas = Tarea.query.all()
    return render_template("panel_estudiante.html", usuario=session['usuario_nombre'], tareas=tareas)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("inicio"))

if __name__ == "__main__":
    app.run(debug=True)