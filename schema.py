import sqlite3

# Conectar a tu base de datos llena
conn = sqlite3.connect("hackathon.db")

# Extraer solo las sentencias DDL (CREATE TABLE, INDEX, VIEW)
with open("schema.sql", "w", encoding="utf-8") as f:
  for line in conn.iterdump():
    if line.startswith("CREATE"):
      f.write(f"{line}\n")

conn.close()
print(
    "✅ ¡Archivo 'schema.sql' generado con éxito! Solo contiene la estructura"
    " vacía."
)
