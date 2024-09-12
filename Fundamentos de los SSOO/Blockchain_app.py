import Blockchain
from uuid import uuid4

import platform
import socket
from flask import Flask, jsonify, request
from argparse import ArgumentParser

import time
from threading import Thread, Semaphore
import requests
import hashlib
import json
import copy

# Semáforo para manejar concurrencia
mutex_1 = Semaphore(1)
mutex_2 = Semaphore(1)

# Instancia de la aplicación Flask
app = Flask(__name__)

# Instancia de la cadena de bloques
blockchain = Blockchain.Blockchain()

# Dirección IP del nodo actual (sustituir con la dirección real)
mi_ip = "192.168.1.106"
mi_ip_local = "127.0.0.1"
mi_puerto = "5002"


# Ruta para recibir nuevas transacciones
@app.route("/transacciones/nueva", methods=["POST"])
def nueva_transaccion():
    mutex_1.acquire()
    values = request.get_json()
    # Comprobamos que todos los datos de la transaccion están presentes
    required = ["origen", "destino", "cantidad"]
    if not all(k in values for k in required):
        return "Faltan valores", 400
    # Creamos una nueva transacción
    indice = blockchain.nueva_transaccion(
        values["origen"], values["destino"], values["cantidad"]
    )
    response = {
        "mensaje": f"La transacción se incluirá en el bloque con índice {indice}"
    }
    print(blockchain.transacciones_no_confirmadas)
    mutex_1.release()
    return jsonify(response), 201


# Ruta para obtener la cadena de bloques completa
@app.route("/chain", methods=["GET"])
def blockchain_completa():
    """
    Endpoint para obtener la cadena completa de bloques mediante una solicitud GET.

    :return: Una respuesta JSON con la cadena de bloques y su longitud.
    """
    mutex_2.acquire()
    # Construimos la respuesta JSON que incluye la cadena de bloques y su longitud
    response = {
        "chain": [b.toDict() for b in blockchain.bloques if b.hash is not None],
        "longitud": len(blockchain.bloques),
    }  # Se permite la cadena de bloques solo con bloques finales que tienen hash
    mutex_2.release()
    # Respondemos con la cadena de bloques y un código de éxito 200
    return jsonify(response), 200


# Ruta para minar un nuevo bloque
@app.route("/minar", methods=["GET"])
def minar():
    mutex_1.acquire()
    # No hay transacciones
    if len(blockchain.transacciones_no_confirmadas) == 0:
        response = {
            "mensaje": "No es posible crear un nuevo bloque. No hay transacciones"
        }
    else:
        # Hay transacciones, por lo tanto, además de minar el bloque, se recibe recompensa
        blockchain.nueva_transaccion("0", "192.168.1.106", 1)
        conflictos = resuelve_conflictos()
        if conflictos == True:
            # Borro las transacciones actuales no confirmadas
            blockchain.transacciones_no_confirmadas = []
            response = {
                "mensaje": "Ha habido un conflicto. Esta cadena se ha actualizado con una version mas larga"
            }  # Obligando al nodo a volver a volver a capturar transacciones si quiere crear él un nuevo bloque
        else:
            nuevo_bloque = Blockchain.Bloque(
                len(blockchain.bloques) + 1,
                blockchain.transacciones_no_confirmadas,
                time.time(),
                blockchain.last_block().hash,
                "0",
                0,
            )

        nuevo_hash = blockchain.prueba_trabajo(nuevo_bloque)
        validez = blockchain.integra_bloque(nuevo_bloque, nuevo_hash)
        if validez and not conflictos:
            response = {
                "hash_bloque": nuevo_bloque.hash,
                "hash_previo": nuevo_bloque.hash_previo,
                "indice": nuevo_bloque.indice,
                "mensaje": "Nuevo bloque minado",
                "prueba": nuevo_bloque.prueba,
                "timestamp": nuevo_bloque.timestamp,
                "transacciones": nuevo_bloque.transacciones,
            }
        else:
            response = {
                "mensaje": "Ha habido un conflicto. Esta cadena se ha actualizado con una versión más larga"
            }
    mutex_1.release()

    return jsonify(response), 200


# Ruta para obtener detalles del sistema del nodo actual
@app.route("/system", methods=["GET"])
def detalles_nodo_actual():
    """
    Endpoint para obtener detalles específicos del nodo actual, como el sistema operativo, su versión y el tipo de procesador.

    :return: Una respuesta JSON con información sobre el sistema del nodo.
    """
    mutex_1.acquire()

    response = {
        "maquina": platform.machine(),
        "nombre_sistema": platform.system(),
        "version": platform.version(),
    }

    mutex_1.release()

    # Respondemos con los detalles del sistema y un código de éxito 200

    return jsonify(response), 200


# Lista de nodos en la red
nodos_red = []


# Ruta para registrar nodos en la red
@app.route("/nodos/registrar", methods=["POST"])
def registrar_nodos_completo():
    """
    Endpoint para registrar nodos en la red y actualizar sus blockchains.
    :return: Una respuesta JSON con información sobre el resultado del registro de nodos.
    """
    mutex_1.acquire()

    values = request.get_json()

    global blockchain
    global nodos_red

    nodos_nuevos = values.get("direccion_nodos")

    if nodos_nuevos is None:
        return "Error: No se ha proporcionado una lista de nodos", 400

    nodo_local = "http://" + mi_ip_local + ":" + mi_puerto
    nodo_red_enviar = []
    nodo_red_enviar.append(nodo_local)

    all_correct = True
    for nodo in nodos_nuevos:
        nodo_red_enviar.append(nodo)

    for nodo in nodos_nuevos:
        if (
            (nodo not in nodos_red)
            and (nodo != ("http://" + mi_ip + ":" + mi_puerto))
            and (nodo != ("http://" + mi_ip_local + ":" + mi_puerto))
        ):
            nodos_red.append(nodo)
        nodo_enviados = nodo_red_enviar.copy()
        nodo_enviados.remove(nodo)
        data = {
            "nodos_direcciones": nodo,
            "blockchain": [
                b.toDict() for b in blockchain.bloques if b.hash is not None
            ],
            "nodos_red": nodo_enviados,
        }
        # Enviar JSON al nodo para registrar y actualizar blockchain

        response = requests.post(
            nodo + "/nodos/registro_simple",
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
        )
        if response.status_code != 200:
            all_correct = False

    if all_correct:
        response = {
            "mensaje": "Se han incluido nuevos nodos en la red",
            "nodos_totales": nodos_red,
        }
    else:
        response = {
            "mensaje": "Error notificando el nodo estipulado",
        }

    mutex_1.release()

    return jsonify(response), 201


# Ruta para registrar nodo y actualizar blockchain
@app.route("/nodos/registro_simple", methods=["POST"])
def registrar_nodo_actualiza_blockchain():
    """
    Endpoint para que un nodo registre y actualice su blockchain en la red.
    :return: Una respuesta JSON con información sobre el resultado del registro y actualización.
    """
    mutex_2.acquire()
    global blockchain
    global nodos_red

    blockchain_leida = Blockchain.Blockchain()

    read_json = request.get_json()
    lista_nodos = read_json.get("nodos_red")
    for nodo in lista_nodos:
        if nodo not in nodos_red:
            nodos_red.append(nodo)
    block_data = read_json.get("blockchain", [])
    for block in block_data:
        bloque_leido = Blockchain.Bloque(
            block["indice"],
            block["transacciones"],
            block["timestamp"],
            block["hash_previo"],
            block["hash"],
            block["prueba"],
        )
        hash_leido = block["hash"]
        hash_calculado = bloque_leido.calcular_hash()
        if hash_leido == hash_calculado:
            if block["indice"] == 1:
                blockchain_leida.bloques[0].indice = block["indice"]
                blockchain_leida.bloques[0].transacciones = block["transacciones"]
                blockchain_leida.bloques[0].timestamp = block["timestamp"]
                blockchain_leida.bloques[0].hash_previo = block["hash_previo"]
                blockchain_leida.bloques[0].hash = block["hash"]
                blockchain_leida.bloques[0].prueba = block["prueba"]
            else:
                blockchain_leida.nuevo_bloque2(
                    block["indice"],
                    block["transacciones"],
                    block["timestamp"],
                    block["hash_previo"],
                    block["hash"],
                    block["prueba"],
                )

    mutex_2.release()

    if blockchain_leida is None:
        return jsonify("El blockchain de la red está corrupto"), 400
    else:
        blockchain = blockchain_leida
        return (
            jsonify(
                "La blockchain del nodo"
                + str(mi_ip)
                + ":"
                + str(puerto)
                + " ha sido correctamente actualizada"
            ),
            200,
        )


# Función para resolver conflictos y establecer consenso
def resuelve_conflictos():
    """
    Mecanismo para establecer el consenso y resolver los conflictos
    """
    global blockchain
    global nodos_red
    conflicto = False
    longitud_actual = len(blockchain.bloques)
    for nodo in nodos_red:
        response = requests.get(str(nodo) + "/chain")
        longitud_cadena = response.json()["longitud"]
        if longitud_cadena > longitud_actual:
            conflicto = True

    if conflicto == True:
        return True  # Hay conflicto
    else:
        return False  # No ha habido conflicto


# Lista de respuestas a los pings
respuestas_nodos = []


# Ruta para realizar ping a los nodos
@app.route("/ping", methods=["GET"])
def ping():
    """
    Endpoint para enviar solicitudes de ping a nodos en la red y obtener respuestas.
    :return: Una respuesta JSON con información sobre los pings y las respuestas de los nodos en la red.
    """
    mutex_1.acquire()
    global nodos_red

    nodo_origen = "http://" + mi_ip_local + ":" + mi_puerto
    respuesta_final = ""
    respuestas = 0

    for nodo in nodos_red:
        data = {"nodos": nodo_origen, "mensaje": "PING ", "hora": time.time()}

        response = requests.post(
            nodo + "/pong",
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
        )

        read_json = response.json()
        nodes_destino = read_json.get("ip_puerto_destino")
        retardo = read_json.get("Retardo")
        respuesta_final += f"#PING de {nodes_destino[7:]}. Respuesta: PONG {nodo[7:]}. Retardo {retardo}. "
        if response.status_code == 200:
            respuestas += 1

    if respuestas == len(nodos_red):
        respuesta_final += " Todos los nodos responden"
    else:
        respuesta_final += " Algún nodo no responde"

    mutex_1.release()

    return jsonify({"respuesta_final": respuesta_final})


# Ruta para recibir respuesta al ping (PONG)
@app.route("/pong", methods=["POST"])
def pong():
    """
    Endpoint para recibir solicitudes de ping, calcular el retardo y enviar respuestas de pong.
    :return: Una respuesta JSON con información sobre el nodo de destino y el retardo.
    """
    mutex_2.acquire()

    read_json = request.get_json()
    nodes_destino = read_json.get("nodos")
    time_leido = read_json.get("hora")
    retardo = time.time() - time_leido

    mutex_2.release()

    return jsonify({"ip_puerto_destino": nodes_destino, "Retardo": retardo})


# Función para realizar copia de seguridad de la cadena de bloques
def copia_seguridad():
    """
    Realiza copias de seguridad de la cadena de bloques en un archivo JSON con un nombre específico.
    El contenido del archivo incluirá la cadena de bloques, su longitud y la fecha actual.
    :return: None
    """
    global blockchain

    while True:
        mutex_1.acquire()
        mutex_2.acquire()
        # Crear una copia de seguridad de la cadena de bloques
        data = {
            "chain": [b.toDict() for b in blockchain.bloques if b.hash is not None],
            "longitud": len(blockchain.bloques),
            "date": time.strftime("%d/%m/%Y %H:%M:%S"),
        }

        # Obtener la dirección IP y el puerto del nodo (sustituir con los valores reales)
        ip_nodo = "192.168.1.1"
        puerto_nodo = 5000

        # Crear el nombre del archivo de copia de seguridad
        nombre_archivo = f"respaldo-nodo{ip_nodo}-{puerto_nodo}.json"

        # Escribir la copia de seguridad en el archivo
        with open(nombre_archivo, "a") as archivo:
            json.dump(data, archivo, indent=2)
            archivo.write("\n")

        print(f"Copia de seguridad creada en {nombre_archivo}")

        mutex_2.release()
        mutex_1.release()

        # Dormir durante 60 segundos antes de la próxima copia de seguridad
        time.sleep(60)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-p", "--puerto", default=5000, type=int, help="puerto para escuchar"
    )
    args = parser.parse_args()
    puerto = args.puerto

    # Iniciar hilo para la copia de seguridad
    h = Thread(target=copia_seguridad)
    h.start()

    # Iniciar la aplicación Flask
    app.run(host="0.0.0.0", port=puerto)
    h.join()
