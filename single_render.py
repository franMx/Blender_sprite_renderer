#para pillow: "C:\Program Files\Blender Foundation\Blender 4.2\4.2\python\bin\python.exe" -m pip install Pillow, con CMD y permiso admin.
import bpy
import os
import math
from mathutils import Vector

# ============================================
# CONFIGURACIÓN
# ============================================

# Paths
OUTPUT_DIR = "C:/CrowdSprites/"  # Cambia esto
IDLE_FOLDER = OUTPUT_DIR + "idle/"

# Resolución de cada frame
FRAME_WIDTH = 512
FRAME_HEIGHT = 1024

# Configuración de animaciones
IDLE_FRAMES = 24  # 24 frames para animación fluida

# Grid layout
IDLE_GRID = (6, 4)  # 6 columnas x 4 filas = 24 celdas

# Nombres de las acciones/animaciones en Blender
IDLE_ACTION_NAME = "Idle_Sitting"  # ← NOMBRE CORRECTO DE TU ANIMACIÓN

# ============================================
# FUNCIONES AUXILIARES
# ============================================

def setup_camera_for_billboard(obj, distance=5.0):
    """
    Configura la cámara ortográfica mirando al personaje de frente
    """
    # Crea o usa cámara existente
    if "CrowdCamera" in bpy.data.objects:
        cam = bpy.data.objects["CrowdCamera"]
    else:
        cam_data = bpy.data.cameras.new("CrowdCamera")
        cam = bpy.data.objects.new("CrowdCamera", cam_data)
        bpy.context.scene.collection.objects.link(cam)
    
    # Configura como ortográfica
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 2.5  # Ajusta según tamaño del personaje
    
    # Posiciona frente al objeto
    obj_location = obj.location
    cam.location = Vector((obj_location.x, obj_location.y - distance, obj_location.z + 1))
    cam.rotation_euler = (math.radians(90), 0, 0)
    
    # Setea como cámara activa
    bpy.context.scene.camera = cam
    
    return cam

def setup_render_settings(width, height, transparent=True):
    """
    Configura los settings de render
    """
    scene = bpy.context.scene
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    
    # Formato de imagen
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA' if transparent else 'RGB'
    
    # Transparencia
    if transparent:
        scene.render.film_transparent = True
    
    # Engine (Cycles para mejor calidad)
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 128
    
    print(f"✓ Render configurado: {width}x{height}, Cycles {scene.cycles.samples} samples")

def render_animation_sequence(obj, action_name, output_folder, num_frames):
    """
    Renderiza una secuencia de animación frame por frame
    """
    # Crea carpeta si no existe
    os.makedirs(output_folder, exist_ok=True)
    
    # Lista todas las actions disponibles
    print(f"\n📋 Actions disponibles en el archivo:")
    for action in bpy.data.actions:
        print(f"  - '{action.name}' (frames: {action.frame_range[0]:.0f} - {action.frame_range[1]:.0f})")
    
    # Asigna la acción al objeto
    if action_name in bpy.data.actions:
        action = bpy.data.actions[action_name]
        if obj.animation_data is None:
            obj.animation_data_create()
        obj.animation_data.action = action
    else:
        print(f"\n❌ ERROR: Action '{action_name}' no encontrada!")
        print(f"Por favor actualiza IDLE_ACTION_NAME con uno de los nombres de arriba.")
        return
    
    # Calcula frame range
    start_frame = int(action.frame_range[0])
    end_frame = int(action.frame_range[1])
    total_frames_in_action = end_frame - start_frame + 1
    frame_step = max(1, total_frames_in_action // num_frames)
    
    print(f"\n=== Renderizando {action_name} ===")
    print(f"Frames totales en action: {total_frames_in_action} ({start_frame} - {end_frame})")
    print(f"Frames a renderizar: {num_frames}")
    print(f"Step entre frames: {frame_step}")
    
    # Renderiza cada frame
    for i in range(num_frames):
        current_frame = start_frame + (i * frame_step)
        # Asegura no pasar el final
        if current_frame > end_frame:
            current_frame = end_frame
            
        bpy.context.scene.frame_set(current_frame)
        
        output_path = os.path.join(output_folder, f"frame_{i:04d}.png")
        bpy.context.scene.render.filepath = output_path
        
        print(f"  Renderizando frame {i+1}/{num_frames}: frame {current_frame} -> {output_path}")
        bpy.ops.render.render(write_still=True)
    
    print(f"✓ Completado: {num_frames} frames renderizados\n")

def create_spritesheet(input_folder, output_path, grid_cols, grid_rows, frame_width, frame_height):
    """
    Combina frames individuales en un spritesheet usando PIL
    """
    try:
        from PIL import Image
    except ImportError:
        print("⚠️ ERROR: PIL no está instalado.")
        print("Los frames individuales están en:", input_folder)
        print("Puedes combinarlos manualmente o instalar Pillow.")
        return
    
    sheet_width = grid_cols * frame_width
    sheet_height = grid_rows * frame_height
    
    spritesheet = Image.new('RGBA', (sheet_width, sheet_height), (0, 0, 0, 0))
    
    frames = sorted([f for f in os.listdir(input_folder) if f.endswith('.png')])
    
    if not frames:
        print(f"❌ ERROR: No se encontraron frames PNG en {input_folder}")
        return
    
    print(f"Creando spritesheet: {output_path}")
    print(f"  Grid: {grid_cols}x{grid_rows}, Tamaño final: {sheet_width}x{sheet_height}px")
    
    for idx, frame_file in enumerate(frames):
        if idx >= grid_cols * grid_rows:
            break
        
        col = idx % grid_cols
        row = idx // grid_cols
        
        x = col * frame_width
        y = row * frame_height
        
        frame_path = os.path.join(input_folder, frame_file)
        frame_img = Image.open(frame_path)
        frame_img = frame_img.resize((frame_width, frame_height), Image.Resampling.LANCZOS)
        
        spritesheet.paste(frame_img, (x, y))
        print(f"  Frame {idx}: {frame_file} -> posición ({x}, {y})")
    
    spritesheet.save(output_path)
    
    # Verifica tamaño final
    final_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
    print(f"✓ Spritesheet guardado: {final_size:.2f} MB\n")

# ============================================
# SCRIPT PRINCIPAL
# ============================================

def main():
    print("\n" + "="*60)
    print("GENERADOR DE SPRITESHEET PARA CROWD")
    print(f"Configuración: {IDLE_FRAMES} frames, grid {IDLE_GRID[0]}x{IDLE_GRID[1]}")
    print("="*60 + "\n")
    
    # Selecciona el objeto (debe tener armature/rig)
    if not bpy.context.selected_objects:
        print("❌ ERROR: ¡Selecciona un objeto con animaciones en la viewport!")
        print("   Haz click en el armature/rig antes de ejecutar el script.")
        return
    
    obj = bpy.context.active_object
    print(f"✓ Objeto seleccionado: {obj.name}\n")
    
    # Setup cámara
    print("📷 Configurando cámara...")
    setup_camera_for_billboard(obj)
    
    # Setup render
    print("🎨 Configurando render settings...")
    setup_render_settings(FRAME_WIDTH, FRAME_HEIGHT, transparent=True)
    
    # Renderiza IDLE
    render_animation_sequence(
        obj, 
        IDLE_ACTION_NAME, 
        IDLE_FOLDER, 
        IDLE_FRAMES
    )
    
    # Crea spritesheet
    print("="*60)
    print("GENERANDO SPRITESHEET")
    print("="*60 + "\n")
    
    create_spritesheet(
        IDLE_FOLDER,
        OUTPUT_DIR + "idle_spritesheet.png",
        IDLE_GRID[0], IDLE_GRID[1],
        FRAME_WIDTH, FRAME_HEIGHT
    )
    
    print("="*60)
    print("✓ PROCESO COMPLETADO!")
    print("="*60)
    print(f"\n📁 Archivos generados en: {OUTPUT_DIR}")
    print(f"   - Frames individuales: {IDLE_FOLDER}")
    print(f"   - Spritesheet final: {OUTPUT_DIR}idle_spritesheet.png")
    print(f"\n📊 Stats:")
    print(f"   - Frames: {IDLE_FRAMES}")
    print(f"   - Grid: {IDLE_GRID[0]}x{IDLE_GRID[1]} = {IDLE_GRID[0] * IDLE_GRID[1]} celdas")
    print(f"   - Resolución por frame: {FRAME_WIDTH}x{FRAME_HEIGHT}")
    print(f"   - Spritesheet final: {IDLE_GRID[0] * FRAME_WIDTH}x{IDLE_GRID[1] * FRAME_HEIGHT}px")

# Ejecutar
if __name__ == "__main__":
    main()
