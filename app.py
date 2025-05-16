
#Inicializar el servidor 
from flask import Flask, render_template, request, redirect
import psycopg2



# Configuración de la base de datos PostgreSQL
#DATABASE_URL = 'postgres://postgres:101214@localhost:5432/rotiseria'

import os
DATABASE_URL = os.getenv ("postgresql://rotiseria_db_user:YxkD1Ah8Z5IROmTQfVYUa2eYjiYUGBlJ@dpg-d0i1j86mcj7s739jtjcg-a.oregon-postgres.render.com/rotiseria_db")


app = Flask(__name__)

# Función para conectarse a la base de datos
def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, client_encoding='UTF8')
    return conn

@app.route('/productos')
def productos():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT p.nombre, p.descripcion, p.precio, p.disponibilidad
        FROM productos p
        ORDER BY p.nombre
    ''')
    lista = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('productos.html', lista=lista)

    lista = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('productos.html', lista=lista)

@app.route('/agregar_menu', methods=['GET', 'POST'])
def agregar_menu():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT id, nombre FROM productos')
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

@app.route('/panel')
def panel():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT m.id, p.nombre, m.fecha
        FROM menu_del_dia m
        JOIN productos p ON m.producto_id = p.id
        ORDER BY m.fecha DESC
    ''')
    menus = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('panel.html', menus=menus)

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
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)

 #app.run(debug=True)
