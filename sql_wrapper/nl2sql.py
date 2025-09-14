import os
import openai
import mysql.connector
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MYSQL_HOST = os.getenv('MYSQL_HOST')
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE')

openai.api_key = OPENAI_API_KEY

def natural_language_to_sql(nl_query, db_schema):
    """
    Use OpenAI API to convert a natural language query to SQL.
    Only allows descriptive (SELECT) queries.
    The schema of all tables is provided so the model can infer the correct table.
    """
    prompt = f"""
    You are an assistant that converts natural language questions into SQL SELECT queries for a MySQL database. 
    Only generate SELECT statements. If the question is not descriptive or cannot be answered with a SELECT, respond with 'ERROR: Only descriptive queries are allowed.'

    Database schema:
    {db_schema}

    Question: {nl_query}
    SQL:"""
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=150,
        temperature=0,
        stop=["#", "\n\n"]
    )
    sql = response.choices[0].text.strip()
    if not sql.lower().startswith('select'):
        raise ValueError('ERROR: Only descriptive queries are allowed.')
    return sql

def get_db_schema(cursor):
    """
    Returns the schema of all tables in the database as a string.
    """
    cursor.execute("SHOW TABLES")
    tables = [row[0] for row in cursor.fetchall()]
    schema_str = ""
    for table in tables:
        cursor.execute(f"DESCRIBE {table}")
        columns = cursor.fetchall()
        schema_str += f"Table: {table}\n"
        for col in columns:
            schema_str += f"  {col[0]} {col[1]}\n"
        schema_str += "\n"
    return schema_str

def execute_sql_query(sql):
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )
    cursor = conn.cursor()
    cursor.execute(sql)
    results = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    cursor.close()
    conn.close()
    return columns, results

def main():
    nl_query = input("Pregunta en lenguaje natural: ")
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        cursor = conn.cursor()
        db_schema = get_db_schema(cursor)
        cursor.close()
        conn.close()
        sql = natural_language_to_sql(nl_query, db_schema)
        print(f"Consulta generada: {sql}")
        columns, results = execute_sql_query(sql)
        print("Resultados:")
        print(columns)
        for row in results:
            print(row)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
