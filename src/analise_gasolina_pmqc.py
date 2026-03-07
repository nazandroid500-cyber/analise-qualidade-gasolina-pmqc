import sys
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
import os  # ← ADICIONADO

# Configuração de diretórios ← NOVO
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, '..', 'data')
OUTPUT_DIR = os.path.join(BASE_DIR, '..', 'outputs')
GEO_DIR = os.path.join(BASE_DIR, '..', 'geo')

def carregar_dados(caminho_csv):
    df = pd.read_csv(caminho_csv, sep=';', encoding='latin1')
    print(f"✅ Total de registros carregados: {len(df)}")
    return df

def filtrar_gasolina(df):
    df_gas = df[df['Produto'].str.contains("GASOLINA", na=False)]
    print(f"📊 Registros de gasolina encontrados: {len(df_gas)}")
    return df_gas

def conformidade_por_uf(df_gasolina):
    resumo = (df_gasolina
              .groupby(['Uf', 'Conforme'])
              .size()
              .unstack(fill_value=0))

    resumo['total'] = resumo.sum(axis=1)
    resumo['perc_conforme'] = 100 * resumo.get('Sim', 0) / resumo['total']
    
    return resumo.sort_values('perc_conforme')

def plotar_conformidade(resumo):
    plt.figure(figsize=(10,6))
    plt.bar(resumo.index, resumo['perc_conforme'])
    plt.ylabel('% amostras conformes')
    plt.xlabel('UF')
    plt.title('Conformidade da Gasolina por UF')
    plt.ylim(0,100)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'grafico_conformidade_por_uf.png'), dpi=150)  # ← MUDOU
    plt.close()  # ← BOM PRÁTICA
    print("📈 Gráfico grafico_conformidade_por_uf.png gerado")

def filtrar_ensaio(df, nome_ensaio):
    ensaio_col = df["Ensaio"].astype(str).str.lower()
    df_ensaio = df[ensaio_col.str.contains(nome_ensaio.lower(), na=False)]
    df_ensaio = df_ensaio[df_ensaio["Produto"].str.contains("GASOLINA", na=False)]
    df_ensaio = df_ensaio.copy()
    df_ensaio["Resultado"] = pd.to_numeric(df_ensaio["Resultado"], errors="coerce")
    df_ensaio = df_ensaio.dropna(subset=["Resultado"])
    print(f"🔬 Registros do ensaio '{nome_ensaio}': {len(df_ensaio)}")
    return df_ensaio

def plotar_histograma(df_ensaio, nome_ensaio):
    plt.figure(figsize=(8,6))
    plt.hist(df_ensaio['Resultado'], bins=30)
    plt.xlabel(nome_ensaio)
    plt.ylabel('Frequência')
    plt.title(f'Distribuição do ensaio: {nome_ensaio}')
    plt.grid(alpha=0.3)
    plt.tight_layout()
    nome_arquivo = f"histograma_{nome_ensaio.replace(' ','_')}.png"
    plt.savefig(os.path.join(OUTPUT_DIR, nome_arquivo), dpi=150)  # ← MUDOU
    plt.close()
    print(f"📈 Gráfico {nome_arquivo} gerado")

def media_por_uf(df_ensaio, nome_ensaio):
    media = df_ensaio.groupby('Uf')['Resultado'].mean().sort_values()
    plt.figure(figsize=(10,6))
    plt.bar(media.index, media.values)
    plt.xlabel('UF')
    plt.ylabel(f'Média {nome_ensaio}')
    plt.title(f'Média do ensaio {nome_ensaio} por UF')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    nome_arquivo = f"media_{nome_ensaio.replace(' ','_')}_uf.png"
    plt.savefig(os.path.join(OUTPUT_DIR, nome_arquivo), dpi=150)  # ← MUDOU
    plt.close()
    print(f"📈 Gráfico {nome_arquivo} gerado")

def boxplot_por_uf(df_ensaio, nome_ensaio):
    dados = []
    ufs = sorted(df_ensaio["Uf"].unique())
    for uf in ufs:
        valores = df_ensaio[df_ensaio["Uf"] == uf]["Resultado"]
        dados.append(valores)
    
    plt.figure(figsize=(12,6))
    plt.boxplot(dados, tick_labels=ufs, showfliers=True)
    plt.xlabel("UF")
    plt.ylabel(nome_ensaio)
    plt.title(f"Distribuição de {nome_ensaio} por UF")
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    nome_arquivo = f"boxplot_{nome_ensaio.replace(' ','_')}_uf.png"
    plt.savefig(os.path.join(OUTPUT_DIR, nome_arquivo), dpi=150)  # ← MUDOU
    plt.close()
    print(f"📈 Gráfico {nome_arquivo} gerado")

def mapa_conformidade(resumo):
    estados = gpd.read_file(os.path.join(GEO_DIR, 'brazil-states.geojson'))
    estados["Uf"] = estados["sigla"]
    mapa = estados.merge(resumo, on="Uf")

    plt.figure(figsize=(10,8))

    mapa.plot(
        column="perc_conforme",
        cmap="RdYlGn",
        legend=True,
        vmin=0,   # mínimo da escala = 0%
        vmax=100  # máximo da escala = 100%
    )

    plt.title("Conformidade da gasolina por estado (%)")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, 'mapa_conformidade_brasil.png'), dpi=150)
    plt.close()


def main():  # ← SEM PARÂMETRO
    caminho_csv = os.path.join(DATA_DIR, 'pmqc_2025_06.csv')  # ← CAMINHO FIXO
    
    df = carregar_dados(caminho_csv)
    df_gas = filtrar_gasolina(df)
    resumo = conformidade_por_uf(df_gas)
    
    # Salva CSV com path correto ← MUDOU
    resumo.to_csv(os.path.join(OUTPUT_DIR, 'resumo_conformidade_uf.csv'), sep=';')
    print("💾 Arquivo resumo_conformidade_uf.csv gerado")
    
    plotar_conformidade(resumo)
    mapa_conformidade(resumo)
    
    nome_ensaio = "massa"
    df_ensaio = filtrar_ensaio(df, nome_ensaio)
    
    if len(df_ensaio) > 0:
        plotar_histograma(df_ensaio, nome_ensaio)
        media_por_uf(df_ensaio, nome_ensaio)
        boxplot_por_uf(df_ensaio, nome_ensaio)
    else:
        print("❌ Nenhum registro encontrado para esse ensaio.")

if __name__ == '__main__':
    main()  # ← SEM ARGUMENTO
