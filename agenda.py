import sqlite3
from datetime import date

DB = 'banco.db'

def init_agenda():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS compromissos
                 (id INTEGER PRIMARY KEY,
                  data TEXT,
                  hora_inicio TEXT,
                  duracao INTEGER,
                  tipo TEXT,
                  cliente_id INTEGER,
                  titulo TEXT)''')
    conn.commit()
    conn.close()

def add_compromisso(data, hora_inicio, duracao, tipo, cliente_id=None, titulo=""):
    conn = sqlite3.connect(DB)
    conn.execute("INSERT INTO compromissos (data, hora_inicio, duracao, tipo, cliente_id, titulo) VALUES (?,?,?,?,?,?)",
                 (data, hora_inicio, duracao, tipo, cliente_id, titulo))
    conn.commit()
    conn.close()

def get_compromissos(data):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT id, data, hora_inicio, duracao, tipo, cliente_id, titulo FROM compromissos WHERE data=? ORDER BY hora_inicio", (data,))
    rows = c.fetchall()
    conn.close()
    lista = []
    for r in rows:
        lista.append({
            'id': r[0], 'data': r[1], 'hora_inicio': r[2], 'duracao': r[3],
            'tipo': r[4], 'cliente_id': r[5], 'titulo': r[6]
        })
    return lista

def deletar_compromisso(id_comp):
    conn = sqlite3.connect(DB)
    conn.execute("DELETE FROM compromissos WHERE id=?", (id_comp,))
    conn.commit()
    conn.close()

def hora_para_minutos(h):
    # h = "17:15"
    hh, mm = map(int, h.split(":"))
    return hh*60 + mm

# Cores clarinhas
CORES = {
    'visita': '#dbeafe', # azul clarinho
    'viagem': '#e5e7eb', # cinza clarinho
    'evento': '#ede9fe', # roxo clarinho
    'outros': '#dcfce7', # verde clarinho
    'almoco': '#f5e6d3' # marrom clarinho
}

def update_horario(id_comp, novo_horario):
    conn = sqlite3.connect(DB)
    conn.execute("UPDATE compromissos SET hora_inicio=? WHERE id=?", (novo_horario, id_comp))
    conn.commit()
    conn.close()