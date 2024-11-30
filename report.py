from flask import Flask, render_template, send_file, redirect, url_for, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
import pandas as pd
import requests
import matplotlib.pyplot as plt

app = Flask(__name__)
app.secret_key = '1234'  

#Configuración de Flask-Login
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
    #Obtener datos de la API
    response = requests.get("https://www.datos.gov.co/resource/mntw-htj4.json?municipio=SOGAMOSO")
    data = response.json()
    df = pd.DataFrame(data)

    #Obtener las columnas disponibles para graficar
    columnas_disponibles = df.columns.tolist()

    if request.method == 'POST':
        # Obtener el tipo de gráfico y las columnas seleccionadas
        tipo_grafico = request.form['tipo_grafico']
        nombres_columnas_validas = request.form.getlist('nombre_columnas')

        #Validar si se seleccionaron columnas
        if not nombres_columnas_validas:
            return "Error: No se seleccionaron columnas para graficar.", 400

        # Crear el gráfico según el tipo seleccionado
        plt.figure(figsize=(10, 6))

        if tipo_grafico == 'lineas':
            for nombre_columna in nombres_columnas_validas:
                if nombre_columna in df.columns:
                    plt.plot(df.index, pd.to_numeric(df[nombre_columna], errors='coerce'), label=nombre_columna)
                else:
                    return f"Error: La columna {nombre_columna} no existe en los datos.", 400

            plt.title('Gráfico de Líneas')
            plt.xlabel('Índice')
            plt.ylabel('Valores')
            plt.legend()

        elif tipo_grafico == 'barras':
            for nombre_columna in nombres_columnas_validas:
                if nombre_columna in df.columns:
                    plt.bar(df.index, pd.to_numeric(df[nombre_columna], errors='coerce'), label=nombre_columna)
                else:
                    return f"Error: La columna {nombre_columna} no existe en los datos.", 400

            plt.title('Gráfico de Barras')
            plt.xlabel('Índice')
            plt.ylabel('Valores')
            plt.legend()

        elif tipo_grafico == 'pie':
            if len(nombres_columnas_validas) != 1:
                return "Error: El gráfico de pastel solo permite seleccionar una columna.", 400

            columna = nombres_columnas_validas[0]
            if columna in df.columns:
                valores = pd.to_numeric(df[columna], errors='coerce').dropna()
                etiquetas = valores.index

                plt.pie(
                    valores, 
                    labels=etiquetas, 
                    autopct='%1.1f%%', 
                    startangle=90,  #Inicia desde un ángulo para mejorar la distribución
                    labeldistance=1.1  #Aumenta la distancia de las etiquetas
                )
                plt.title(f'Gráfico de Pastel: {columna}')
            else:
                return f"Error: La columna {columna} no existe en los datos.", 400

        #Guardar el gráfico en formato PNG y PDF
        plt.savefig('static/grafico.png')
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