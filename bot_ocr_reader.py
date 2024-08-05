import paddle
from paddleocr import PaddleOCR
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def authorize_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_path = os.getenv("CREDENTIALS_PATH")
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    worksheet_name = os.getenv("WORKSHEET_NAME")
    spreadsheet = client.open_by_key(sheet_id).worksheet(worksheet_name)
    return spreadsheet

def share_sheet_with_email(email: str):
    """Comparte la hoja de cálculo con el correo electrónico proporcionado con permisos de edición."""
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_path = os.getenv("CREDENTIALS_PATH")
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
        client = gspread.authorize(creds)
        sheet_id = os.getenv("GOOGLE_SHEET_ID")

        # Comparte la hoja de cálculo con el correo electrónico proporcionado
        client.insert_permission(sheet_id, email, perm_type='user', role='writer')
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

def procesar_imagen(image_path):
    print(f"Procesando la imagen: {image_path}")
    Date = ""
    Time = ""
    Opposition = ""
    Guild = "RAW"
    Enemy = ""
    GLoseWin = ""
    ELoseWin = ""

    Player = []
    Kills = []
    Death = []
    Debuffs = []
    Dealt = []
    Taken = []
    Healed = []
    line_count = 0

    Fam_names_num = [1, 7, 13, 19, 25, 31, 37, 43, 49, 55, 61, 67, 73, 79, 85, 91, 97, 103, 109, 115]
    Kill_death_num = [2, 8, 14, 20, 26, 32, 38, 44, 50, 56, 62, 68, 74, 80, 86, 92, 98, 104, 110, 116]
    Debuffs_num = [3, 9, 15, 21, 27, 33, 39, 45, 51, 57, 63, 69, 75, 81, 87, 93, 99, 105, 111, 117]
    Dealt_num = [4, 10, 16, 22, 28, 34, 40, 46, 52, 58, 64, 70, 76, 82, 88, 94, 100, 106, 112, 118]
    Taken_num = [5, 11, 17, 23, 29, 35, 41, 47, 53, 59, 65, 71, 77, 83, 89, 95, 101, 107, 113, 119]
    Healed_num = [6, 12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 72, 78, 84, 90, 96, 102, 108, 114, 120]

    ocr = PaddleOCR(use_angle_cls=True, lang='en')

    try:
        result = ocr.ocr(image_path, cls=True)
        #print(f"Resultado del OCR: {result}")
        if len(result) > 0:
            extracted_text = []
            for line in result:
                for word in line:
                    extracted_text.append(word[1][0])

            parts = '\n'.join(extracted_text)
            parts = parts.split('\n')
            
            print(parts)
            parts = [line.replace(' ', '_') if ' ' in line else line for line in parts]
                       
            date_pattern = r'\d{4}-\d{2}-\d{2}'
            time_pattern = r'\d{1,2}:\d{2}'
            win_pattern = r'\[Victory(?:, Victory)?\]|\[Defeat(?:, Defeat)?\]|Victory|Defeat'
            enemy_pattern = r'(\d{1,2}:\d{2}):(\w+)'

            for part in parts[:3]:  # Iterar solo sobre las primeras tres partes
                match_date = re.search(date_pattern, part)
                if match_date:
                    Date = match_date.group(0)

                match_time = re.search(time_pattern, part)
                if match_time:
                    Time = match_time.group(0)
                    enemy_match = re.search(enemy_pattern, part)
                    if enemy_match:
                        Enemy = enemy_match.group(2)

                match_win = re.search(win_pattern, part)
                if match_win:
                    GLoseWin = match_win.group(0).replace('[', '').replace(']', '')

            if Date == "":
                #Date = input("No date found. Please enter a date in the format YYYY-MM-DD: ")
                Date = "Unknown"
            if Time == "":
                #Time = input("A time was not found. Please enter a time in the format HH:MM ")
                Time = "Unknown"
            if GLoseWin == "":
                while GLoseWin not in ["Victory", "Defeat"]:
                    #win_input = input("No result (Victory/Defeat) was found. Please enter 'V' for Victory or 'D' for Defeat: ").strip().upper()
                    win_input = "Unknown"
                    if win_input == 'V':
                        GLoseWin = "Victory"
                    elif win_input == 'D':
                        GLoseWin = "Defeat"
                    elif win_input == 'Unknown':
                        GLoseWin = "Unknown"
                    else:
                        print("Invalid input. Please enter 'V' for Victory or 'D' for Defeat.")
            if Enemy == "":
                #Enemy = input("Enemy name was not found. Please enter the enemy name: ")
                Enemy = "Unknown"
            ELoseWin = "Defeat" if GLoseWin == "Victory" else "Victory"
            Opposition = Enemy

            healed_count = 0
            index_to_start = 0

            for i, part in enumerate(parts):
                if part == "Healed":
                    healed_count += 1
                    if healed_count == 2:
                        index_to_start = i + 1
                        break

            parts = parts[index_to_start:]

            for part in parts:
                line_count += 1

                if line_count in Fam_names_num:
                    Player.append(part)

                if line_count in Kill_death_num:
                    if ('/' not in part or '|' not in part) and line_count < len(parts):

                        part += parts[line_count]

                    # Separar la cadena usando '/' o '|'
                    partes = re.split(r'[\/|]', part)
                    if len(partes) == 2 and partes[0].isdigit() and partes[1].isdigit():
                        Kills.append(int(partes[0]))
                        Death.append(int(partes[1]))

                if line_count in Debuffs_num:
                    Debuffs.append(part)

                if line_count in Dealt_num:
                    Dealt.append(part)

                if line_count in Taken_num:
                    Taken.append(part)

                if line_count in Healed_num:
                    Healed.append(part)

            Start_time = round_time_to_half_hour(Time)
            Duration = calculate_duration(Start_time, Time)    
            Match = Date + " " + Time + " " + Opposition

            # Al final de todo el procesamiento
            ws = authorize_google_sheets()

            # Calcular la última fila existente
            last_row = len(ws.get_all_values()) + 1  # La nueva fila es la primera después de la última fila existente

            # Listas para almacenar los datos de filas impares y pares
            odd_rows = []
            even_rows = []

            # Suponiendo que i es el índice de un bucle que recorre un rango
            for i in range(max(len(Kills), len(Player), len(Death), len(Debuffs), len(Dealt), len(Taken), len(Healed))):
                # Determinar si es impar o par
                # Calcular K/D
                kd_ratio = 0
                Kills_player = Kills[i] if i < len(Kills) else 0  # Asegúrate de que el índice no exceda
                Death_player = Death[i] if i < len(Death) else 0  # Asegúrate de que el índice no exceda

                if Death_player == 0:
                    kd_ratio = Kills_player  # Si muere 0 veces, el ratio es Kills
                else:
                    kd_ratio = Kills_player / Death_player

                kd_ratio = round(kd_ratio, 2)  # Redondear a dos decimales
                
                if i % 2 == 0:  # Fila impar (índice 0, 2, 4, ...)
                    kill_value = Kills[i] if i < len(Kills) else "Unknown"
                
                    row_data = [
                        Date, 
                        Time, 
                        Opposition, 
                        Match, 
                        "10", 
                        Start_time, 
                        Duration, 
                        GLoseWin,
                        Player[i] if i < len(Player) else "Unknown",
                        "", "",
                        Guild,
                        kill_value,
                        Death[i] if i < len(Death) else "Unknown",
                        kd_ratio,
                        Debuffs[i] if i < len(Debuffs) else "Unknown",
                        Dealt[i] if i < len(Dealt) else "Unknown",
                        Taken[i] if i < len(Taken) else "Unknown", 
                        Healed[i] if i < len(Healed) else "Unknown",
                    ]
                    odd_rows.append(row_data)
                else:  # Fila par (índice 1, 3, 5, ...)
                    kill_value = Kills[i] if i < len(Kills) else "Unknown"
                    
                    row_data = [
                        Date, 
                        Time, 
                        Opposition, 
                        Match, 
                        "10", 
                        Start_time, 
                        Duration,
                        ELoseWin,
                        Player[i] if i < len(Player) else "Unknown",
                        "", "",
                        Enemy,
                        kill_value,
                        Death[i] if i < len(Death) else "Unknown",
                        kd_ratio,
                        Debuffs[i] if i < len(Debuffs) else "Unknown",
                        Dealt[i] if i < len(Dealt) else "Unknown",
                        Taken[i] if i < len(Taken) else "Unknown",
                        Healed[i] if i < len(Healed) else "Unknown"
                    ]
                    
                    even_rows.append(row_data)
              
            # Combinar las filas de odd_rows y even_rows
            all_rows = odd_rows + even_rows

            # Insertar todas las filas a la vez
            ws.insert_rows(all_rows, 2)

        return "Imagen procesada con éxito"  # Mensaje de éxito al finalizar
    
    except Exception as e:
        return f"Error al procesar la imagen: {str(e)}"  # Mensaje de error

if __name__ == "__main__":
    # Para pruebas locales, puedes llamar a la función directamente
    print(procesar_imagen("ruta_de_la_imagen_a_procesar.jpg"))
