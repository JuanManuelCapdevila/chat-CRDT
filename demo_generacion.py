#!/usr/bin/env python3
"""
Demostración del generador automático de crucigramas
"""

import time
from generador_crucigramas import GeneradorCrucigramas, DiccionarioPalabras
from crucigrama_crdt import CrucigramaCRDT


def mostrar_crucigrama_simple(crucigrama: CrucigramaCRDT, titulo: str = ""):
    """Muestra un crucigrama de forma simple en consola"""
    if titulo:
        print(f"\n=== {titulo} ===")
    
    print(f"Palabras: {len(crucigrama.palabras)}")
    print(f"Tamaño: {crucigrama.filas}x{crucigrama.columnas}")
    print()
    
    # Mostrar grid
    print("   ", end="")
    for col in range(min(12, crucigrama.columnas)):
        print(f"{col:2}", end=" ")
    print()
    
    for fila in range(min(12, crucigrama.filas)):
        print(f"{fila:2} ", end="")
        
        for columna in range(min(12, crucigrama.columnas)):
            celda = crucigrama.obtener_celda(fila, columna)
            
            if celda and celda.es_negra:
                print("██", end=" ")
            elif celda and celda.letra:
                if celda.numero:
                    # Mostrar número + letra
                    print(f"{celda.numero}{celda.letra}"[:2], end=" ")
                else:
                    print(f" {celda.letra}", end=" ")
            elif celda and celda.numero:
                print(f"{celda.numero} ", end=" ")
            else:
                print("· ", end=" ")
        print()
    
    # Mostrar palabras
    print("\nPalabras:")
    for numero, palabra in sorted(crucigrama.palabras.items()):
        direccion_symbol = "→" if palabra.direccion == "horizontal" else "↓"
        print(f"{numero:2}. {direccion_symbol} {palabra.respuesta:12} - {palabra.pista}")


def demo_generacion_basica():
    """Demo de generación básica de crucigramas"""
    print("=== Demo: Generación Básica de Crucigramas ===")
    
    generador = GeneradorCrucigramas()
    
    # Generar crucigrama básico
    print("1. Generando crucigrama básico...")
    crucigrama_basico = generador.generar_crucigrama_basico(10, 10, 6)
    mostrar_crucigrama_simple(crucigrama_basico, "Crucigrama Básico")
    
    input("\nPresiona Enter para continuar...")
    
    # Generar crucigrama fácil
    print("\n2. Generando crucigrama fácil...")
    crucigrama_facil = generador.generar_plantilla_facil()
    mostrar_crucigrama_simple(crucigrama_facil, "Crucigrama Fácil")
    
    input("\nPresiona Enter para continuar...")
    
    # Generar crucigrama difícil
    print("\n3. Generando crucigrama difícil...")
    crucigrama_dificil = generador.generar_plantilla_dificil()
    mostrar_crucigrama_simple(crucigrama_dificil, "Crucigrama Difícil")


def demo_crucigramas_tematicos():
    """Demo de crucigramas temáticos por categoría"""
    print("\n=== Demo: Crucigramas Temáticos ===")
    
    generador = GeneradorCrucigramas()
    
    temas = ["tecnologia", "ciencia", "geografia", "historia"]
    
    for tema in temas:
        print(f"\nGenerando crucigrama de {tema.upper()}...")
        crucigrama_tematico = generador.generar_crucigrama_tematico(tema, 12, 12)
        mostrar_crucigrama_simple(crucigrama_tematico, f"Crucigrama de {tema.capitalize()}")
        
        input(f"\nPresiona Enter para ver el siguiente tema...")


def demo_diccionario():
    """Demo del sistema de diccionario de palabras"""
    print("\n=== Demo: Sistema de Diccionario ===")
    
    diccionario = DiccionarioPalabras()
    
    # Mostrar estadísticas del diccionario
    print("Estadísticas del diccionario:")
    total_palabras = 0
    for categoria, palabras in diccionario.palabras.items():
        cantidad = len(palabras)
        total_palabras += cantidad
        print(f"  {categoria:12}: {cantidad:3} palabras")
    
    print(f"  {'TOTAL':12}: {total_palabras:3} palabras")
    
    # Mostrar ejemplos por categoría
    print("\nEjemplos por categoría:")
    for categoria in ["tecnologia", "ciencia", "geografia"]:
        palabras = diccionario.obtener_palabras_por_categoria(categoria)
        print(f"\n{categoria.upper()}:")
        for i, palabra_pista in enumerate(palabras[:3]):  # Solo primeras 3
            print(f"  {palabra_pista.palabra:10} - {palabra_pista.pista}")
        if len(palabras) > 3:
            print(f"  ... y {len(palabras) - 3} más")
    
    # Demo de búsquedas específicas
    print("\n" + "="*50)
    print("Búsquedas específicas:")
    
    # Palabras de 5 letras
    palabras_5 = diccionario.obtener_palabras_por_longitud(5)
    print(f"\nPalabras de 5 letras ({len(palabras_5)} encontradas):")
    for palabra_pista in palabras_5[:5]:  # Mostrar solo 5
        print(f"  {palabra_pista.palabra} - {palabra_pista.pista}")
    
    # Palabras aleatorias
    palabras_aleatorias = diccionario.obtener_palabras_aleatorias(5)
    print(f"\n5 palabras aleatorias:")
    for palabra_pista in palabras_aleatorias:
        print(f"  {palabra_pista.palabra:10} ({palabra_pista.categoria}) - {palabra_pista.pista}")


def demo_algoritmo_colocacion():
    """Demo del algoritmo de colocación de palabras"""
    print("\n=== Demo: Algoritmo de Colocación ===")
    
    generador = GeneradorCrucigramas()
    crucigrama = CrucigramaCRDT(8, 8, "demo")
    
    print("Creando crucigrama paso a paso:")
    
    # Paso 1: Palabra inicial
    print("\nPaso 1: Colocando palabra inicial 'PYTHON' horizontalmente")
    crucigrama.agregar_palabra(
        "Lenguaje de programación", "PYTHON", 3, 1, "horizontal", "demo"
    )
    mostrar_crucigrama_simple(crucigrama, "Después del paso 1")
    input("Presiona Enter para continuar...")
    
    # Paso 2: Palabra que cruza
    print("\nPaso 2: Colocando 'HTML' verticalmente cruzando con 'PYTHON'")
    # HTML debe cruzar con la 'H' de PYTHON (posición 3,4)
    crucigrama.agregar_palabra(
        "Lenguaje de marcado", "HTML", 1, 4, "vertical", "demo"
    )
    mostrar_crucigrama_simple(crucigrama, "Después del paso 2")
    input("Presiona Enter para continuar...")
    
    # Paso 3: Otra palabra
    print("\nPaso 3: Colocando 'JAVA' horizontalmente")
    crucigrama.agregar_palabra(
        "Otro lenguaje de programación", "JAVA", 6, 2, "horizontal", "demo"
    )
    mostrar_crucigrama_simple(crucigrama, "Después del paso 3")
    
    print("\n¡Crucigrama completado manualmente!")


def demo_guardado_carga():
    """Demo de guardado y carga de crucigramas"""
    print("\n=== Demo: Guardado y Carga ===")
    
    generador = GeneradorCrucigramas()
    
    # Generar crucigrama
    print("1. Generando crucigrama de tecnología...")
    crucigrama_original = generador.generar_crucigrama_tematico("tecnologia", 10, 10)
    mostrar_crucigrama_simple(crucigrama_original, "Crucigrama Original")
    
    # Guardar
    archivo = "crucigrama_demo.json"
    print(f"\n2. Guardando en '{archivo}'...")
    try:
        generador.guardar_crucigrama_json(crucigrama_original, archivo)
        print("✓ Guardado exitoso")
    except Exception as e:
        print(f"✗ Error guardando: {e}")
        return
    
    input("Presiona Enter para cargar el archivo...")
    
    # Cargar
    print(f"\n3. Cargando desde '{archivo}'...")
    try:
        crucigrama_cargado = generador.cargar_crucigrama_json(archivo, "cargado")
        print("✓ Carga exitosa")
        mostrar_crucigrama_simple(crucigrama_cargado, "Crucigrama Cargado")
        
        # Verificar que son iguales
        if len(crucigrama_original.palabras) == len(crucigrama_cargado.palabras):
            print("✓ Los crucigramas coinciden")
        else:
            print("✗ Los crucigramas no coinciden")
            
    except Exception as e:
        print(f"✗ Error cargando: {e}")


def demo_interactivo():
    """Demo interactivo donde el usuario puede personalizar"""
    print("\n=== Demo Interactivo ===")
    print("Personaliza tu crucigrama:")
    
    generador = GeneradorCrucigramas()
    diccionario = generador.diccionario
    
    # Seleccionar categoría
    categorias = list(diccionario.palabras.keys()) + ["mixto"]
    print("\nCategorías disponibles:")
    for i, cat in enumerate(categorias):
        print(f"{i+1}. {cat.capitalize()}")
    
    try:
        opcion_cat = int(input("\nSelecciona categoría (número): ")) - 1
        categoria = categorias[opcion_cat] if 0 <= opcion_cat < len(categorias) else "mixto"
    except:
        categoria = "mixto"
    
    # Seleccionar número de palabras
    try:
        num_palabras = int(input("Número de palabras (3-15): "))
        num_palabras = max(3, min(15, num_palabras))
    except:
        num_palabras = 8
    
    # Generar
    print(f"\nGenerando crucigrama de {categoria} con {num_palabras} palabras...")
    
    if categoria == "mixto":
        crucigrama = generador.generar_crucigrama_basico(
            filas=12, columnas=12, num_palabras=num_palabras
        )
    else:
        crucigrama = generador.generar_crucigrama_tematico(categoria, 12, 12)
    
    mostrar_crucigrama_simple(crucigrama, f"Tu Crucigrama Personalizado ({categoria})")
    
    # Opción de guardar
    guardar = input("\n¿Guardar este crucigrama? (s/n): ").lower().startswith('s')
    if guardar:
        archivo = f"mi_crucigrama_{categoria}_{int(time.time())}.json"
        try:
            generador.guardar_crucigrama_json(crucigrama, archivo)
            print(f"✓ Guardado como '{archivo}'")
        except Exception as e:
            print(f"✗ Error guardando: {e}")


def main():
    """Función principal con menú de demos"""
    print("=== Demos de Generación Automática de Crucigramas ===")
    
    demos = [
        ("Generación básica", demo_generacion_basica),
        ("Crucigramas temáticos", demo_crucigramas_tematicos),
        ("Sistema de diccionario", demo_diccionario),
        ("Algoritmo de colocación", demo_algoritmo_colocacion),
        ("Guardado y carga", demo_guardado_carga),
        ("Demo interactivo", demo_interactivo),
        ("Ejecutar todos", None)
    ]
    
    print("\nSelecciona el demo a ejecutar:")
    for i, (nombre, _) in enumerate(demos):
        print(f"{i+1}. {nombre}")
    
    try:
        opcion = int(input(f"\nOpción (1-{len(demos)}): ")) - 1
        
        if 0 <= opcion < len(demos):
            if opcion == len(demos) - 1:  # Ejecutar todos
                for nombre, demo_func in demos[:-1]:
                    if demo_func:
                        print(f"\n{'='*60}")
                        print(f"Ejecutando: {nombre}")
                        print('='*60)
                        demo_func()
                        input("\nPresiona Enter para continuar con el siguiente demo...")
            else:
                nombre, demo_func = demos[opcion]
                if demo_func:
                    demo_func()
                else:
                    print("Demo no disponible")
        else:
            print("Opción no válida")
    
    except KeyboardInterrupt:
        print("\nDemo cancelado por el usuario")
    except Exception as e:
        print(f"Error ejecutando demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()