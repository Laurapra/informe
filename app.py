from flask import Flask, render_template, send_file, redirect, url_for, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
import pandas as pd
import requests
import matplotlib.pyplot as plt
import os

app = Flask(__name__)
app.secret_key = '1234'  

# Configuración de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# Simulación de una base de datos de usuarios
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

@app.route('/report')
@login_required
def report():
    # Obtener datos de la API
    response = requests.get("https://www.datos.gov.co/resource/mntw-htj4.json?municipio=SOGAMOSO")
    data = response.json()
    df = pd.DataFrame(data)

    # Imprimir las columnas del DataFrame para verificar su contenido
    print("Columnas disponibles en el DataFrame:", df.columns.tolist())

    # Resumen estadístico
    summary = df.describe()

    # Elegir una columna válida para graficar
    nombre_columna_valida = 'tipo_de_vinculaci_n'  # Cambia esto según el resultado de la impresión anterior

    if nombre_columna_valida in df.columns:
        plt.figure(figsize=(10, 6))
        df[nombre_columna_valida].value_counts().plot(kind='bar')  
        plt.title('Cantidad de Trámites por Tipo de Vinculación')
        plt.xlabel('Tipo de Vinculación')
        plt.ylabel('Cantidad de Trámites')
        plt.xticks(rotation=45)  # Rotar las etiquetas del eje X si es necesario
        plt.savefig('static/grafico.png')  # Guarda el gráfico en la carpeta 'static'
        plt.close()
    else:
        print(f"Error: La columna '{nombre_columna_valida}' no existe en el DataFrame.")
        return "Error: La columna seleccionada no existe en los datos."

    # Guardar el informe como un archivo HTML
    report_file = 'informe.html'
    df.to_html(report_file)

    return render_template('report.html', tables=[summary.to_html(classes='data')], graph='grafico.png')

@app.route('/download')
@login_required
def download():
    return send_file('informe.html', as_attachment=True)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)