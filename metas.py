import sqlite3
from datetime import date, timedelta

DB = 'banco.db'

def init_metas():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS visitas
                 (id INTEGER PRIMARY KEY, cliente_id INTEGER, data TEXT, valor REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS config
                 (chave TEXT PRIMARY KEY, valor TEXT)''')
    c.execute("INSERT OR IGNORE INTO config (chave, valor) VALUES ('meta_diaria_clientes', '15')")
    c.execute("INSERT OR IGNORE INTO config (chave, valor) VALUES ('meta_diaria_vendas', '500')")
    c.execute("INSERT OR IGNORE INTO config (chave, valor) VALUES ('meta_semanal_clientes', '80')")
    c.execute("INSERT OR IGNORE INTO config (chave, valor) VALUES ('meta_semanal_vendas', '2500')")
    conn.commit()
    conn.close()

def get_config(chave):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT valor FROM config WHERE chave=?", (chave,))
    r = c.fetchone()
    conn.close()
    return r[0] if r else "0"

def set_config(chave, valor):
    conn = sqlite3.connect(DB)
    conn.execute("INSERT OR REPLACE INTO config (chave, valor) VALUES (?,?)", (chave, str(valor)))
    conn.commit()
    conn.close()

def registrar_visita(cliente_id, valor=0):
    hoje = date.today().isoformat()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id FROM visitas WHERE cliente_id=? AND data=?", (cliente_id, hoje))
    existe = c.fetchone()
    if existe:
        conn.execute("UPDATE visitas SET valor=? WHERE cliente_id=? AND data=?", (valor, cliente_id, hoje))
    else:
        conn.execute("INSERT INTO visitas (cliente_id, data, valor) VALUES (?,?,?)", (cliente_id, hoje, valor))
    conn.commit()
    conn.close()

def deletar_visita_hoje(cliente_id):
    hoje = date.today().isoformat()
    conn = sqlite3.connect(DB)
    conn.execute("DELETE FROM visitas WHERE cliente_id=? AND data=?", (cliente_id, hoje))
    conn.commit()
    conn.close()

def get_visitas_hoje():
    hoje = date.today().isoformat()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*), COALESCE(SUM(valor),0) FROM visitas WHERE data=?", (hoje,))
    qtd, total = c.fetchone()
    conn.close()
    return qtd or 0, total or 0

def get_visitas_semana():
    hoje = date.today()
    inicio = (hoje - timedelta(days=hoje.weekday())).isoformat()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*), COALESCE(SUM(valor),0) FROM visitas WHERE data>=?", (inicio,))
    qtd, total = c.fetchone()
    conn.close()
    return qtd or 0, total or 0

def ja_visitou_hoje(cliente_id):
    hoje = date.today().isoformat()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM visitas WHERE cliente_id=? AND data=?", (cliente_id, hoje))
    r = c.fetchone()[0]
    conn.close()
    return r > 0

def get_valor_visita_hoje(cliente_id):
    hoje = date.today().isoformat()
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT valor FROM visitas WHERE cliente_id=? AND data=?", (cliente_id, hoje))
    r = c.fetchone()
    conn.close()
    return r[0] if r else 0.0