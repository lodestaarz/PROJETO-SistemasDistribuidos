import numpy as np
import threading
import time
import pandas as pd
import matplotlib.pyplot as plt


#Estados das células
VAZIO = 0
ARVORE = 1
FOGO = 2


#Atualização de uma faixa da matriz 
def atualizar_faixa(grid, novo, inicio, fim, p_ignicao, p_crescer, rng):
    N = grid.shape[0]
    for i in range(inicio, fim):
        for j in range(N):
            estado = grid[i, j]
            if estado == FOGO:
                novo[i, j] = VAZIO
            elif estado == ARVORE:
                i0, i1 = max(0, i - 1), min(N, i + 2)
                j0, j1 = max(0, j - 1), min(N, j + 2)
                viz = grid[i0:i1, j0:j1]
                if (viz == FOGO).any():
                    novo[i, j] = FOGO
                elif rng.random() < p_ignicao:
                    novo[i, j] = FOGO
                else:
                    novo[i, j] = ARVORE
            else:
                if rng.random() < p_crescer:
                    novo[i, j] = ARVORE
                else:
                    novo[i, j] = VAZIO

#Simulação paralela
def simular_paralelo(N, ITER, NUM_THREADS, p_ignicao, p_crescer, densidade=0.6):
    grid = (np.random.rand(N, N) < densidade).astype(np.int8)
    grid[np.random.rand(N, N) < 0.001] = FOGO
    rngs = [np.random.default_rng(seed=i) for i in range(NUM_THREADS)]

    inicio_total = time.time()

    for _ in range(ITER):
        novo = np.zeros_like(grid)
        threads = []
        passo = N // NUM_THREADS

        for t in range(NUM_THREADS):
            ini = t * passo
            fim = N if t == NUM_THREADS - 1 else (t + 1) * passo
            thr = threading.Thread(
                target=atualizar_faixa,
                args=(grid, novo, ini, fim, p_ignicao, p_crescer, rngs[t])
            )
            threads.append(thr)
            thr.start()

        for thr in threads:
            thr.join()

        grid = novo

    fim_total = time.time()
    return fim_total - inicio_total


#Execução e medição de desempenho
def executar_experimentos(tamanho, threads_list, ITER, reps, p_ignicao, p_crescer):
    resultados = []
    for N in tamanho:
        for t in threads_list:
            for r in range(reps):
                tempo = simular_paralelo(N, ITER, t, p_ignicao, p_crescer)
                resultados.append([N, t, r + 1, tempo])
                print(f" N={N} Threads={t} Exec={r+1} Tempo={tempo:.4f}s")
    df = pd.DataFrame(resultados, columns=["tamanho", "threads", "execucao", "tempo_s"])
    return df


#Teste automático
print("Executando simulação paralela ")

df_resultados = executar_experimentos(
    tamanho=[100, 200, 300],
    threads_list=[1, 2, 4],
    ITER=100,
    reps=3,
    p_ignicao=0.0005,
    p_crescer=0.01
)


#Cálculo da média
media = df_resultados.groupby(["tamanho", "threads"], as_index=False)["tempo_s"].mean()


#Gráfico - Tempo médio x Threads
plt.figure(figsize=(8,5))
for N in media["tamanho"].unique():
    subset = media[media["tamanho"] == N]
    plt.plot(subset["threads"], subset["tempo_s"], marker="o", label=f"{N}x{N}")
plt.xlabel("Número de Threads")
plt.ylabel("Tempo médio (s)")
plt.title("Desempenho Paralelo - Simulação de Incêndio Florestal")
plt.legend()
plt.grid(True)
plt.show()

#Exibe a tabela resumo
from IPython.display import display
display(media)