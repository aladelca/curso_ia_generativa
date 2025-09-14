import os
from dotenv import load_dotenv
from langchain_community.llms import OpenAI
from langchain_community.utilities.sql_database import SQLDatabase
import pandas as pd
import re

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')

def get_mysql_uri():
    return f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}"

def get_schema_summary(db):
    """Obtener un resumen del esquema de la base de datos"""
    try:
        tables = db.get_usable_table_names()
        schema_summary = "Tablas disponibles: " + ", ".join(tables)  # Solo las primeras 10 tablas
        return schema_summary
    except:
        return "Base de datos MySQL con tablas de productos, ventas, clientes, etc."

def generate_sql_query(user_question, schema_summary, llm):
    """Generar consulta SQL usando OpenAI directamente"""
    prompt = f"""
Eres un experto en SQL para MySQL. Genera SOLO la consulta SQL para responder la pregunta.
Reglas:
- SOLO consultas SELECT (descriptivas)
- Una sola línea de SQL
- Sin explicaciones, sin comentarios
- Si no es posible con SELECT, responde: 'ERROR: Solo se permiten consultas descriptivas.'

Esquema: {schema_summary}

Pregunta: {user_question}
SQL:"""
    
    response = llm.invoke(prompt)
    sql_query = response.strip()
    
    # Limpiar la respuesta para obtener solo el SQL
    if sql_query.lower().startswith('select'):
        return sql_query
    elif 'select' in sql_query.lower():
        # Extraer solo la parte SELECT
        match = re.search(r'(SELECT.*?(?:;|$))', sql_query, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).rstrip(';').strip()
    
    return sql_query

def main():
    db_uri = get_mysql_uri()
    db = SQLDatabase.from_uri(db_uri)
    llm = OpenAI(openai_api_key=OPENAI_API_KEY, temperature=0)
    
    # Obtener resumen del esquema una sola vez
    schema_summary = get_schema_summary(db)
    
    print("Asistente conversacional para consultas SQL. Escribe 'salir' para terminar.")
    chat_history = []
    
    while True:
        user_input = input("Usuario: ")
        if user_input.strip().lower() in ["salir", "exit", "quit"]:
            print("Adiós!")
            break
            
        try:
            sql_query = generate_sql_query(user_input, schema_summary, llm)
            print(f"Consulta generada:\n{sql_query}")
            
            # Ejecutar la consulta y mostrar como DataFrame
            if sql_query.lower().startswith('select'):
                try:
                    df = pd.read_sql(sql_query, db._engine)
                    print("Resultado (DataFrame):")
                    print(df)
                except Exception as ex:
                    print(f"Error al ejecutar la consulta SQL: {ex}")
            else:
                print(sql_query)  # Mostrar mensaje de error
                
            chat_history.append((user_input, sql_query))
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
