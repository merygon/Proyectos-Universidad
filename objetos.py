import funciones as f
class Bebida:

    def __init__(self) -> None:
        self.nombre = f.nombre()
        self.lugar = f.lugar()
        self.tipo = f.tipo()
        self.tamaño = f.tamaño()
        self.ingredientes = f.ingredientes()
        self.descuento = f.descuentos()
        self.tiempo = f.tiempo()
        
    def __str__(self) -> str:
        cliente = {"Nombre": self.nombre, "Lugar": self.lugar, "Bebida": self.tipo, "Tamaño": self.tamaño, "Ingredientes": self.ingredientes, "Descuento": self.descuento, "Time": self.tiempo}
        #return f"Nombre: {self.nombre}" "\n" f"{self.lugar}" "\n" f"Bebida: {self.tipo}" "\n" f"Tamaño: {self.tamaño}" "\n" f"Ingredientes: {self.ingredientes}" "\n" f"Time: {self.tiempo}"
        return cliente