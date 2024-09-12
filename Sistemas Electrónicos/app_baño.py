# Importación de librerias
from flask import Flask, render_template, jsonify
from gpiozero import MCP3008, MotionSensor, PWMLED, AngularServo, Button, LED
from gpiozero.pins.pigpio import PiGPIOFactory
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import io
import base64
from time import sleep

# Creación de la app
app = Flask(__name__)
# Sensor de movimiento
"""
Se declara el sensor de movimiento al pin GPIO 14 y la bombilla al GPIO15, cuando el sensor detecte movimiento, el programa recibirá
la señal y actuará en consecuencia, accediendo a las funciones de bombilla_on para encenderla y off para apagarl cuando no haya
movimiento.
"""
sensor_movimiento = MotionSensor(14)
bombilla = LED(15)


def bombilla_on():
    global bombilla
    bombilla.on()
    print("Bombilla encendida.")


def bombilla_off():
    global bombilla
    bombilla.off()
    print("Bombilla apagada.")


sensor_movimiento.when_motion = bombilla_on
sensor_movimiento.when_no_motion = bombilla_off


# Configuración del sensor de temperatura y humedad

"""
Se declara la salidad del sensor de temperatura al canal 1 de la raspberry y el de humedad al 0.
"""
factory = PiGPIOFactory()
sensor_temperatura = MCP3008(channel=1)
sensor_humedad = MCP3008(channel=0)

"""
Declaramos los servos, el de la ducha al pin 23 y el de al puerta al 22, inicializamos sus angulos a 0 para que no haya problemas
a la hora de abrirlos.
"""
# servo de la ducha
factory = PiGPIOFactory()
servo_ducha = AngularServo(
    23,
    min_angle=0,
    max_angle=180,
    min_pulse_width=0.0005,
    max_pulse_width=0.0025,
    pin_factory=factory,
)
servo_ducha.min()
angulo_servo_ducha = 0

# servo de la puerta
servo_puerta = AngularServo(
    22,
    min_angle=0,
    max_angle=180,
    min_pulse_width=0.0005,
    max_pulse_width=0.0025,
    pin_factory=factory,
)
servo_puerta.min()
angulo_servo_puerta = 0

# Listas donde guardaremos los datos por segundos del sensor de temperatura y humedad.
temperatura_data = []
humedad_data = []
time_data = [0]


# Función de captura de datos de temperatura y humedad
def capture_data():
    global temperatura_data, humedad_data, time_data
    while True:
        temperatura_data.append(sensor_temperatura.value)
        humedad_data.append(sensor_humedad.value)
        time_data.append(time_data[-1] + 1)  # Incrementa el tiempo
        sleep(1)


# Inicializamos el hilo para capturar datos
capture_thread = threading.Thread(target=capture_data)
capture_thread.daemon = True
capture_thread.start()


# Definimos la ruta principal
@app.route("/")
def index():
    return render_template("index2.html")


# Ruta para el botón que abre la puerta
@app.route("/abrir_puerta", methods=["POST"])
def abrir_puerta():
    angulo_servo_puerta = 45
    servo_puerta.angle = angulo_servo_puerta
    sleep(2)
    servo_puerta.min()
    return "Puerta abierta"


"""
En la app, para aquellas rutas como los servos hemos usado el método post ya que el motor recibe una señal desde la app para actuar.
Mientras que para las rutas de captura de datos de los sensores de temperatura y humedad, usamos el método GET ya que es la app
la que tiene que extraer estos datos de la app.
"""


# Ruta para el botón que abre la ducha
@app.route("/abrir_ducha", methods=["POST"])
def abrir_ducha():
    global servo_ducha, angulo_servo_ducha, contador_ducha
    angulo_servo_ducha = 180
    servo_ducha.angle = angulo_servo_ducha
    sleep(5)
    servo_ducha.min()
    return "Ducha abierta"


# Ruta para obtener datos de temperatura
@app.route("/temperatura", methods=["GET"])
def get_temperatura():
    return jsonify(temperatura_data)


# Ruta para obtener datos de humedad
@app.route("/humedad", methods=["GET"])
def get_humedad():
    return jsonify(humedad_data)


# Función para generar la gráfica de temperatura
@app.route("/temperatura_chart")
def temperatura_chart():
    fig, ax = plt.subplots()
    ax.plot(time_data, temperatura_data)
    ax.set_xlabel("Tiempo")
    ax.set_ylabel("Temperatura")
    ax.set_title("Gráfico de Temperatura")

    # Convertir la figura a una representación base64
    img = io.BytesIO()
    fig.savefig(img, format="png")
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode()

    # Limpieza y cierre de la figura
    plt.close(fig)

    return f"data:image/png;base64,{img_base64}"


# Función para generar la gráfica de humedad
@app.route("/humedad_chart")
def humedad_chart():
    fig, ax = plt.subplots()
    ax.plot(time_data, humedad_data)
    ax.set_xlabel("Tiempo")
    ax.set_ylabel("Humedad")
    ax.set_title("Gráfico de Humedad")

    # Convertir la figura a una representación base64
    img = io.BytesIO()
    fig.savefig(img, format="png")
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode()

    # Limpieza y cierre de la figura
    plt.close(fig)

    return f"data:image/png;base64,{img_base64}"


if __name__ == "__main__":
    # app.run(debug=True, port=8000)
    app.run(host="0.0.0.0", port=8000)
