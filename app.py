from flask import Flask, render_template, send_file, redirect, url_for, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
import pandas as pd
import requests
import matplotlib.pyplot as plt
import numpy as np

app = Flask(__name__)
app.secret_key = '1234'  # Cambia esto por una clave secreta más segura en producción

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

#Simulación de una base de datos de usuarios
users = {'usuario1': {'password': '1234'}} 

class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            user = User(username)
            login_user(user)
            return redirect(url_for('report'))
        else:
            return "Credenciales incorrectas", 401
    return render_template('login.html')

@app.route('/report', methods=['GET', 'POST'])
@login_required
def report():
    # Obtener datos de la API
    response = requests.get("https://www.datos.gov.co/resource/mntw-htj4.json?municipio=SOGAMOSO")
    data = response.json()
    df = pd.DataFrame(data)

    # Obtener las columnas disponibles para graficar
    columnas_disponibles = df.columns.tolist()

    if request.method == 'POST':
        # Obtener el tipo de gráfico y las columnas seleccionadas
        tipo_grafico = request.form['tipo_grafico']
        nombres_columnas_validas = request.form.getlist('nombre_columnas')

        # Crear un gráfico con todas las columnas seleccionadas
        plt.figure(figsize=(10, 6))

        for nombre_columna_valida in nombres_columnas_validas:
            if nombre_columna_valida in df.columns:
                plt.plot(df.index, df[nombre_columna_valida], label=nombre_columna_valida)
            else:
                return "Error: La columna seleccionada no existe en los datos."

        plt.title('Gráfico de Múltiples Columnas')
        plt.xlabel('Índice')
        plt.ylabel('Valores')
        plt.legend()

        # Guardar el gráfico en formato PNG
        plt.savefig('static/grafico.png')
        
        # Guardar el gráfico en formato PDF
        plt.savefig('static/grafico.pdf', format='pdf')
        plt.close()

        return render_template('report_form.html', columnas=columnas_disponibles, grafico=True)

    return render_template('report_form.html', columnas=columnas_disponibles)

@app.route('/download_pdf')
def download_pdf():
    return send_file('static/grafico.pdf', as_attachment=True)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)