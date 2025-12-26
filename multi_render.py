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
CELEBRATION_FOLDER = OUTPUT_DIR + "celebration/"

# Resolución de cada frame
FRAME_WIDTH = 512
FRAME_HEIGHT = 1024

# Configuración de animaciones
IDLE_FRAMES = 8  # 8 frames para idle loop
CELEBRATION_FRAMES = 16  # 16 frames para celebration

# Grid layout
IDLE_GRID = (4, 2)  # 4 columnas x 2 filas
CELEBRATION_GRID = (4, 4)  # 4 columnas x 4 filas

# Nombres de las acciones/animaciones en Blender
IDLE_ACTION_NAME = "Idle_Sitting"
CELEBRATION_ACTION_NAME = "Celebration_StandUp"

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
    
    # Engine (Eevee es más rápido para esto)
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
    scene.eevee.taa_render_samples = 64
    #scene.render.engine = 'CYCLES'
    #scene.cycles.samples = 128

def render_animation_sequence(obj, action_name, output_folder, num_frames):
    """
    Renderiza una secuencia de animación frame por frame
    """
    # Crea carpeta si no existe
    os.makedirs(output_folder, exist_ok=True)
    
    # Asigna la acción al objeto
    if action_name in bpy.data.actions:
        action = bpy.data.actions[action_name]
        if obj.animation_data is None:
            obj.animation_data_create()
        obj.animation_data.action = action
    else:
        print(f"ERROR: Action '{action_name}' no encontrada!")
        return
    
    # Calcula frame range
    start_frame = int(action.frame_range[0])
    end_frame = int(action.frame_range[1])
    frame_step = max(1, (end_frame - start_frame) // (num_frames - 1))
    
    print(f"\n=== Renderizando {action_name} ===")
    print(f"Frames: {start_frame} a {end_frame}, step: {frame_step}")
    
    # Renderiza cada frame
    for i in range(num_frames):
        current_frame = start_frame + (i * frame_step)
        bpy.context.scene.frame_set(current_frame)
        
        output_path = os.path.join(output_folder, f"frame_{i:04d}.png")
        bpy.context.scene.render.filepath = output_path
        
        print(f"  Renderizando frame {i+1}/{num_frames}: {current_frame} -> {output_path}")
        bpy.ops.render.render(write_still=True)
    
    print(f"✓ Completado: {num_frames} frames en {output_folder}\n")

def create_spritesheet(input_folder, output_path, grid_cols, grid_rows, frame_width, frame_height):
    """
    Combina frames individuales en un spritesheet usando PIL
    """
    try:
        from PIL import Image
    except ImportError:
        print("ERROR: PIL no está instalado. Instala con: pip install Pillow")
        return
    
    sheet_width = grid_cols * frame_width
    sheet_height = grid_rows * frame_height
    
    spritesheet = Image.new('RGBA', (sheet_width, sheet_height), (0, 0, 0, 0))
    
    frames = sorted([f for f in os.listdir(input_folder) if f.endswith('.png')])
    
    print(f"Creando spritesheet: {output_path}")
    print(f"  Grid: {grid_cols}x{grid_rows}, Tamaño: {sheet_width}x{sheet_height}")
    
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
        print(f"  Frame {idx}: {frame_file} -> ({x}, {y})")
    
    spritesheet.save(output_path)
    print(f"✓ Spritesheet guardado: {output_path}\n")

# ============================================
# SCRIPT PRINCIPAL
# ============================================

def main():
    print("\n" + "="*60)
    print("GENERADOR DE SPRITESHEETS PARA CROWD")
    print("="*60 + "\n")
    
    # Selecciona el objeto (debe tener armature/rig)
    if not bpy.context.selected_objects:
        print("ERROR: Selecciona un objeto con animaciones!")
        return
    
    obj = bpy.context.active_object
    print(f"Objeto seleccionado: {obj.name}\n")
    
    # Setup cámara
    setup_camera_for_billboard(obj)
    
    # Setup render
    setup_render_settings(FRAME_WIDTH, FRAME_HEIGHT, transparent=True)
    
    # Renderiza IDLE
    render_animation_sequence(
        obj, 
        IDLE_ACTION_NAME, 
        IDLE_FOLDER, 
        IDLE_FRAMES
    )
    
    # Renderiza CELEBRATION
    render_animation_sequence(
        obj, 
        CELEBRATION_ACTION_NAME, 
        CELEBRATION_FOLDER, 
        CELEBRATION_FRAMES
    )
    
    # Crea spritesheets
    print("="*60)
    print("GENERANDO SPRITESHEETS")
    print("="*60 + "\n")
    
    create_spritesheet(
        IDLE_FOLDER,
        OUTPUT_DIR + "idle_spritesheet.png",
        IDLE_GRID[0], IDLE_GRID[1],
        FRAME_WIDTH, FRAME_HEIGHT
    )
    
    create_spritesheet(
        CELEBRATION_FOLDER,
        OUTPUT_DIR + "celebration_spritesheet.png",
        CELEBRATION_GRID[0], CELEBRATION_GRID[1],
        FRAME_WIDTH, FRAME_HEIGHT
    )
    
    print("="*60)
    print("✓ PROCESO COMPLETADO!")
    print("="*60)
    print(f"\nArchivos generados en: {OUTPUT_DIR}")

# Ejecutar
if __name__ == "__main__":
    main()
