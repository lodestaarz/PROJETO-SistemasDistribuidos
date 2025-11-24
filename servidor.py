import socket
import threading
import pickle
import struct
import random
import time

HOST = '127.0.0.1'
PORTA = 50000

try:
    NUM_CLIENTES = int(input("Quantos nós deseja usar? (2,3 ou 4) [3]: ") or "3")
except Exception:
    NUM_CLIENTES = 3

N = 300    #Matriz 300x300 // Trocamos o esse numero para ver a escalabilidade
ITER = 300

p_ignicao = 0.0005
p_crescer = 0.01

def enviar_obj(sock, obj):
    dados = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
    tamanho = struct.pack('!Q', len(dados))
    sock.sendall(tamanho + dados)

def recv_all(sock, n):
    buf = b''
    while len(buf) < n:
        parte = sock.recv(n - len(buf))
        if not parte:
            return None
        buf += parte
    return buf

def receber_obj(sock):
    header = recv_all(sock, 8)
    if not header:
        return None
    tamanho = struct.unpack('!Q', header)[0]
    dados = recv_all(sock, tamanho)
    if dados is None:
        return None
    return pickle.loads(dados)

#Matrizes auxiliares 
def criar_grid_aleatorio(N, prob_arvore=0.6, prob_queimando=0.001):
    grid = []
    for i in range(N):
        linha = []
        for j in range(N):
            if random.random() < prob_queimando:
                linha.append(2)
            elif random.random() < prob_arvore:
                linha.append(1)
            else:
                linha.append(0)
        grid.append(linha)
    return grid

def copiar_submatriz(grid, ini, fim):
    return [row[:] for row in grid[ini:fim]]

def colar_submatriz(grid, bloco, ini, fim):
    for idx, linha in enumerate(bloco):
        grid[ini + idx] = linha[:]

def aceitar_conexoes(servidor_socket):
    lista = []
    while len(lista) < NUM_CLIENTES:
        conn, addr = servidor_socket.accept()
        print(f"[Servidor] Cliente conectado: {addr}")
        lista.append((conn, addr))
    return lista

def main():
    random.seed(0)

    servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind((HOST, PORTA))
    servidor.listen()
    print(f"[Servidor] Aguardando {NUM_CLIENTES} clientes em {HOST}:{PORTA}...")

    conexoes = aceitar_conexoes(servidor)

    grid = criar_grid_aleatorio(N)

    #Dividir linhas entre clientes
    def dividir(total):
        passo = total // NUM_CLIENTES
        faixas = []
        for t in range(NUM_CLIENTES):
            ini = t * passo
            fim = total if t == NUM_CLIENTES - 1 else (t + 1) * passo
            faixas.append((ini, fim))
        return faixas

    faixas = dividir(N)

    clientes = []
    for (conn, addr), (ini, fim) in zip(conexoes, faixas):
        sub = copiar_submatriz(grid, ini, fim)
        payload = {
            'ini': ini, 'fim': fim, 'N': N,
            'ITER': ITER,
            'p_ignicao': p_ignicao, 'p_crescer': p_crescer,
            'sub': sub
        }
        enviar_obj(conn, payload)
        clientes.append({'conn': conn, 'addr': addr, 'ini': ini, 'fim': fim})
        print(f"[Servidor] Enviada faixa {ini}:{fim} (matriz {N}x{N}) para {addr}")

    #Medição de tempo por iteração
    tempos_iter = []
    t0 = time.time()
    marcos = [50, 100, 150, 200, 250, 300]

    try:
        for it in range(ITER):
            it_ini = time.time()

            for cli in clientes:
                ini, fim = cli['ini'], cli['fim']

                linha_sup = [0]*N if ini == 0 else grid[ini-1][:]
                linha_inf = [0]*N if fim == N else grid[fim][:]

                enviar_obj(cli['conn'], {
                    'top': [linha_sup], 'bottom': [linha_inf]
                })

            resultados = []
            for cli in clientes:
                obj = receber_obj(cli['conn'])
                if obj is None:
                    raise ConnectionError(f"[Servidor] Cliente {cli['addr']} desconectou.")
                if 'sub' not in obj:
                    raise KeyError(f"[Servidor] Objeto recebido sem 'sub' de {cli['addr']}: {list(obj.keys())}")
                resultados.append(obj['sub'])

            for (ini, fim), bloco in zip(faixas, resultados):
                colar_submatriz(grid, bloco, ini, fim)

            it_fim = time.time()
            tempo_it = (it_fim - it_ini) * 1000
            tempos_iter.append(tempo_it)
            print(f"[Iteração {it+1}] Tempo: {tempo_it:.2f} ms")

            if (it+1) in marcos:
                tempo_acumulado = sum(tempos_iter)
                print(f"\n>>> Tempo até {it+1}/{ITER}: {tempo_acumulado:.2f} ms\n")

    except (ConnectionError, ConnectionResetError) as e:
        print(f"[Servidor] Erro de conexão: {e}")
    except Exception as e:
        print(f"[Servidor] Erro inesperado: {type(e).__name__}: {e}")
    finally:
        tf = time.time()
        tempo_total = (tf - t0) * 1000
        print(f"\n[Distribuído] Tempo total: {tempo_total:.2f} ms\n")

        try:
            with open("tempos_iter_servidor.txt", "w") as f:
                for t in tempos_iter:
                    f.write(f"{t}\n")
            print("[Servidor] Tempos salvos em tempos_iter_servidor.txt")
        except Exception as e:
            print("[Servidor] Falha ao salvar tempos:", e)

        for cli in clientes:
            try:
                cli['conn'].close()
            except Exception:
                pass
        servidor.close()

if __name__ == "__main__":
    main()
