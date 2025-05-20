from flask import Flask, render_template, request, redirect
import psycopg2
import os
from dotenv import load_dotenv
from collections import defaultdict

# Cargar variables de entorno desde .env
load_dotenv()

app = Flask(__name__)
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, client_encoding='UTF8')
    return conn

# Inicio
@app.route('/')
def inicio():
    return render_template('inicio.html')

# -------------------- PRODUCTOS --------------------

@app.route('/productos', methods=['GET', 'POST'])
def productos():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Guardar cambios si hay POST
    if request.method == 'POST':
        producto_id = request.form['guardar']
        nuevo_precio = request.form[f'precio_{producto_id}']
        nueva_disponibilidad = request.form[f'disponibilidad_{producto_id}'] == 'true'

        cursor.execute('''
            UPDATE productos
            SET precio = %s, disponibilidad = %s
            WHERE id = %s
        ''', (nuevo_precio, nueva_disponibilidad, producto_id))
        conn.commit()

    # Obtener lista actualizada de productos
    cursor.execute('''
        SELECT p.id, p.nombre, p.descripcion, p.precio, p.disponibilidad,
               c.nombre AS categoria, u.nombre AS unidad
        FROM productos p
        JOIN categorias c ON p.categoria_id = c.id
        JOIN unidades u ON p.unidad_id = u.id
        ORDER BY p.nombre
    ''')
    lista = cursor.fetchall()

    # Convertir a lista de diccionarios para más claridad en Jinja
    productos_list = []
    for row in lista:
        productos_list.append({
            'id': row[0],
            'nombre': row[1],
            'descripcion': row[2],
            'precio': row[3],
            'disponibilidad': row[4],
            'categoria': row[5],
            'unidad': row[6]
        })

    cursor.close()
    conn.close()
    return render_template('productos.html', lista=productos_list)

# -------------------- MENÚ DEL DÍA --------------------

@app.route('/panel')
def panel():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT m.id, p.nombre, p.descripcion, u.nombre AS unidad, p.precio, m.fecha
        FROM menu_del_dia m
        JOIN productos p ON m.producto_id = p.id
        JOIN unidades u ON p.unidad_id = u.id
        ORDER BY p.nombre
    ''')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # Agrupar por nombre y descripción
    menus = defaultdict(list)
    for menu_id, nombre, descripcion, unidad, precio, fecha in rows:
        key = (nombre, descripcion)
        menus[key].append({
            'unidad': unidad,
            'precio': precio,
            'fecha': fecha,
            'menu_id': menu_id
        })

    return render_template('panel.html', menus=menus)

@app.route('/agregar_menu', methods=['GET', 'POST'])
def agregar_menu():
    conn = get_db_connection()
    cursor = conn.cursor()

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

    cursor.execute('SELECT id, descripcion, nombre FROM productos ORDER BY nombre')
    productos = cursor.fetchall()
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

# -------------------- RUN APP --------------------

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
