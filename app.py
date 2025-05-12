
#Inicializar el servidor 
from flask import Flask, render_template, request, redirect
import psycopg2

# Configuración de la base de datos PostgreSQL
import os
DATABASE_URL = os.environ.get('DATABASE_URL')


app = Flask(__name__)

# Función para conectarse a la base de datos
def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, client_encoding='UTF8')
    return conn

@app.route('/productos')
def productos_variantes():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT p.nombre, v.nombre_variacion, v.precio, v.disponible
        FROM productos p
        JOIN variantes_producto v ON p.id = v.producto_id
        ORDER BY p.nombre, v.nombre_variacion
    ''')

    lista = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('productos.html', lista=lista)

@app.route('/agregar_menu', methods=['GET', 'POST'])
def agregar_menu():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener los productos y variantes
    cursor.execute('SELECT id, nombre FROM productos')
    productos = cursor.fetchall()

    cursor.execute('SELECT id, nombre_variacion FROM variantes_producto')
    variantes = cursor.fetchall()

    if request.method == 'POST':
        # Obtener los valores seleccionados
        producto_id = request.form['producto_id']
        variante_id = request.form['variante_id']
        fecha = request.form['fecha']

        # Insertar en la base de datos
        cursor.execute('''
            INSERT INTO menu_del_dia (producto_id, variante_id, fecha) 
            VALUES (%s, %s, %s)
        ''', (producto_id, variante_id, fecha))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect('/panel')

    return render_template('agregar_menu.html', productos=productos, variantes_producto=variantes)

@app.route('/panel')
def panel():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Actualización de la consulta para obtener también el nombre de la variante
    cursor.execute('''
        SELECT m.id, p.nombre, v.nombre_variacion, m.fecha
        FROM menu_del_dia m
        JOIN productos p ON m.producto_id = p.id
        JOIN variantes_producto v ON m.variante_id = v.id
    ''')
    menus = cursor.fetchall()

    cursor.execute('SELECT id, nombre FROM productos')
    productos = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('panel.html', menus=menus, productos=productos)

@app.route('/eliminar_menu/<int:id>', methods=['POST'])
def eliminar_menu(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM menu_del_dia WHERE id = %s', (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect('/panel')


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
