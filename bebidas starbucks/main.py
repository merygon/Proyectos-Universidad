import funciones as f
import objetos as o
import excepciones as e

import tkinter as tk

#para meter la info en un fichero e imprimirlo
# try:
#     Bevrage = o.Bebida()
#     #print(f'*** ' '\n' f' {Bevrage.__str__()} ' '\n' ' ***')
#     with open("clientes.txt","w") as clientes:
#         linea = Bevrage.__str__()
#         #clientes.write(f'*** ' '\n' f' {linea} ' '\n' ' ***')
#         for k,v in linea.items():
#             clientes.write(f'{k} : {v}')
#             clientes.write("\n")
#     try:
#         with open("clientes.txt","r") as fich:
#             for linea in fich:
#                 print(linea)
#     except FileNotFoundError as error:
#         print("Este fichero no existe.s")
# except e.BebidaError as error: 
#     print("Bebida incorrecta.")
# except e.NombreError as error:
#     print("Nombre incorrecto.")

# interfaz_datos = f.cargar_datos()
# interfaz_datos

if __name__ == "__main__":
    
    print("""
          
          Menú:
            1. Crear cliente
            2. Salir
        
        """)
    
    opcion = int(input("Introduce la operación que deseas realizar: "))
    
    if opcion == 1:
        
        try:
            Bevrage = o.Bebida()
            #print(f'*** ' '\n' f' {Bevrage.__str__()} ' '\n' ' ***')
            with open("clientes.txt","w") as clientes:
                linea = Bevrage.__str__()
                #clientes.write(f'*** ' '\n' f' {linea} ' '\n' ' ***')
                for k,v in linea.items():
                    clientes.write(f'{k} : {v}')
                    clientes.write("\n")
            try:
                def extraccion_datos() -> dict:
                    with open("clientes.txt","r") as fich:
                        datos = fich.read()
                    return datos
                
                ventana = tk.Tk()
                ventana.title('Pedido de Bebidas')

                etiqueta = tk.Label(ventana, text = "Saludos cliente.")
                etiqueta.pack(pady = 10)

                def saludar():
                    datos = extraccion_datos()
                    etiqueta.config(text = f"Tus datos son: " "\n" f"{datos}")
                    
                boton_saludo = tk.Button(ventana, text = "Ver Datos", command = saludar)
                boton_saludo.pack()

                ventana.mainloop()

            except FileNotFoundError as error:
                print("Este fichero no existe.s")
        except e.BebidaError as error: 
            print("Bebida incorrecta.")
        except e.NombreError as error:
            print("Nombre incorrecto.")
            
    else:
        print("Gracias por utilizar nuestros servicios.")
