from flask import Flask, render_template, request, redirect
import psycopg2
import os
from dotenv import load_dotenv
from collections import defaultdict
import json

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

    if request.method == 'POST':
        # Actualizar precio y disponibilidad de productos
        for key in request.form:
            if key.startswith('precio_'):
                producto_id = key.split('_')[1]
                precio = request.form[key]
                disponibilidad_str = request.form.get(f'disponibilidad_{producto_id}', 'false')
                disponibilidad = True if disponibilidad_str == 'true' else False

                cursor.execute('''
                    UPDATE productos
                    SET precio = %s, disponibilidad = %s
                    WHERE id = %s
                ''', (precio, disponibilidad, producto_id))
        conn.commit()

    cursor.execute('''
        SELECT p.nombre, p.descripcion, p.precio, p.disponibilidad,
               c.nombre AS categoria, u.nombre AS unidad, p.id
        FROM productos p
        JOIN categorias c ON p.categoria_id = c.id
        JOIN unidades u ON p.unidad_id = u.id
        ORDER BY p.nombre
    ''')

    lista = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('productos.html', lista=lista)

# -------------------- MENÚ DEL DÍA --------------------

@app.route('/panel')
def panel():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT m.id, p.nombre, p.descripcion, u.nombre AS unidad, m.precio_menu, m.fecha
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
    for menu_id, nombre, descripcion, unidad, precio_menu, fecha in rows:
        key = (nombre, descripcion)
        menus[key].append({
            'unidad': unidad,
            'precio_menu': precio_menu,
            'fecha': fecha,
            'menu_id': menu_id
        })

    return render_template('panel.html', menus=menus)

@app.route('/agregar_menu', methods=['GET', 'POST'])
def agregar_menu():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT id, nombre, descripcion, precio FROM productos')
    productos_raw = cursor.fetchall()

    # Convertir a lista de dicts para facilitar JS
    productos = []
    for p in productos_raw:
        productos.append({
            'id': p[0],
            'nombre': p[1],
            'descripcion': p[2],
            'precio': float(p[3])
        })

    if request.method == 'POST':
        producto_id = request.form['producto_id']
        fecha = request.form['fecha']
        precio_menu = request.form['precio_menu']

        cursor.execute('''
            INSERT INTO menu_del_dia (producto_id, precio_menu, fecha)
            VALUES (%s, %s, %s)
        ''', (producto_id, precio_menu, fecha))

        conn.commit()
        cursor.close()
        conn.close()
        return redirect('/panel')

    cursor.close()
    conn.close()

    return render_template('agregar_menu.html', productos=productos, productos_json=json.dumps(productos))

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
