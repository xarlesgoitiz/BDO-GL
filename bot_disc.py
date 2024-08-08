import os
from flask import Flask

# Crear una instancia de Flask
app = Flask(__name__)

# Definir una ruta para la raíz
@app.route('/')
def home():
    return "El bot de Discord está funcionando!"

# Iniciar el servidor HTTP en un hilo separado
if __name__ == '__main__':
    from threading import Thread
    import discord
    from discord.ext import commands
    from dotenv import load_dotenv
    import os
    from bot_ocr_readerV1 import *
    from bot_ocr_readerV2 import *
    import time
    from PIL import Image, ImageEnhance  # Asegúrate de que esto esté incluido


    # Asegúrate de que la carpeta 'temp' exista para guardar imagenes glr
    if not os.path.exists('temp'):
        os.makedirs('temp')
        
    # Cargar variables de entorno
    load_dotenv()

    # Obtener el token de Discord de la variable de entorno
    token = os.getenv('DISCORD_TOKEN')

    # Imprimir el valor del token para depuración
    #print(f'Token: {token}')

    if token is None:
        print('Error: No se pudo cargar el token. Asegúrate de que el archivo .env esté configurado correctamente.')
    else:
        intents = discord.Intents.all()
        intents.messages = True
        intents.members = True

        bot = commands.Bot(command_prefix='!', intents=intents)

        # Variable para almacenar el ID del canal restringido
        allowed_channel_id = None

        @bot.command()
        async def info(ctx):
            if allowed_channel_id is not None and ctx.channel.id != allowed_channel_id:
                return  # Ignora comandos fuera del canal permitido
            await ctx.send('Soy un botardo cabron, desarrollado por  el grandioso Xaaaarrrr! :snake: \n si no sabes nada el botardo ```!commands```')

        @bot.command()
        async def commands(ctx):
            """Muestra una lista de los comandos disponibles y lo que hacen."""
            command_list = (
                "**!bind** Vincula el canal actual para que el bot solo responda aquí.\n"
                "**!unbind** Desvincula el canal, permitiendo respuestas en todos los canales.\n"
                "**!fototip** informacion para que parte hacer screenshot (solo en el canal vinculado).\n"
                "**!info** Muestra información sobre el bot y su creador (solo en el canal vinculado).\n"
                "**!glr <adjunta_foto>** foto convierte a texto y sube al sheet (solo en el canal vinculado).\n"
                "**!share_sheet <email>** Comparte la hoja de cálculo con el correo electrónico proporcionado.\n"
                "**!url** Envía un enlace a la hoja de cálculo de Guild League."
            
            )
            await ctx.send(command_list)
        
        @bot.command()
        async def fototip(ctx):
            """Envía un ejemplo de cómo capturar la foto y da consejos sobre la configuración."""
            # Ruta de la imagen de ejemplo
            image_path = 'fototip/fototip.png'
            
            # Enviar la imagen de ejemplo
            await ctx.send(file=discord.File(image_path))

            # Mensaje de instrucciones
            instructions = (
                "Para capturar la foto de la mejor manera, sigue estos consejos:\n"
                "1. Asegúrate de que la iluminación sea adecuada.\n"
                "2. Ajusta la configuración de pantalla:\n"
                "   - Ve a Settings > Display Settings > Effects.\n"
                "   - Ajusta el Contraste a -50.\n"
                "   - Ajusta la Gama a +50.\n"
                "3. Ajusta el nombre y clan:\n"
                "   - Ve a Settings > General Settings > Show-Hide.\n"
                "   - Caracter name: always hide. \n"
                "Estos ajustes oscurecen el fondo, y quitan lecturas que no tengan que ver con la score lo que permite que la foto sea mejor leída al capturar el score."
            )
            
            # Enviar las instrucciones
            await ctx.send(instructions)
        
        @bot.command()
        async def bind(ctx):
            global allowed_channel_id
            allowed_channel_id = ctx.channel.id  # Establece el ID del canal donde se ejecuta el comando
            await ctx.send(f'Canal vinculado: <#{allowed_channel_id}>. El bot solo responderá en este canal.')

        @bot.command()
        async def unbind(ctx):
            global allowed_channel_id
            allowed_channel_id = None  # Desvincula el canal
            await ctx.send('El bot ahora responderá en todos los canales.')

        @bot.command()
        async def glr(ctx):
            template_path = 'resources/templateGL_V2.png'
            await procesar_y_guardar_imagen(ctx, template_path, procesar_imagen)

        @bot.command()
        async def glrV2(ctx):
            template_path = 'resources/templateGL_V2.png'
            await procesar_y_guardar_imagen(ctx, template_path, procesar_imagenV3)

        @bot.command()
        async def share_sheet(ctx, email: str):
            """Comparte la hoja de cálculo con el correo electrónico proporcionado y elimina el mensaje del comando."""
            try:
                # Llamar a la función del archivo auxiliar
                response = share_sheet_with_email(email)
                await ctx.send(response)
            except Exception as e:
                await ctx.send(f'Ocurrió un error: {str(e)}')
            finally:
                # Asegúrate de que la eliminación del mensaje se realiza después de enviar la respuesta
                try:
                    await ctx.message.delete()
                except Exception as delete_error:
                    # Puedes manejar el error de eliminación aquí si es necesario
                    print(f"Error al intentar eliminar el mensaje: {str(delete_error)}")
                
        @bot.command()
        async def url(ctx):  
            sheet_url = 'https://docs.google.com/spreadsheets/d/1aDwM4ZJM57Mj83VKbgwdjp2bZc8M9VeN2BYxJ8C4AGc'
            await ctx.send(f'url para el acceso al Sheet de Guild League:({sheet_url})')
            
        async def procesar_y_guardar_imagen(ctx, template_path, procesar_func):
            if allowed_channel_id is not None and ctx.channel.id != allowed_channel_id:
                return  # Ignora comandos fuera del canal permitido

            # Verifica si hay archivos adjuntos en el mensaje
            if ctx.message.attachments:
                # Toma el primer archivo adjunto
                attachment = ctx.message.attachments[0]

                # Genera un nombre único para el archivo
                timestamp = int(time.time())
                nombre_archivo = f"{timestamp}_{attachment.filename}"

                og_img_path = os.path.join('temp', 'img', nombre_archivo)  # ruta img sin editar
                ed_img_path = os.path.join('temp', 'edited_img', nombre_archivo)  # ruta edited_img

                # Asegurarse de que las carpetas existan
                os.makedirs(os.path.dirname(og_img_path), exist_ok=True)
                os.makedirs(os.path.dirname(ed_img_path), exist_ok=True)

                # Guarda el archivo adjunto localmente en la carpeta 'temp/img'
                await attachment.save(og_img_path)

                # Cargar la imagen para procesarla
                imagen = Image.open(og_img_path)  # Abre la imagen original

                # Crear y aplicar mejoras
                enhancer_contraste = ImageEnhance.Contrast(imagen)
                contraste_ajustado = enhancer_contraste.enhance(1.0)  # Ajusta el valor según sea necesario

                enhancer_saturacion = ImageEnhance.Color(contraste_ajustado)
                saturacion_ajustada = enhancer_saturacion.enhance(1.6)  # Ajusta según sea necesario

                # Cargar y redimensionar la plantilla
                plantilla = Image.open(template_path)
                plantilla = plantilla.resize(contraste_ajustado.size, Image.LANCZOS)

                # Superponer la plantilla sobre la imagen
                imagen_final = Image.alpha_composite(saturacion_ajustada.convert("RGBA"), plantilla.convert("RGBA"))

                # Guardar la imagen editada
                imagen_final.save(ed_img_path)

                # Procesar la imagen localmente usando la función pasada como argumento
                response = procesar_func(ed_img_path)

                # Envía la respuesta de vuelta al canal
                await ctx.send(response)

                # Limpia la imagen después de procesarla si es necesario
                os.remove(og_img_path)  # Descomentar si deseas eliminar la imagen original
                #os.remove(ed_img_path)   # Descomentar si deseas eliminar la imagen editada
            else:
                await ctx.send("Por favor, adjunta una imagen al comando.")

        #run
        Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))).start()

        bot.run(token)

