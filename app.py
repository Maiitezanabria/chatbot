from flask import Flask, request, render_template, redirect
import psycopg2
import os
from dotenv import load_dotenv
from datetime import date
import requests
from collections import defaultdict

# === CARGAR VARIABLES DE ENTORNO ===
load_dotenv()

# === CONFIGURACIÓN DE FLASK ===
app = Flask(__name__)
DATABASE_URL = os.getenv("DATABASE_URL")

# === CONFIGURACIÓN DE WHATSAPP (API de Meta) ===
PHONE_NUMBER_ID = '713498288506815'
ACCESS_TOKEN = 'EAATbmmYZAMZCIBOx6GCW8rOoD18ds0nkDzdtojyjXXpjeYsAz9M4c08WNsZAJu1KFCciFUFeJLtF3jmmtWCz4g1DHfDsMLwYrzjZAwq7VdMfubdDvv184hGZBPrV1Xbh3fKiV8JkYBmvzZCtdDjBnf655rXdzPkUi4l1ZBumsiMuQdeIQ6FPapc9nY4rapgzzeWKZAyEsyYeW9eA9lOpZAZCgKK4EP2kwZD'
WHATSAPP_API_URL = f'https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages'
HEADERS = {
    'Authorization': f'Bearer {ACCESS_TOKEN}',
    'Content-Type': 'application/json'
}

# === CONEXIÓN A BASE DE DATOS ===
def get_db_connection():
    return psycopg2.connect(DATABASE_URL, client_encoding='UTF8')

# === ENVIAR MENSAJE WHATSAPP ===
def enviar_mensaje(destinatario, mensaje):
    data = {
        'messaging_product': 'whatsapp',
        'to': destinatario,
        'type': 'text',
        'text': {'body': mensaje}
    }
    response = requests.post(WHATSAPP_API_URL, headers=HEADERS, json=data)
    print("WhatsApp Status:", response.status_code)
    print("Respuesta:", response.json())

# === VERIFICACIÓN DEL WEBHOOK DE META (GET) ===
@app.route('/webhook', methods=['GET'])
def verificar_webhook():
    TOKEN_VERIFICACION = 'rotiseria1234'
    modo = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if modo == 'subscribe' and token == TOKEN_VERIFICACION:
        print("✅ Webhook verificado correctamente.")
        return challenge, 200
    else:
        print("❌ Falló la verificación del webhook.")
        return 'Error de verificación', 403

# === ENDPOINT PARA RECIBIR MENSAJES DE WHATSAPP (POST) ===
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    try:
        mensaje = data['entry'][0]['changes'][0]['value']['messages'][0]['text']['body'].strip().lower()
        telefono = data['entry'][0]['changes'][0]['value']['messages'][0]['from']
        print(f"Mensaje recibido: {mensaje} de {telefono}")

        if mensaje == "hola":
            respuesta = (
                "¡Hola! 👋 Bienvenido a *Sabor Casero*.\n"
                "Podés consultar el menú del día, ver los productos disponibles o hacer un pedido.\n"
                "¿Qué te gustaría hacer hoy?"
            )
            enviar_mensaje(telefono, respuesta)

    except Exception as e:
        print("Error al procesar mensaje:", e)

    return 'ok', 200



# === PANEL DEL DUEÑO ===

@app.route('/')
def inicio():
    return render_template('inicio.html')

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
        SELECT m.id, p.nombre, p.descripcion, u.nombre AS unidad, p.precio, m.fecha
        FROM menu_del_dia m
        JOIN productos p ON m.producto_id = p.id
        JOIN unidades u ON p.unidad_id = u.id
        ORDER BY p.nombre, p.descripcion, u.nombre
    ''')
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    menus = defaultdict(list)
    for id_menu, nombre, descripcion, unidad, precio, fecha in rows:
        key = (nombre, descripcion)
        menus[key].append({
            'id': id_menu,
            'unidad': unidad,
            'precio': precio,
            'fecha': fecha
        })

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
        cursor.execute('SELECT precio FROM productos WHERE id = %s', (producto_id,))
        resultado = cursor.fetchone()

        if resultado is None:
            cursor.close()
            conn.close()
            return "Producto no encontrado", 400

        precio_menu = resultado[0]
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

# === EJECUCIÓN DEL SERVIDOR ===
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
