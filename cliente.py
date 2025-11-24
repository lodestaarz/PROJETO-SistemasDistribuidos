import socket
import pickle
import struct
import random
import sys
import time

#IP e porta do servidor
HOST = '127.0.0.1'
PORTA = 50000

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

def passo_local(submatriz, top, bottom, p_ign, p_cres):

    linhas = len(submatriz)
    Nloc = len(submatriz[0])

    #Cria nova matriz resultado
    novo = [[0]*Nloc for _ in range(linhas)]
    ext = [top[0][:]] + [row[:] for row in submatriz] + [bottom[0][:]]

    #Percorre todas as células
    for i in range(linhas):
        for j in range(Nloc):
            estado = ext[i+1][j] 

            if estado == 2:
                novo[i][j] = 0
 
            elif estado == 1:
                queimando = False

                for ii in range(i, i+3):
                    for jj in range(max(0, j-1), min(Nloc, j+2)):
                        if ext[ii][jj] == 2:  
                            queimando = True
                            break
                    if queimando:
                        break

                if queimando or random.random() < p_ign:
                    novo[i][j] = 2  
                else:
                    novo[i][j] = 1  

            else:
                novo[i][j] = 1 if random.random() < p_cres else 0

    return novo


if __name__ == "__main__":

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    #Tenta conectar ao servidor
    try:
        s.connect((HOST, PORTA))
    except Exception as e:
        print("[Cliente] Não conseguiu conectar:", e)
        sys.exit(1)

    #Recebe dados enviados pelo servidor
    inicial = receber_obj(s)
    if inicial is None:
        print("[Cliente] Não recebeu dados iniciais do servidor.")
        s.close()
        sys.exit(1)

    try:
        ini = inicial['ini']; fim = inicial['fim']; N = inicial['N']
        ITER = inicial['ITER']
        p_ign = inicial['p_ignicao']; p_cres = inicial['p_crescer']
        sub = inicial['sub'] 
    except KeyError as e:
        print("[Cliente] Payload inicial faltando chave:", e)
        s.close()
        sys.exit(1)

    print(f"[Cliente] Recebi: matriz {ini}:{fim} (linhas={len(sub)}) do servidor")

    #Loop da simulação
    try:
        for it in range(ITER):

            bordas = receber_obj(s)
            if bordas is None:
                print("[Cliente] Servidor fechou a conexão.")
                break

            top = bordas['top']
            bottom = bordas['bottom']

            new = passo_local(sub, top, bottom, p_ign, p_cres)

            enviar_obj(s, {'sub': new})

            sub = new

            if (it+1) % 50 == 0:
                print(f"[Cliente] Iteração {it+1}/{ITER} enviada")

    except ConnectionResetError:
        print("[Cliente] Conexão resetada pelo servidor")

    finally:
        s.close() 
        print("[Cliente] Finalizado")
