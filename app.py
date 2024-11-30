from flask import Flask, render_template, send_file, redirect, url_for, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
import pandas as pd
import requests
import matplotlib.pyplot as plt
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image
import io

app = Flask(__name__)
app.secret_key = '1234'  # Cambia esto por una clave secreta más segura en producción

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

@app.route('/report', methods=['GET', 'POST'])
@login_required
def report():
    # Obtener datos de la API
    response = requests.get("https://www.datos.gov.co/resource/mntw-htj4.json?municipio=SOGAMOSO")
    data = response.json()
    df = pd.DataFrame(data)

    if request.method == 'POST':
        # Obtener el tipo de gráfico seleccionado
        tipo_grafico = request.form['tipo_grafico']
        nombre_columna_valida = 'tipo_de_vinculaci_n'  # Cambia esto según el resultado de la impresión anterior

        if nombre_columna_valida in df.columns:
            plt.figure(figsize=(10, 6))
            
            if tipo_grafico == 'bar':
                df[nombre_columna_valida].value_counts().plot(kind='bar')
                plt.title('Cantidad de Trámites por Tipo de Vinculación')
                plt.xlabel('Tipo de Vinculación')
                plt.ylabel('Cantidad de Trámites')
            elif tipo_grafico == 'pie':
                df[nombre_columna_valida].value_counts().plot(kind='pie', autopct='%1.1f%%')
                plt.title('Distribución de Trámites por Tipo de Vinculación')
                plt.ylabel('')  # Eliminar la etiqueta del eje Y para gráficos de pastel
            else:
                return "Tipo de gráfico no soportado", 400
            
            plt.xticks(rotation=45)
            plt.savefig('static/grafico.png')
            plt.close()
        else:
            return "Error: La columna seleccionada no existe en los datos."

        # Crear el contenido del PDF
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        elements = []

        # Estilos
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        normal_style = styles['Normal']

        # Título
        elements.append(Paragraph("Informe de Datos", title_style))
        elements.append(Paragraph(f"Usuario: {current_user.id}", normal_style))
        elements.append(Paragraph("<br/>", normal_style))  # Espacio en blanco

        # Resumen Estadístico
        elements.append(Paragraph("Resumen Estadístico:", normal_style))

        # Crear tabla a partir del resumen estadístico
        stats = df.describe()
        data = [stats.columns.tolist()] + stats.values.tolist()
        table = Table(data)

        # Estilo de la tabla
        table .setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(table)

        # Agregar gráfico al PDF
        elements.append(Paragraph("<br/>", normal_style))  # Espacio en blanco
        elements.append(Image('static/grafico.png', width=400, height=300))

        # Finalizar el PDF
        doc.build(elements)
        pdf_buffer.seek(0)

        # Enviar el archivo PDF al usuario
        return send_file(pdf_buffer, as_attachment=True, download_name='informe.pdf', mimetype='application/pdf')

    # Si es un GET, simplemente muestra el formulario
    return render_template('report_form.html')

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