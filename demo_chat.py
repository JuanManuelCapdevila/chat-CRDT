#!/usr/bin/env python3
"""
Demostración del chat cooperativo con CRDTs
"""

import time
import threading
from chat_crdt import ChatCRDT
from sincronizacion_chat import ClienteP2PChat


def demo_chat_basico():
    """Demuestra las funcionalidades básicas del chat"""
    print("=== DEMO: Chat Básico ===\n")
    
    # Crear chat
    chat = ChatCRDT("demo_usuario")
    
    # Enviar algunos mensajes
    print("💬 Enviando mensajes...")
    chat.enviar_mensaje("¡Hola! Este es mi primer mensaje en el chat CRDT.")
    chat.enviar_mensaje("Los CRDTs permiten chat colaborativo sin conflictos.")
    chat.enviar_mensaje("¿Alguien más está conectado?")
    
    # Crear canal nuevo
    print("📺 Creando canal...")
    chat.crear_canal("tecnologia")
    chat.enviar_mensaje("Este es un canal específico para hablar de tech.", "tecnologia")
    
    print(f"✅ Chat creado con {len(chat.mensajes)} mensajes\n")
    
    # Mostrar mensajes del canal general
    print("📄 Mensajes del canal #general:")
    mensajes_general = chat.obtener_mensajes_canal("general")
    for i, mensaje in enumerate(mensajes_general, 1):
        fecha = mensaje.timestamp.strftime("%H:%M:%S")
        print(f"{i}. [{fecha}] {mensaje.autor}: {mensaje.contenido}")
    print()
    
    # Mostrar mensajes del canal tecnología
    print("📄 Mensajes del canal #tecnologia:")
    mensajes_tech = chat.obtener_mensajes_canal("tecnologia")
    for i, mensaje in enumerate(mensajes_tech, 1):
        fecha = mensaje.timestamp.strftime("%H:%M:%S")
        print(f"{i}. [{fecha}] {mensaje.autor}: {mensaje.contenido}")
    print()
    
    # Mostrar estadísticas
    stats = chat.obtener_estadisticas()
    print("📊 Estadísticas del chat:")
    print(f"   Mensajes totales: {stats['total_mensajes']}")
    print(f"   Mensajes hoy: {stats['mensajes_hoy']}")
    print(f"   Canales activos: {stats['canales_activos']}")
    print(f"   Usuarios activos: {stats['usuarios_activos']}")
    print()
    
    return chat


def demo_colaboracion():
    """Demuestra la colaboración entre múltiples usuarios"""
    print("=== DEMO: Colaboración Multi-usuario ===\n")
    
    # Crear múltiples chats (simulando usuarios diferentes)
    print("👥 Creando usuarios...")
    chat_alice = ChatCRDT("alice")
    chat_bob = ChatCRDT("bob")
    chat_charlie = ChatCRDT("charlie")
    
    chats = [chat_alice, chat_bob, chat_charlie]
    nombres = ["Alice", "Bob", "Charlie"]
    
    # Alice inicia la conversación
    print("💬 Alice inicia la conversación...")
    mensaje_id = chat_alice.enviar_mensaje("¡Hola a todos! ¿Cómo están?")
    
    # Sincronizar el mensaje de Alice con otros usuarios
    print("🔄 Sincronizando con otros usuarios...")
    operaciones_alice = chat_alice.obtener_operaciones()
    
    for operacion in operaciones_alice:
        chat_bob.aplicar_operacion_remota(operacion)
        chat_charlie.aplicar_operacion_remota(operacion)
    
    print("✅ Mensaje de Alice sincronizado")
    
    # Bob responde
    print("💬 Bob responde...")
    chat_bob.enviar_mensaje("¡Hola Alice! Todo bien por aquí 👋")
    
    # Charlie también responde
    print("💬 Charlie responde...")
    chat_charlie.enviar_mensaje("¡Buenas! Trabajando en el proyecto CRDT 🚀")
    
    # Sincronizar todas las respuestas
    print("🔄 Sincronizando todas las respuestas...")
    
    # Obtener operaciones de Bob y aplicarlas
    operaciones_bob = chat_bob.obtener_operaciones()
    for operacion in operaciones_bob:
        if operacion.usuario == "bob":  # Solo nuevas operaciones
            chat_alice.aplicar_operacion_remota(operacion)
            chat_charlie.aplicar_operacion_remota(operacion)
    
    # Obtener operaciones de Charlie y aplicarlas
    operaciones_charlie = chat_charlie.obtener_operaciones()
    for operacion in operaciones_charlie:
        if operacion.usuario == "charlie":  # Solo nuevas operaciones
            chat_alice.aplicar_operacion_remota(operacion)
            chat_bob.aplicar_operacion_remota(operacion)
    
    # Mostrar conversación final desde la perspectiva de Alice
    print("📊 Conversación final (desde perspectiva de Alice):")
    mensajes = chat_alice.obtener_mensajes_canal("general")
    for i, mensaje in enumerate(mensajes, 1):
        fecha = mensaje.timestamp.strftime("%H:%M:%S")
        print(f"{i}. [{fecha}] {mensaje.autor}: {mensaje.contenido}")
    print()
    
    # Verificar convergencia
    print("🔍 Verificando convergencia...")
    todos_convergieron = True
    
    for i, (chat, nombre) in enumerate(zip(chats, nombres)):
        stats = chat.obtener_estadisticas()
        print(f"   {nombre}: {stats['total_mensajes']} mensajes")
        
        if stats['total_mensajes'] != 3:  # Deberían ser 3 mensajes
            todos_convergieron = False
    
    if todos_convergieron:
        print("✅ ¡Todos los nodos han convergido correctamente!")
    else:
        print("❌ Algunos nodos no han convergido")
    
    print()
    return chats


def demo_edicion_mensajes():
    """Demuestra la edición y eliminación de mensajes"""
    print("=== DEMO: Edición y Eliminación ===\n")
    
    # Crear chat
    chat = ChatCRDT("editor_usuario")
    
    # Enviar mensaje original
    print("💬 Enviando mensaje original...")
    mensaje_id = chat.enviar_mensaje("Este mensaje tiene un eror.")
    
    # Editar mensaje
    print("✏️ Editando mensaje...")
    chat.editar_mensaje(mensaje_id, "Este mensaje tiene un error corregido.")
    
    # Enviar otro mensaje
    mensaje2_id = chat.enviar_mensaje("Este mensaje será eliminado.")
    
    # Eliminar segundo mensaje
    print("🗑️ Eliminando mensaje...")
    chat.eliminar_mensaje(mensaje2_id)
    
    # Mostrar estado final
    print("📄 Estado final de los mensajes:")
    mensajes = chat.obtener_mensajes_canal("general")
    for i, mensaje in enumerate(mensajes, 1):
        fecha = mensaje.timestamp.strftime("%H:%M:%S")
        print(f"{i}. [{fecha}] {mensaje.autor}: {mensaje.contenido}")
    print()


def demo_busqueda():
    """Demuestra la funcionalidad de búsqueda"""
    print("=== DEMO: Búsqueda de Mensajes ===\n")
    
    # Crear chat con varios mensajes
    chat = ChatCRDT("buscador")
    
    print("💬 Creando mensajes para búsqueda...")
    chat.enviar_mensaje("Los CRDTs son estructuras de datos increíbles")
    chat.enviar_mensaje("Python es genial para implementar sistemas distribuidos")
    chat.enviar_mensaje("¿Alguien sabe más sobre algoritmos CRDT?")
    chat.enviar_mensaje("El chat está funcionando perfectamente")
    chat.enviar_mensaje("CRDTs + Python = ❤️")
    
    # Buscar mensajes con "CRDT"
    print("🔍 Buscando mensajes con 'CRDT':")
    resultados = chat.buscar_mensajes("CRDT")
    for i, mensaje in enumerate(resultados, 1):
        fecha = mensaje.timestamp.strftime("%H:%M:%S")
        print(f"{i}. [{fecha}] {mensaje.autor}: {mensaje.contenido}")
    print()
    
    # Buscar mensajes con "Python"
    print("🔍 Buscando mensajes con 'Python':")
    resultados = chat.buscar_mensajes("Python")
    for i, mensaje in enumerate(resultados, 1):
        fecha = mensaje.timestamp.strftime("%H:%M:%S")
        print(f"{i}. [{fecha}] {mensaje.autor}: {mensaje.contenido}")
    print()


def demo_multiples_canales():
    """Demuestra el uso de múltiples canales"""
    print("=== DEMO: Múltiples Canales ===\n")
    
    # Crear chat
    chat = ChatCRDT("admin_canales")
    
    # Crear varios canales
    print("📺 Creando canales...")
    canales = ["tecnologia", "random", "proyectos", "ayuda"]
    
    for canal in canales:
        chat.crear_canal(canal)
        print(f"   ✅ Canal #{canal} creado")
    
    # Enviar mensajes a diferentes canales
    print("\n💬 Enviando mensajes a diferentes canales...")
    
    chat.enviar_mensaje("Bienvenidos al canal general", "general")
    chat.enviar_mensaje("Hablemos de Python y CRDTs aquí", "tecnologia")
    chat.enviar_mensaje("¿Alguien para charlar?", "random")
    chat.enviar_mensaje("Nuevo proyecto: Chat CRDT", "proyectos")
    chat.enviar_mensaje("¿Cómo uso este chat?", "ayuda")
    chat.enviar_mensaje("Respuesta: Es muy fácil!", "ayuda")
    
    # Mostrar mensajes por canal
    print("\n📊 Resumen por canal:")
    for canal in chat.canales.keys():
        mensajes = chat.obtener_mensajes_canal(canal)
        print(f"\n📺 Canal #{canal} ({len(mensajes)} mensajes):")
        for mensaje in mensajes:
            fecha = mensaje.timestamp.strftime("%H:%M:%S")
            print(f"   [{fecha}] {mensaje.autor}: {mensaje.contenido}")


def demo_p2p():
    """Demuestra la sincronización P2P (simulada)"""
    print("=== DEMO: Sincronización P2P ===\n")
    
    # Crear clientes P2P
    print("🌐 Creando clientes P2P...")
    cliente1 = ClienteP2PChat(
        ChatCRDT("usuario1"),
        nombre_usuario="Usuario 1",
        habilitar_autodescubrimiento=False
    )
    
    cliente2 = ClienteP2PChat(
        ChatCRDT("usuario2"),
        nombre_usuario="Usuario 2",
        habilitar_autodescubrimiento=False
    )
    
    # Iniciar clientes
    print("🚀 Iniciando clientes...")
    cliente1.iniciar()
    cliente2.iniciar()
    
    time.sleep(1)  # Dar tiempo para inicializar
    
    # Usuario 1 envía mensaje
    print("💬 Usuario 1 envía mensaje...")
    cliente1.chat.enviar_mensaje("¡Hola desde Usuario 1! 👋")
    
    # Usuario 2 también envía mensaje
    print("💬 Usuario 2 envía mensaje...")
    cliente2.chat.enviar_mensaje("¡Saludos desde Usuario 2! 🚀")
    
    # Simular sincronización manual
    print("🔄 Simulando sincronización...")
    
    # Obtener operaciones del cliente 1 y aplicar en cliente 2
    operaciones1 = cliente1.chat.obtener_operaciones()
    for op in operaciones1:
        if op.usuario == "usuario1":
            cliente2.chat.aplicar_operacion_remota(op)
    
    # Obtener operaciones del cliente 2 y aplicar en cliente 1
    operaciones2 = cliente2.chat.obtener_operaciones()
    for op in operaciones2:
        if op.usuario == "usuario2":
            cliente1.chat.aplicar_operacion_remota(op)
    
    print("✅ Sincronización completada")
    
    # Verificar estado
    print("📊 Estado de los chats:")
    print(f"   Cliente 1: {len(cliente1.chat.mensajes)} mensajes")
    print(f"   Cliente 2: {len(cliente2.chat.mensajes)} mensajes")
    
    # Mostrar mensajes desde perspectiva del cliente 1
    print("\n💬 Conversación (desde Cliente 1):")
    mensajes = cliente1.chat.obtener_mensajes_canal("general")
    for i, mensaje in enumerate(mensajes, 1):
        fecha = mensaje.timestamp.strftime("%H:%M:%S")
        print(f"{i}. [{fecha}] {mensaje.autor}: {mensaje.contenido}")
    
    if len(cliente1.chat.mensajes) == len(cliente2.chat.mensajes):
        print("\n✅ ¡Sincronización P2P exitosa!")
    else:
        print("\n❌ Sincronización P2P falló")
    
    # Detener clientes
    print("\n🛑 Deteniendo clientes...")
    cliente1.detener()
    cliente2.detener()
    
    print()


def main():
    """Ejecuta todas las demostraciones"""
    print("🎉 DEMOSTRACIONES DEL CHAT COOPERATIVO CRDT 🎉\n")
    
    try:
        # Demo básico
        chat = demo_chat_basico()
        
        input("Presiona Enter para continuar con la demo de colaboración...")
        
        # Demo colaboración
        chats = demo_colaboracion()
        
        input("Presiona Enter para continuar con la demo de edición...")
        
        # Demo edición
        demo_edicion_mensajes()
        
        input("Presiona Enter para continuar con la demo de búsqueda...")
        
        # Demo búsqueda
        demo_busqueda()
        
        input("Presiona Enter para continuar con la demo de canales...")
        
        # Demo canales múltiples
        demo_multiples_canales()
        
        input("Presiona Enter para continuar con la demo P2P...")
        
        # Demo P2P
        demo_p2p()
        
        print("🎊 ¡Todas las demostraciones completadas!")
        print("\nPara usar la interfaz gráfica, ejecuta:")
        print("   python main_chat.py")
        
    except KeyboardInterrupt:
        print("\n⏹️ Demostraciones interrumpidas por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante las demostraciones: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()