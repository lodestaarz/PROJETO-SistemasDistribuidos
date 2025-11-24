import numpy as np
import time
import matplotlib.pyplot as plt
import pandas as pd

p_ignicao = 0.0005
p_crescer = 0.01

def passo_forest_fire(grid):
    N = grid.shape[0]
    novo = grid.copy()

    for i in range(N):
        for j in range(N):
            estado = grid[i, j] #Estado atual da célula: 0 = vazio, 1 = árvore, 2 = queimando
            if estado == 2:
                novo[i, j] = 0
            elif estado == 1:
                i0 = max(0, i-1); i1 = min(N, i+2)
                j0 = max(0, j-1); j1 = min(N, j+2)
                viz = grid[i0:i1, j0:j1]
                if (viz == 2).any():
                    novo[i, j] = 2
                elif np.random.rand() < p_ignicao:
                    novo[i, j] = 2
                else:
                    novo[i, j] = 1
            else:
                if np.random.rand() < p_crescer:
                    novo[i, j] = 1
                else:
                    novo[i, j] = 0
    return novo


def simular(N, ITER):
    np.random.seed(0)
    grid = (np.random.rand(N, N) < 0.6).astype(np.int8)
    grid[np.random.rand(N, N) < 0.001] = 2

    t0 = time.time()
    for _ in range(ITER):
        grid = passo_forest_fire(grid)
    tf = time.time()
    return tf - t0


#Tamanhos das matrizes a testar
tamanhos = [100, 200, 300]
ITER = 100
reps = 3

resultados = []

for N in tamanhos:
    for r in range(reps):
        tempo = simular(N, ITER)
        resultados.append([N, r + 1, tempo])
        print(f"N={N} Exec={r+1} Tempo={tempo:.4f}s")

df = pd.DataFrame(resultados, columns=["tamanho", "execucao", "tempo_s"])

media = df.groupby("tamanho")["tempo_s"].mean().reset_index()

plt.figure(figsize=(8,5))
plt.plot(media["tamanho"], media["tempo_s"], marker="o")
plt.xlabel("Tamanho da Matriz")
plt.ylabel("Tempo médio (s)")
plt.title("Desempenho Sequencial - Simulação de Incêndio Florestal")
plt.grid(True)
plt.show()

df