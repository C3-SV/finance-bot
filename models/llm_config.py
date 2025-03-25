import os, sys
from openai import OpenAI
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
#from langchain_community.llms import OpenAI
from langchain_community.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
import json
import faiss
import numpy as np
#INICIAL 
# Configurar API de OpenAI
from dotenv import load_dotenv
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Inicializar el cliente de OpenAI
os.environ["OPENAI_API_KEY"] = openai_api_key
openai_client = OpenAI(api_key=openai_api_key)
#client = OpenAI(
#    api_key = openai_api_key
#)
FINE_TUNED_MODEL = "ft:gpt-4o-mini-2024-07-18:competitivecodingclub::BEqeTYBE"
FEEDBACK_FILE = "models\\feedback_data\\chatbot_feedback.json"
TRAINING_FILE = "models\\fine_tuning_data\\training_data.jsonl"
FEEDBACK_LIMIT = 50
#MANEJO DE EMBEDDINGS PARA FEEDBACK 
EMBEDDING_MODEL = "text-embedding-ada-002"
dimension = 1536 
index = faiss.IndexFlatL2(dimension)

# INFORMACION SI ES CLIENTE 
from is_client import get_is_client_string
# FECHA PARA CONTEXTO
from datetime import datetime
# Consideraciones estandar para el sys message 
def get_standard_sys_msg():
    fecha_hora = datetime.now()
    dia_semana = fecha_hora.strftime("%A")  # Ejemplo: "Monday", "Tuesday", etc.
    fecha_hora_string =   f"\nCONSIDERACIONES: \n La hora actual es {fecha_hora}. El dia es {dia_semana}. Ignora cualquier cosa que contradiga esto."

    standard_msg = '''

    No repitas la consulta del usuario.

    No menciones que la pregunta del usuario puede tener un error tipográfico a menos que sea muy claro. Considera la pregunta original del usuario como la fuente de verdad.

    Presenta tu respuesta de manera ordenada y cohesiva usando markdown. Puedes reorganizar el orden de la información para mejorar la respuesta.

    Comienza con una sección de respuesta directa (sin mencionar respuesta directa en el título o en cualquier parte). Luego, presenta una sección detallada con toda la respuesta en estilo de puntos breves y que incluya todos los detalles. Termina con una conclusion y sugiere posible continuación a la pregunta. 

    La sección de respuesta directa debe abordar la consulta del usuario con matices basados en incertidumbre o complejidad. Incluye hechos clave que el usuario probablemente espera, y considera agregar detalles inesperados (evita usar detalle sorprendente en el título; describe lo inesperado). Escrita para un público conocedor, la respuesta debe ser clara y fácil de seguir.

    La sección de respuesta directa debe comenzar con puntos clave muy breves, seguidos de algunas secciones cortas, antes de comenzar la sección detallada. Usa negritas y encabezados apropiados cuando sea necesario. Incluye URLs de soporte cuando sea posible. Los puntos clave deben tener un nivel adecuado de firmeza basado en tu nivel de incertidumbre y resaltar cualquier controversia sobre el tema. Solo usa afirmaciones absolutas si la pregunta no es sensible/controvertida y estás completamente seguro. De lo contrario, usa lenguaje que reconozca la complejidad. 

    Usa encabezados y tablas para mejorar la organización. Procura incluir al menos una tabla (o varias tablas) en la sección de informe a menos que se indique lo contrario.

    Incluye toda la información relevante del rastro de pensamiento en la respuesta, no solo de la parte final.

    La respuesta debe ser completa y autónoma, ya que el usuario no tendrá acceso al rastro de pensamiento.

    La respuesta debe ser un documento independiente que responda la pregunta del usuario sin repetirla.

    Debes responder en español.
    '''
    standard_msg = fecha_hora_string + standard_msg
    return standard_msg

# Consideraciones para los client del sys message
def get_complement_sys_msg_client():
    fecha_hora = datetime.now()
    dia_semana = fecha_hora.strftime("%A")  # Ejemplo: "Monday", "Tuesday", etc.
    fecha_hora_string =   f"CONSIDERACIONES: \n La hora actual es {fecha_hora}. El dia es {dia_semana}. Ignora cualquier cosa que contradiga esto."

    standard_msg = '''

    No repitas la consulta del usuario.

    No menciones que la pregunta del usuario puede tener un error tipográfico a menos que sea muy claro. Considera la pregunta original del usuario como la fuente de verdad.

    Presenta tu respuesta de manera ordenada y cohesiva usando markdown. Puedes reorganizar el orden de la información para mejorar la respuesta.

    Comienza con una sección de respuesta directa (sin mencionar respuesta directa en el título o en cualquier parte). Luego, presenta una sección detallada con toda la respuesta en estilo de puntos breves y que incluya todos los detalles. Termina con una conclusion y sugiere posible continuación a la pregunta. 

    La sección de respuesta directa debe abordar la consulta del usuario con matices basados en incertidumbre o complejidad. Incluye hechos clave que el usuario probablemente espera, y considera agregar detalles inesperados (evita usar detalle sorprendente en el título; describe lo inesperado). Escrita para un público conocedor, la respuesta debe ser clara y fácil de seguir.

    Usa encabezados y tablas si mejoran la organización. Procura incluir al menos una tabla (o varias tablas) a menos que se indique lo contrario.

    La respuesta debe ser completa y autónoma, ya que el usuario no tendrá acceso al rastro de pensamiento.
    
    Considera que te diriges a conocedores del negocio. 
    
    Prioriza usar tablas y recursos que complementen. 
    
    Prioriza agregar informacion especifica que haga personalizada la respuesta. 
    
    Agrega toda la informacion relevante. Puedes mencionar datos destacados e interesantes si existen y si complementan a la respuesta. 

    Debes responder en español.
    '''
    standard_msg = fecha_hora_string + standard_msg
    return standard_msg



# Funcion para actualizar el fine tunning 
def prepare_fine_tunning_data():
    if not os.path.exists(FEEDBACK_FILE):
        return
    
    with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    with open(TRAINING_FILE, "a", encoding="utf-8") as f:
        for entry in data:
            if entry["feedback"] == "like":
                f.write(json.dumps({
                        "messages": [
                            {"role": "system", "content": "Eres un asesor financiero experto para PYMES."},
                            {"role": "user", "content": entry["prompt"]},
                            {"role": "assistant", "content": entry["response"]}
                        ]
                    }, ensure_ascii=False) + "\n")
            elif entry["feedback"] == "dislike":
                f.write(json.dumps({
                    "messages": [
                        {"role": "system", "content": "Eres un asesor financiero experto para PYMES."},
                        {"role": "user", "content": entry["prompt"]},
                        {"role": "assistant", "content": "[EVITAR ESTA RESPUESTA:]" + entry["response"]}
                    ]
                }, ensure_ascii=False) + "\n")
                
    # Limpiar el archivo de retroalimentación después de generar el training file
    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)
                
# Inicializar el modelo de OpenAI
def get_openai_llm():
    return ChatOpenAI(
        model= FINE_TUNED_MODEL,
        api_key = openai_api_key,
        temperature=0.4
    )
    
def get_simple_openai_llm():
    return ChatOpenAI(
        model= "gpt-4o-mini",
        api_key= openai_api_key,
        temperature = 0.4
    )
    
# FUNCION PARA GENERAR EL EMBEDDING DE TEXTO 
def get_embedding(text):
    response = openai_client.embeddings.create(input = text, model = EMBEDDING_MODEL)
    return np.array(response.data[0].embedding, dtype = np.float32)

# FUNCION PARA GUARDAR FEEDBACK 
def save_feedback(prompt, response, feedback):
    data = []
    if os.path.exists(FEEDBACK_FILE):
        try: 
            with open(FEEDBACK_FILE, 'r', encoding = 'utf-8') as file:
                content = file.read().strip()
                if content:
                    data = json.loads(content)
        except (json.JSONDecodeError, ValueError):
            data = []
                
    embedding = get_embedding(prompt).tolist()
    data.append({"prompt": prompt, "response": response, "feedback": feedback, "embedding": embedding})
    
    # INSERTAR EN FEEDBACK_FILE 
    with open(FEEDBACK_FILE, 'w', encoding= 'utf-8') as file: 
        json.dump(data, file, ensure_ascii= False, indent= 2)
    # FUTURO --> CONVERTIR FEEDBACK_FILE EN FINE TUNNING FILE 
    if len(data) >= FEEDBACK_LIMIT:
        prepare_fine_tunning_data()
        print("Limite alcanzado de feedback, generando {}")

# FUNCION PARA OBTENER FEEDBACK RELEVANTE 
def get_similar_feedback(prompt, k = 3):
    if not os.path.exists(FEEDBACK_FILE):
        return {"likes": [], "dislikes": []}
    
    data = []
    try: 
        with open(FEEDBACK_FILE, 'r', encoding = 'utf-8') as file:
            content = file.read().strip()
            if content:
                data = json.loads(content)
    except (json.JSONDecodeError, ValueError):
        return {"likes": [], "dislikes": []}
    
    if not data:
        return {"likes": [], "dislikes": []}
    
    embeddings = np.array([entry["embedding"] for entry in data], dtype=np.float32)
    global index
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    
    query_embedding = get_embedding(prompt)
    distances, indices = index.search(np.array([query_embedding]), k)
    
    likes = []
    dislikes = []
    for idx in indices[0]:
        entry = data[idx]
        if entry["feedback"] == "like":
            likes.append(entry["response"])
        elif entry["feedback"] == "dislike":
            dislikes.append(entry["response"])
    
    return {"likes": likes[:k], "dislikes": dislikes[:k]}


# Función para usar chat completions directamente
def get_chat_completion(prompt, context=None, chat_history=None, temperature=0.5, max_tokens=2000):
    """-
    Genera una respuesta usando el endpoint /v1/chat/completions con el modelo ajustado.
    
    Args:
        prompt (str): La pregunta o instrucción del usuario.
        context (str, optional): Contexto adicional (ej. del vector store).
        chat_history (list, optional): Lista de mensajes previos para incluir historial.
        temperature (float): Controla la creatividad (0.0 = determinista).
        max_tokens (int): Límite de tokens en la respuesta.
    
    Returns:
        str: Respuesta generada por el modelo.
    """
    sys_message = '''
    Eres un asesor financiero experto que siempre brinda respuestas detalladas, desarrollado por la fintech Ábaco, enfocado en PYMES de Centroamérica. 
    Sigue este formato al responder: 
    1) Respuesta general explicada en terminos simplese. Agrega los conceptos clave. 
    2) Explica la respuesta y su importancia. 
    3) Detalla pasos concretos para abordarlo, numerados y separados. 
    4) Incluye un ejemplo práctico. 
    5) Concluye con una recomendación, Ábaco puede ayudar y un seguimiento a la pregunta.
    '''
    sys_message += get_complement_sys_msg_client()
    sys_message += get_is_client_string()
    messages = [
        {"role": "system", "content": sys_message} 
    ]
    
    # Añadir historial si existe
    if chat_history:
        for msg in chat_history:
                # Obtener el rol desde el tipo de mensaje de LangChain
                role = getattr(msg, 'type', 'user')  # Default a 'user' si no hay type
                if role == "human":
                    role = "user"
                elif role == "ai":
                    role = "assistant"
                messages.append({"role": role, "content": msg.content})
    
    # Buscar feedback similar
    feedback = get_similar_feedback(prompt)
    # Construir el mensaje del usuario
    user_content = f"ANALIZA Y RESPONDE EN ESPAÑOL\nPregunta del usuario: {prompt}"
    if context:
        user_content += f"\nRespuesta Base y Marco Teorico, Esta es la repuesta del conocimiento de Abaco, usalo a detalle y con precision para tu respuesta: {context}"
    if feedback["likes"]:
        user_content += f"\nRespuestas bien valoradas, sigue este estilo: {', '.join(str(like) for like in feedback['likes'])}"
    if feedback["dislikes"]:
        user_content += f"\nRespuestas mal valoradas, evita seguir este estilo: {', '.join(str(dislike) for dislike in feedback['dislikes'])}"
    messages.append({"role": "user", "content": user_content})
    
    try:
        response = openai_client.chat.completions.create(
            model=FINE_TUNED_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"GetCompletion -- Error al procesar la consulta: {str(e)}")
    
#! FUNCION PARA LOS COMPLETIONS DEL CLIENTE 
def get_client_chat_completion(prompt, general_answer=None, chat_history=None, empresa_data=None, temperature=0.5, max_tokens=2000):
    """-
    Genera una respuesta para clients usando chat completion con el modelo ajustado.
    
    Args:
        prompt (str): La pregunta o instrucción del usuario.
        general_answer (str, optional): Respuesta basica 
        chat_history (list, optional): Lista de mensajes previos para incluir historial.
        temperature (float): Controla la creatividad (0.0 = determinista).
        max_tokens (int): Límite de tokens en la respuesta.
    
    Returns:
        str: Respuesta generada por el modelo.
    """
    
    sys_message = (
        '''
        Eres un asesor financiero experto de Ábaco para clientes. Siempre proporciona respuestas detalladas y personalizadas basadas en los datos de la empresa del usuario.
        Tienes acceso a lo siguiente:
        1. Pregunta del usuario, tu prioridad y lo que debes resolver
        2. Informacion de la web de Abaco que puede guiarte en la respuesta (opcional)
        3. Data de la empresa, toda la data disponible de la empresa para que generes una respuesta basada en la empresa del usuario
        Para responder, considera lo siguiente: 
        - Presentar la respuesta y definición de conceptos claves. 
        - Explicacion detallada de la respuesta, incluyendo datos relevantes. Agrega informacion de la empresa para esto. Es prioridad incluir la informacion de la empresa y personalizar. 
        - Explicacion con los datos de la empresa. Esta parte es critica, usa de forma detallada la informacion existente de la empresa para explicar y completar la respuesta.
       '''
    )
    sys_message += get_is_client_string()
    sys_message += get_complement_sys_msg_client()
    if empresa_data:
        sys_message += f"\nDatos de la empresa: {json.dumps(empresa_data, ensure_ascii=False, indent=2)}"
        
    messages = [{"role": "system", "content": sys_message}]
    
    # Añadir historial si existe
    if chat_history:
        for msg in chat_history:
                # Obtener el rol desde el tipo de mensaje de LangChain
                role = getattr(msg, 'type', 'user')  # Default a 'user' si no hay type
                if role == "human":
                    role = "user"
                elif role == "ai":
                    role = "assistant"
                messages.append({"role": role, "content": msg.content})
    
    # Buscar feedback similar
    feedback = get_similar_feedback(prompt)
    # Construir el mensaje del usuario
    user_content = f"\nPregunta del usuario: {prompt}"
    if general_answer:
        user_content += f"\nInformacion de apoyo: {general_answer}"
    if feedback["likes"]:
        user_content += f"\nRespuestas bien valoradas, sigue este estilo: {', '.join(str(like) for like in feedback['likes'])}"
    if feedback["dislikes"]:
        user_content += f"\nRespuestas mal valoradas, evita seguir este estilo: {', '.join(str(dislike) for dislike in feedback['dislikes'])}"
    messages.append({"role": "user", "content": user_content})
    
    try:
        response = openai_client.chat.completions.create(
            model=FINE_TUNED_MODEL,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        print(f"RESPUESTA DESDE CLIENT CHAT COMPLETION {response.choices[0].message.content}")
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"GetCompletion -- Error al procesar la consulta: {str(e)}")

if __name__ == "__main__":
    print("Completed llm_config")