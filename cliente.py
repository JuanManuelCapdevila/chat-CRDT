"""
Cliente con interfaz de línea de comandos para el crucigrama cooperativo
"""

import os
import sys
from typing import Optional
from crucigrama_crdt import CrucigramaCRDT, Celda
from sincronizacion import ClienteP2P


class Cliente:
    """Interfaz de cliente para interactuar con el crucigrama"""
    
    def __init__(self, nombre_usuario: str, crucigrama: CrucigramaCRDT):
        self.nombre_usuario = nombre_usuario
        self.crucigrama = crucigrama
        self.cliente_p2p = ClienteP2P(crucigrama)
        
    def mostrar_menu(self):
        """Muestra el menú principal"""
        while True:
            self.limpiar_pantalla()
            print(f"=== Crucigrama Cooperativo - Usuario: {self.nombre_usuario} ===")
            print(f"Node ID: {self.crucigrama.node_id}")
            print()
            
            self.mostrar_crucigrama()
            print()
            
            print("Opciones:")
            print("1. Establecer letra")
            print("2. Marcar celda como negra")
            print("3. Agregar palabra con pista")
            print("4. Ver estado completo")
            print("5. Conectar con otro cliente")
            print("6. Ver palabras registradas")
            print("7. Limpiar posición")
            print("8. Salir")
            
            opcion = input("\nSelecciona una opción (1-8): ").strip()
            
            if opcion == '1':
                self.establecer_letra_interfaz()
            elif opcion == '2':
                self.marcar_celda_negra_interfaz()
            elif opcion == '3':
                self.agregar_palabra_interfaz()
            elif opcion == '4':
                self.mostrar_estado_completo()
            elif opcion == '5':
                self.conectar_cliente_interfaz()
            elif opcion == '6':
                self.mostrar_palabras()
            elif opcion == '7':
                self.limpiar_posicion_interfaz()
            elif opcion == '8':
                break
            else:
                input("Opción no válida. Presiona Enter para continuar...")
    
    def mostrar_crucigrama(self, mostrar_detalles: bool = False):
        """Muestra el crucigrama en la consola"""
        print("   ", end="")
        for col in range(self.crucigrama.columnas):
            print(f"{col:2}", end=" ")
        print()
        
        for fila in range(self.crucigrama.filas):
            print(f"{fila:2} ", end="")
            
            for columna in range(self.crucigrama.columnas):
                celda = self.crucigrama.obtener_celda(fila, columna)
                
                if celda and celda.es_negra:
                    print("██", end=" ")
                elif celda and celda.letra:
                    letra_mostrar = celda.letra
                    if celda.numero:
                        print(f"{celda.numero}{letra_mostrar}"[:2], end=" ")
                    else:
                        print(f" {letra_mostrar}", end=" ")
                elif celda and celda.numero:
                    print(f"{celda.numero} ", end=" ")
                else:
                    print("  ", end=" ")
            
            print()
            
            if mostrar_detalles:
                print("   ", end="")
                for columna in range(self.crucigrama.columnas):
                    celda = self.crucigrama.obtener_celda(fila, columna)
                    autor = (celda.autor[:2] if celda and celda.autor else "  ")
                    print(f"{autor}", end=" ")
                print()
    
    def establecer_letra_interfaz(self):
        """Interfaz para establecer una letra"""
        try:
            fila = int(input("Fila: "))
            columna = int(input("Columna: "))
            letra = input("Letra (o Enter para borrar): ").strip()
            
            if letra == "":
                letra = None
            
            if self.crucigrama.establecer_letra(fila, columna, letra, self.nombre_usuario):
                print("Letra establecida correctamente")
                self.cliente_p2p.enviar_cambio_local()
            else:
                print("No se pudo establecer la letra (posición inválida o celda negra)")
                
        except ValueError:
            print("Valores inválidos")
        
        input("Presiona Enter para continuar...")
    
    def marcar_celda_negra_interfaz(self):
        """Interfaz para marcar una celda como negra"""
        try:
            fila = int(input("Fila: "))
            columna = int(input("Columna: "))
            
            if self.crucigrama.establecer_celda_negra(fila, columna, self.nombre_usuario):
                print("Celda marcada como negra")
                self.cliente_p2p.enviar_cambio_local()
            else:
                print("No se pudo marcar la celda (posición inválida)")
                
        except ValueError:
            print("Valores inválidos")
        
        input("Presiona Enter para continuar...")
    
    def limpiar_posicion_interfaz(self):
        """Interfaz para limpiar una posición"""
        try:
            fila = int(input("Fila: "))
            columna = int(input("Columna: "))
            
            if self.crucigrama.establecer_letra(fila, columna, None, self.nombre_usuario):
                print("Posición limpiada")
                self.cliente_p2p.enviar_cambio_local()
            else:
                print("No se pudo limpiar la posición")
                
        except ValueError:
            print("Valores inválidos")
        
        input("Presiona Enter para continuar...")
    
    def agregar_palabra_interfaz(self):
        """Interfaz para agregar una palabra con pista"""
        try:
            pista = input("Pista: ").strip()
            respuesta = input("Respuesta: ").strip()
            fila = int(input("Fila de inicio: "))
            columna = int(input("Columna de inicio: "))
            direccion = input("Dirección (h/v): ").strip().lower()
            
            direccion = 'horizontal' if direccion == 'h' else 'vertical'
            
            numero = self.crucigrama.agregar_palabra(
                pista, respuesta, fila, columna, direccion, self.nombre_usuario
            )
            
            if numero:
                print(f"Palabra agregada con número {numero}")
                self.cliente_p2p.enviar_cambio_local()
            else:
                print("No se pudo agregar la palabra (posición inválida o espacio insuficiente)")
                
        except ValueError:
            print("Valores inválidos")
        
        input("Presiona Enter para continuar...")
    
    def mostrar_palabras(self):
        """Muestra todas las palabras registradas"""
        self.limpiar_pantalla()
        print("=== Palabras Registradas ===")
        print()
        
        if not self.crucigrama.palabras:
            print("No hay palabras registradas")
        else:
            for numero, palabra in sorted(self.crucigrama.palabras.items()):
                print(f"{numero:2}. {palabra.direccion[0].upper()}: {palabra.pista}")
                print(f"    Respuesta: {palabra.respuesta}")
                print(f"    Posición: ({palabra.fila_inicio}, {palabra.columna_inicio})")
                print(f"    Autor: {palabra.autor}")
                print()
        
        input("Presiona Enter para continuar...")
    
    def mostrar_estado_completo(self):
        """Muestra el estado completo con detalles"""
        self.limpiar_pantalla()
        print("=== Estado Completo del Crucigrama ===")
        print()
        self.mostrar_crucigrama(mostrar_detalles=True)
        print()
        
        print("Leyenda:")
        print("██ = Celda negra")
        print("Número en esquina superior = Inicio de palabra")
        print("Letras pequeñas debajo = Autor de cada celda")
        print()
        
        input("Presiona Enter para continuar...")
    
    def conectar_cliente_interfaz(self):
        """Interfaz para conectar con otro cliente (simulación)"""
        print("=== Conexión P2P ===")
        print("En una implementación real, aquí se conectaría con otro cliente")
        print("Por ahora, esto es una demostración local")
        
        # Crear un segundo crucigrama para demostrar sincronización
        otro_crucigrama = CrucigramaCRDT(self.crucigrama.filas, self.crucigrama.columnas)
        otro_cliente = ClienteP2P(otro_crucigrama)
        
        # Conectar los clientes
        self.cliente_p2p.conectar_peer("demo_peer", otro_cliente)
        otro_cliente.conectar_peer(self.crucigrama.node_id, self.cliente_p2p)
        
        print("Conexión simulada establecida con 'demo_peer'")
        input("Presiona Enter para continuar...")
    
    def limpiar_pantalla(self):
        """Limpia la pantalla de la consola"""
        os.system('cls' if os.name == 'nt' else 'clear')