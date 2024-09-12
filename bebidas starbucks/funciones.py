import excepciones as e
import datetime
import objetos as o
import tkinter as tk

def nombre() -> str:
    nombre = input("Dame tu nombre: ")
    if nombre != nombre.capitalize():
        raise e.NombreError
    else:
        return nombre

def lugar() -> str:
    lugar = input("¿Para tomar aquí o para llevar? (aquí/llevar) ")
    if lugar == "aqui" or "aquí":
        lugar = "Here"
        return lugar
    else:
        lugar = "To Go"
        return lugar

def tipo() -> str:
    bebidas = ["Caramel Machiato","CM","Iced Tea","IT"]
    tipo = input("¿Qué bebidad deseas? ")
    if tipo not in bebidas:
        raise e.BebidaError("Lo sentimos pero esta bebida no figura en nuestra base de datos.")
    else:
        return tipo
    
def tamaño() -> str:
    tamaños = ["venti","grande","small"]
    tamaño = input("¿Qué tamaño? ")
    if tamaño not in tamaños:
        raise e.TamañoError("Lo sentimos pero este tamaño no figura en nuestra base de datos.")
    else:
        return tamaño

def ingredientes() -> str:
    # estos tendrían que venir descargados en funcion de la bebida
    leche = input("¿Qué tipo de leche deseas? ")
    return f'leche {leche}'

def tiempo() -> str:
    # devuelve la hora exacta en la que se ha finalizado el pedido
    tiempo = datetime.datetime.now()
    return tiempo

def precio() -> float:
    try:
        precio = float(input("Introduce el precio: "))
        return precio
    
    except ValueError as error:
        print("Introduce el precio correcto.")
    
def descuentos() -> str: # esta función analiza los puntos que tienes en la app y te dice si tienes un descuento en la bebida o no
                                        # también te dice el número de estrellas que tienes y cuantas te quedan para el siguiente descuento y para subir de nivel
    
    estrellas = int(input("Introduce el número de estrellas que tienes: "))
    price = precio()
    sumar_estrellas = price*100 # cada centimo = + 1 estrella
    num_estrellas = estrellas + sumar_estrellas

    if num_estrellas > 3000:
        descuento = input("Esta bebida puede salirte gratis." "\n" "¿Deseas canjear este descuento? (sí/no) ")
        if descuento == "sí" or "si":
            num_estrellas = num_estrellas - 3000
            return f"Tu nuevo número de estrellas es: {num_estrellas}"
        elif descuento == "no":
            return f"Tu número de estrellas actual es: {num_estrellas}"
        else:
            return "Opcion error."
    else:
        return f"Tu número de estrellas actual es: {num_estrellas}"
    


    
        

