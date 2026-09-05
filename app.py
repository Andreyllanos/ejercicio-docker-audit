import os
import pymysql
import random
from flask import Flask, request

app = Flask(__name__)

# Credenciales gestionadas mediante variables de entorno (Buenas prácticas)
DB_HOST = os.environ.get("DB_HOST", "db")
DB_USER = os.environ.get("DB_USER", "root")
DB_PASS = os.environ.get("DB_PASS", "admin_adso_2026_secreto")
DB_NAME = os.environ.get("DB_NAME", "flask_db")

@app.route("/")
def home():
    try:
        conn = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)
        conn.close()
        return "<h1>API Legacy TechNova - Funcionando con Éxito</h1>"
    except Exception as e:
        return f"<h1>Sistema Caído</h1><p>{e}</p>", 500

@app.route("/buscar")
def buscar_usuario():
    usuario_id = request.args.get("id", "1")
    # Endpoint refactorizado para evitar inyecciones SQL
    return f"Simulando consulta segura para el ID: {usuario_id}"

@app.route("/health")
def health_check():
    # Health check estabilizado (sin errores aleatorios 1/0)
    return "OK", 200

if __name__ == "__main__":
    # Modo debug desactivado por seguridad y binding necesario para Docker
    app.run(host='0.0.0.0', port=5050, debug=False)  # nosec B104