from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.tools import Tool

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import models.llm_config as llm_config
chat  = llm_config.get_openai_llm()

# Importar memoria 
import memory.context as context
memory = context.get_conversation_memory()

#Balance general
prompt_balance	= PromptTemplate(
    input_variables=["input"],
    template="""
    PARA ESTA TAREA ES ESENCIAL QUE CONSULTES LA MEMORIA DE BUFFER EXISTENTE Y/O EL TEXTO INGRESADO PARA EXTRAER LOS PARAMETROS NECESARIOS PARA GENERAR UN BALANCE GENERAL:
    Comsulta la memoria existente y/o el texto ingresado para extraer los parámetros para generar un balance general:
    usa toda la informacion que tengas disponible para completar lo siguiente:
    - Suma de todos los ingresos registrados : CONSULTA EN LA MEMORIA TODOS LOS INGRESOS QUE SE HAN REGISTRADO Y SUMALOS
    - Suma de todos los gastos registrados: CONSULTA EN LA MEMORIA TODOS LOS GASTOS QUE SE HAN REGISTRADO Y SUMALOS
    - Calcular el balance (ingresos - gastos) : RESTA LOS VALORES QUE OBTUVISTE

    Texto: "{input}"

    Devuelve el resultado en formato:
    "Balance general: Ingresos $(ingresos) - $(gastos) = $(balance)"
    """
)

# Crear chain para balance general
chain_balance = LLMChain(llm = chat, prompt = prompt_balance, memory = memory)

tool_balance = Tool(
    name = "balance_general",
    func = lambda x: chain_balance.run(input = x),
    description = "Calcula el balance general de ingresos y gastos."
)
print("Balance general tool cargado")