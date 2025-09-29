# Compañero de Viaje

Aplicación web minimal para gestionar planes de viaje con registro/inicio de sesión, creación de viajes, unirse/cancelar y eliminación (solo creador).

Características principales:
- Registro / Inicio de sesión con validaciones (contraseña >= 8 caracteres).
- Página principal: muestra "Mi Calendario de Viajes" (viajes creados o unidos) y "Planes disponibles" (de otros usuarios).
- Ver detalles de cada viaje y la lista de usuarios unidos (excluye al creador).
- Crear nuevos viajes con validaciones y mostrar errores en la página.
- Enlace "Unir" para unirse a un viaje; "Cancelar" para quitar del calendario del usuario; "Eliminar" solo aparece al creador.

Requisitos técnicos:
- Flask + Flask-Login + Flask-SQLAlchemy
- Base de datos SQLite por defecto (fácil de desplegar en EC2)
- Dockerfile incluido para despliegue en EC2 (recomendado usar ECS o VM con Docker)

Cómo ejecutar localmente (Windows PowerShell):

1) Crear e instalar dependencias en virtualenv (recomendado):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

2) Inicializar la base de datos y ejecutar:

```powershell
setx FLASK_APP app.py; setx FLASK_ENV development; python app.py
```

La aplicación escuchará por defecto en http://127.0.0.1:5000

Despliegue en EC2 (resumen):
- Construir la imagen Docker localmente y empujar a un registry (o compilar en la VM EC2). Ejemplo:
  - docker build -t compañero_viaje:latest .
  - docker run -p 5000:5000 compañero_viaje:latest

- En EC2 puede ejecutar con Docker o configurar systemd para ejecutar el contenedor. Asegúrese de abrir el puerto 5000 o configurar un reverse-proxy (Nginx) y un nombre de dominio.

Notas:
- Este repositorio contiene código listo para probar localmente. No despliego automáticamente a EC2 desde aquí.
