
from flask import Flask, render_template, request, redirect
import psycopg2
import os
from dotenv import load_dotenv
from collections import defaultdict

# Cargar variables de entorno desde el archivo .env
load_dotenv()

app = Flask(__name__)

# Obtener la URL de la base de datos desde las variables de entorno
DATABASE_URL = os.getenv("DATABASE_URL")

# Función para conectarse a la base de datos
def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, client_encoding='UTF8')
    return conn

@app.route('/productos')
def productos():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT p.nombre, p.descripcion, p.precio, p.disponibilidad,
               c.nombre AS categoria, u.nombre AS unidad
        FROM productos p
        JOIN categorias c ON p.categoria_id = c.id
        JOIN unidades u ON p.unidad_id = u.id
        ORDER BY p.nombre
    ''')

    lista = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('productos.html', lista=lista)

@app.route('/panel')
def panel():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT p.nombre, p.descripcion, u.nombre AS unidad, p.precio, m.fecha
        FROM menu_del_dia m
        JOIN productos p ON m.producto_id = p.id
        JOIN unidades u ON p.unidad_id = u.id
        ORDER BY p.nombre, p.descripcion, u.nombre
    ''')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # Agrupar por (nombre, descripcion)
    menus = defaultdict(list)
    for nombre, descripcion, unidad, precio, fecha in rows:
        key = (nombre, descripcion)
        menus[key].append({'unidad': unidad, 'precio': precio, 'fecha': fecha})

    return render_template('panel.html', menus=menus)

@app.route('/agregar_menu', methods=['GET', 'POST'])
def agregar_menu():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT id, descripcion, nombre FROM productos')
    productos = cursor.fetchall()

    if request.method == 'POST':
        producto_id = request.form['producto_id']
        fecha = request.form['fecha']

        cursor.execute('''
            INSERT INTO menu_del_dia (producto_id, fecha)
            VALUES (%s, %s)
        ''', (producto_id, fecha))

        conn.commit()
        cursor.close()
        conn.close()
        return redirect('/panel')

    cursor.close()
    conn.close()
    return render_template('agregar_menu.html', productos=productos)

@app.route('/eliminar_menu/<int:id>', methods=['POST'])
def eliminar_menu(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM menu_del_dia WHERE id = %s', (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/panel')

@app.route('/')
def inicio():
    return render_template('inicio.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)

