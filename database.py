import sqlite3
import pandas as pd

DB = 'banco.db'

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS clientes
                 (id INTEGER PRIMARY KEY, nome TEXT, endereco TEXT, whatsapp TEXT, pagamento TEXT, obs TEXT, lat REAL, lng REAL)''')
    conn.commit()
    conn.close()

def get_clientes():
    conn = sqlite3.connect(DB)
    df = pd.read_sql_query("SELECT * FROM clientes ORDER BY nome", conn)
    conn.close()
    return df

def get_cliente_dict(cliente_id):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM clientes WHERE id=?", (cliente_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def salvar_cliente(nome, endereco, whatsapp, pagamento, obs):
    conn = sqlite3.connect(DB)
    conn.execute("INSERT INTO clientes (nome, endereco, whatsapp, pagamento, obs) VALUES (?,?,?,?,?)",
                 (nome, endereco, whatsapp, pagamento, obs))
    conn.commit()
    conn.close()

def atualizar_cliente(cliente_id, nome, endereco, whatsapp, pagamento, obs):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE clientes SET nome=?, endereco=?, whatsapp=?, pagamento=?, obs=? WHERE id=?",
                 (nome, endereco, whatsapp, pagamento, obs, cliente_id))
    conn.commit()
    conn.close()

def atualizar_local(cliente_id, lat, lng):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE clientes SET lat=?, lng=? WHERE id=?", (lat, lng, cliente_id))
    conn.commit()
    conn.close()

def deletar_cliente(cliente_id):
    conn = sqlite3.connect(DB)
    conn.execute("DELETE FROM clientes WHERE id=?", (cliente_id,))
    conn.commit()
    conn.close()