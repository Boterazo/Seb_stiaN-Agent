from twilio.rest import Client
from fastapi import FastAPI, Form, Request
from fastapi.responses import Response
from twilio.twiml.messaging_response import MessagingResponse
from openai import OpenAI
import time


import os


api_key = os.getenv("OPENAI_API_KEY", "")


app = FastAPI()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")


client_TW = Client(account_sid, auth_token)

client = OpenAI(
    api_key=api_key
)

# Guarda la última conversación de cada usuario de WhatsApp
ultima_conversacion = {}


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


def Enviar_msg_pensando(msg, tel):
    client_TW.messages.create(
        from_='whatsapp:+14155238886',
        body=str(msg),
        to=str(tel)
    )


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
    mensaje_usuario = str(mensaje_usuario)
    numero_usuario = str(form_data["From"])

    historial = ultima_conversacion.get(numero_usuario, [])

    print(
        f"\nmensaje_usuario: {mensaje_usuario}\n"
        f"numero_usuario: {numero_usuario}\n"
    )

    Enviar_msg_pensando("Pensando...", numero_usuario)

    inicio = time.time()

    response = client.responses.create(
        model="gpt-5.4-mini",
        input=[
            {
                "role": "developer",
                "content": [
                    {
                        "type": "input_text",
                        "text": """- Descripción general\nEres mi asistente, te daré documentos y con base en ellos me ayudarás a gestionar dudas de los clientes que me contactan, mi canal principal es chat (WhatsApp), necesito saber qué procedimientos realizar de forma concisa para dar solución a los problemas, identificar cuándo debo gestionarlos directamente y cuándo debo conferir,
                         transferir o agendar una llamada al área encargada.\n- Líneas de atención\nWhatsApp (chats), llamadas, quejas y reclamos, fidelización, les básica, les konecta, soporte crédito hipotecario, Cardif, referidos, Sura, asistencias AXA, leasing, televenta Bancolombia, fiduciaria Bancolombia, entre otras.\n- Conferencias y transferencias\nLas conferencias se realizan únicamente desde la línea telefónica, 
                         las transferencias por chat (WhatsApp) solo se permiten en dos casos: línea de quejas y reclamos, línea de colombianos en el exterior, si no es posible transferir o conferir desde WhatsApp se debe agendar una llamada, las transferencias por llamadas no tienen límite y se pueden realizar sin inconveniente, las conferencias solo se realizan por llamada.
                         \n- Procedimiento de respuesta\nPrimero indicar si el caso lo atiendo yo (chat WhatsApp), si se transfiere o si se confiere, después dar una descripción de la solución, si existe un procedimiento incluirlo paso a paso, sugerir un código de tipificación según el archivo “codificacion.docx” (solo se puede usar un código pero se pueden recomendar máximo tres), 
                         si la solución requiere radicar el proceso incluir el paso a paso, si no hay requerimiento dentro de la solución no se incluye nada adicional, si la información se puede obtener a través de AS400 poner los pasos, si no aplica escribir “AS400 no aplica”.\n- Notas adicionales\nAS400 es una herramienta de consultas en consola de comandos, sucursal virtual personas es un aplicativo web de Bancolombia, 
                         sucursal virtual personas es la página web de Bancolombia para los usuarios y se abrevia SVP, gestor transaccional es una herramienta también, es un aplicativo pero para los agentes de Bancolombia, TD es tarjeta débito, TDC es tarjeta de crédito, CxC es cuentas por cobrar."""
                    }
                ]
            }, *historial,
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
                    "vs_6a4472c79fdc8191bee1d8968140255e"
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

    ultima_conversacion[numero_usuario] = [
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": mensaje_usuario
                }
            ]
        },
        {
            "role": "assistant",
            "content": [
                {
                    "type": "output_text",
                    "text": respuesta_ia
                }
            ]
        }
    ]

    for parte in dividir_texto(respuesta_ia):
        client_TW.messages.create(
            from_='whatsapp:+14155238886',
            body=parte,
            to=numero_usuario
        )

    return {"info": "ENVIADO"}
