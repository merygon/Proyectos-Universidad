# class NombreError(Exception):
#     pass

# def nombre() -> str:
#     nombre = input("Dame tu nombre: ")
#     if nombre != nombre.capitalize:
#         raise NombreError("Incorrecto")
#     else:
#         nombre
        
# if __name__ == "__main__":
    
#     print("""
#           Menú:
#             1. Dar nombre
#             2. Salir
#             """)
    
#     try:
#         opcion = int(input("Elige la operación que desea realizar: "))
#     except ValueError as error:
#         print("Debes introducir un número entero.")
        
#     if opcion == 1:

#         try:
#             name = nombre()
#             print(name)
#         except NombreError as error:
#             print("La primera letra del nombre debe ser en mayúsucla.")
            
#     else:
#         print("Hasta luego!")

# ahora vamos a crear una interfaz para que quede mucho más bonito y guay ajjajaj

# import tkinter as tk
# import objetos as o
# import excepciones as e
 
n = 3.4
print(round(n))

# ventana = tk.Tk()
# ventana.title('Pedido de Bebidas')

# etiqueta = tk.Label(ventana, text = "Saludos cliente.")
# etiqueta.pack(pady = 10)

# def saludar():
#     etiqueta.config(text = "¿Cómo estás cliente?")
    
# boton_saludo = tk.Button(ventana, text = "Saludar", command = saludar)
# boton_saludo.pack()

# ventana.mainloop()

# ventana = tk.Tk()
# ventana.title('Pedido de Bebidas')

# def obtener_datos_cliente():
#     with open('datos_cliente.txt', 'r') as archivo:
#         datos = archivo.read()
#     return datos

# etiqueta = tk.Label(ventana, text = "Saludos cliente.")
# etiqueta.pack(pady = 10)

# Bevrage = o.Bebida()
# datos = Bevrage.__str__()

# ventana = tk.Tk()
# ventana.title("Datos cliente")

# etiquetas = []
# for k,v in datos.items():
#     texto_etiqueta = f'{k} : {v}'
#     etiquetas.append(tk.Label(ventana, text = texto_etiqueta))
    
# for idx, k in enumerate(etiquetas):
#     k.pack()
    
# ventana.mainloop()
# ventana.destroy()

