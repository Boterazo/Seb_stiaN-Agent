# para correr el server se usa:
# uvicorn main:app --reload

# En otra terminal ejecuta: ngrok http 8000
from twilio.rest import Client
from fastapi import FastAPI, Form, Request
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI
import time


import os

from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
print("API KEY: \n"+api_key)

app = FastAPI()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")


client_TW = Client(account_sid, auth_token)

client = OpenAI(
    api_key=api_key
)


def dividir_texto(texto, limite=1500):
    partes = []
    while len(texto) > limite:
        corte = texto.rfind("\n", 0, limite)
        if corte == -1:
            corte = limite

        partes.append(texto[:corte])
        texto = texto[corte:].strip()

    partes.append(texto)
    return partes


@app.post("/whatsapp")
async def webhook(request: Request):

    # ------------------------------
    form_data = await request.form()

    print("Datos recibidos de Twilio:")
    '''
    for key, value in form_data.items():
        print(f"{key}: {value}")
	'''
    mensaje_usuario = form_data["Body"]
    numero_usuario = form_data["From"]

    print(
        f"\nmensaje_usuario: {mensaje_usuario}\n"
        f"numero_usuario: {numero_usuario}\n"
    )

    inicio = time.time()

    response = client.responses.create(
        model="gpt-5.4-mini",
        input=[
            {
                "role": "developer",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Eres mi asistente te dare unos documentos y envase a eso me ayudaras a gestionar dudas respecto a clientes que me contactan, mi línea es chat y necesito saber que procedimientos hacer de forma concisa para dar solución a el problema, saber cuando tengo que gestionar yo el procedimiento o cuando tengo que conferir, transferir o agendar una llamada al area encargada.\n\nLas líneas son: whatsApp (chats), llamadas, quejas y reclamos, fidelizacion, les basica, les konecta, etc.\n\nLas conferencias se hacen desde la línea telefónica.\n\nLas transferencia por chat solo son dos que se pueden hacer, línea de quejas y reclamos, línea de colombianos en el exterior.\n\nLas transferencias por llamadas no tienen limites así que se puede conferir o transferir sin inconveniente.\n\nMe tienes que decir de primero que linea lo atiende, recuerda que soy de chats, despues una descripcion de la solucion y si hay un procedimiento de como hacerlo ponerlo tambien.\n\nSi ves que existe una forma de obtener la informacion atraves de AS400 pones los pasos, si no hay pasos solo ignora esta regla."
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": mensaje_usuario
                    }
                ]
            },
        ],
        text={
            "format": {
                "type": "text"
            },
            "verbosity": "medium"
        },
        reasoning={
            "effort": "medium",
            "summary": "auto"
        },
        tools=[
            {
                "type": "file_search",
                "vector_store_ids": [
                    "vs_6a416bb7cb5c81919833f8e8f56932b2"
                ]
            }
        ],
        store=True,
        include=[
            "reasoning.encrypted_content",
            "web_search_call.action.sources"
        ]
    )

    print("Tiempo:", time.time() - inicio)

    respuesta_ia = response.output_text

    print("Respuesta IA:")
    print(respuesta_ia)

    for parte in dividir_texto(respuesta_ia):
        client_TW.messages.create(
            from_='whatsapp:+14155238886',
            body=parte,
            to=numero_usuario
        )

    return {"info": "ENVIADO"}


# para correr el server se usa uvicorn main:app --reload

# Arranca tu servidor FastAPI:
# uvicorn main:app --reload

# usa esto para autenticarte:
# ngrok config add-authtoken TU_TOKEN

# En otra terminal ejecuta:
# ngrok http 8000

# ngrok te dará algo así:
# https://a1b2c3d4.ngrok.io

# Entonces en Twilio debes poner:
# https://a1b2c3d4.ngrok.io/whatsapp

'''
¿Qué es ngrok?

Es una herramienta que crea un túnel seguro desde internet hacia tu computador.
Hace que tu servidor local (localhost) tenga una URL pública para que servicios como Twilio puedan conectarse.

pagina: https://dashboard.ngrok.com/get-started/setup/windows
'''
