import pytesseract
from PIL import Image
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Configura el path para Tesseract si es necesario
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def authorize_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key("1gf58gVjVIfmiSjkvwOTRx1FflI3yXeKWruuqozV6944").worksheet("Raw Data")
    return spreadsheet

def share_sheet_with_email(email: str):
    """Comparte la hoja de cálculo con el correo electrónico proporcionado con permisos de edición."""
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        client = gspread.authorize(creds)
        SHEET_ID = '1gf58gVjVIfmiSjkvwOTRx1FflI3yXeKWruuqozV6944'  # Cambia esto al ID de tu hoja de cálculo

        # Comparte la hoja de cálculo con el correo electrónico proporcionado
        client.insert_permission(SHEET_ID, email, perm_type='user', role='writer')
        return f'La hoja de cálculo ha sido compartida con {email} con permisos de edición.'
    except Exception as e:
        return f'Ocurrió un error al intentar compartir la hoja de cálculo: {str(e)}'

def round_time_to_half_hour(time_str):
    time_obj = datetime.strptime(time_str, "%H:%M")
    if time_obj.minute >= 30:
        rounded_time = time_obj.replace(minute=30, second=0)
    else:
        rounded_time = time_obj.replace(minute=0, second=0)
    return rounded_time.strftime("%H:%M")

def calculate_duration(start_time_str, end_time_str):
    start_time = datetime.strptime(start_time_str, "%H:%M")
    end_time = datetime.strptime(end_time_str, "%H:%M")
    duration = (end_time - start_time).total_seconds() / 60
    return str(int(duration))

# Función para extraer información del encabezado
def parse_header(header):
    # Expresión regular ajustada para manejar todos los casos mencionados
    match = re.match(r'\[?(Victory|Defeat)\]?\s*(\d{4}-\d{2}-\d{2})\s*(\d{2}:\d{2})(?:\s*:\s*(.+))?', header)
    if match:
        result, date, time, enemy_result = match.groups()
        enemy_result = enemy_result or ""
        return result, date, time, enemy_result
    return None, None, None, None

# Función para separar kills y deaths
def separar_kills_deaths(k_d):
    if '/' in k_d:
        kills, deaths = k_d.split('/')
    elif '|' in k_d:
        kills, deaths = k_d.split('|')
    else:
        kills, deaths = k_d, '0'  # Caso por defecto si no hay separador
    return int(kills), int(deaths)

def procesar_imagenV3(image_path):
    print(f"Procesando la imagen: {image_path}")

    try:
        # Cargar la imagen
        img = Image.open(image_path)
        
        # Realizar OCR usando Tesseract
        extracted_text = pytesseract.image_to_string(img)

        print(f"Texto extraído: {extracted_text}")

        lines = extracted_text.splitlines()
        if len(lines) > 0:
            # Extraer información del encabezado
            enemy_result, date, time, enemy_guild = parse_header(lines[0])
            guild_result, guild = re.match(r'\[(Victory|Defeat)\](.+)', lines[1]).groups()
            enemy_result, enemy_guild = re.match(r'\[(Victory|Defeat)\](.+)', lines[2]).groups()

            # Crear listas para cada columna de la tabla de jugadores
            players = []
            kills = []
            deaths = []
            debuffs = []
            dealt = []
            taken = []
            healed = []

            # Iterar sobre los datos de los jugadores y llenar las listas
            for i in range(3, len(lines), 6):
                players.append(lines[i])
                k, d = separar_kills_deaths(lines[i + 1])
                kills.append(k)
                deaths.append(d)
                debuffs.append(lines[i+2])
                dealt.append(lines[i+3])
                taken.append(lines[i+4])
                healed.append(lines[i+5])

            Start_time = round_time_to_half_hour(time)
            Duration = calculate_duration(Start_time, time)    
            Match = date + " " + time + " " + enemy_guild

            # Al final de todo el procesamiento
            ws = authorize_google_sheets()

            # Calcular la última fila existente
            last_row = len(ws.get_all_values()) + 1  # La nueva fila es la primera después de la última fila existente

            all_rows = []
            num_rows = max(len(kills), len(players), len(deaths), len(debuffs), len(dealt), len(taken), len(healed))

            for i in range(num_rows):
                # Calcular K/D
                Kills_player = kills[i] if i < len(kills) else 0
                Death_player = deaths[i] if i < len(deaths) else 0
                kd_ratio = Kills_player / Death_player if Death_player != 0 else Kills_player
                kd_ratio = round(kd_ratio, 2)  # Redondear a dos decimales

                row_data = [
                    date, 
                    time, 
                    enemy_guild,
                    Match, 
                    "10", 
                    Start_time, 
                    Duration, 
                    guild_result if i % 2 == 0 else enemy_result,
                    players[i] if i < len(players) else "Unknown",
                    "", "", 
                    guild if i % 2 == 0 else enemy_guild,
                    kills[i] if i < len(kills) else "Unknown",
                    deaths[i] if i < len(deaths) else "Unknown",
                    kd_ratio,
                    debuffs[i] if i < len(debuffs) else "Unknown",
                    dealt[i] if i < len(dealt) else "Unknown",
                    taken[i] if i < len(taken) else "Unknown", 
                    healed[i] if i < len(healed) else "Unknown",
                    "", ""
                ]
                all_rows.append(row_data)

            # Dividir las filas en impares y pares
            odd_rows = [all_rows[i] for i in range(len(all_rows)) if i % 2 == 0]
            even_rows = [all_rows[i] for i in range(len(all_rows)) if i % 2 != 0]

            all_rows = odd_rows + even_rows

            # Insertar todas las filas a la vez
            ws.insert_rows(all_rows, 2)

        return "Imagen procesada con éxito"  # Mensaje de éxito al finalizar

    except Exception as e:
        return f"Error al procesar la imagen: {str(e)}"  # Mensaje de error

if __name__ == "__main__":
    # Para pruebas locales, puedes llamar a la función directamente
    print(procesar_imagenV3("ruta_de_la_imagen_a_procesar.jpg"))