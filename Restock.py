import streamlit as st
import pandas as pd
import math
import numpy as np
from sqlalchemy import create_engine
import datetime

# Calcular reposição
def calcular_reposicao(dias, data, qtd_minima):
    reposicao = []

    loja_map = {
        '03': 'ASA NORTE',
        '04': 'CEILANDIA',
        '05': 'GAMA',
        '06': 'SOF',
        '07': 'PLANALTINA'
    }

    for idx, row in data.iterrows():
        cd_loja = row['cd_loja']
        num_fab = row['num_fab']
        minimo = row['est_minfra']
        estoque = row['estoque']

        if cd_loja not in loja_map:
            reposicao.append((f'{num_fab} - Loja {cd_loja}', 'CD'))
            continue

        if minimo == 0 and estoque == 0:
            reposicao.append((f'{num_fab} - {loja_map[cd_loja]}', qtd_minima))
        elif ((minimo / 30) * dias) - estoque <= 0:
            reposicao.append((f'{num_fab} - {loja_map[cd_loja]}', 'Estoque OK'))
        else:
            repor = ((minimo / 30) * dias) - estoque
            repor = math.ceil(repor / qtd_minima) * qtd_minima
            reposicao.append((f'{num_fab} - {loja_map[cd_loja]}', repor))
    
    return reposicao

# Definir cor do estoque
def colorir_estoque(dias):
    if dias < 5:
        return 'background-color: red'
    elif dias <= 10:
        return 'background-color: yellow'
    else:
        return 'background-color: green'

# Carregar dados do banco de dados
def carregar_dados():
    conn_string = "postgresql://pecista:postgres123@srvdados:5432/postgres"
    engine = create_engine(conn_string)

    query = """
        select cd_loja, produto.num_fab, est_minfra, estoque,
            CASE
                WHEN est_minfra <> 0 THEN ROUND((estoque*30/(est_minfra)),2)
                ELSE NULL
            END as dias
        from "H-1".prd_loja
        join "D-1".produto ON produto.codpro = prd_loja.codpro
        and cd_loja not in ('02', '08')
        ORDER BY cd_loja asc;
    """
    data = pd.read_sql(query, engine)

    return data

# Carregar produtos do CSV
def carregar_produtos_csv():
    try:
        produtos = pd.read_csv(r'C:\Users\mikael.santos\Desktop\Reposição\Produtos.csv')
        return produtos
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo CSV: {e}")
        return pd.DataFrame()

def main():
    st.title("Reposição de Estoque")

    dias = st.number_input("Reposição para quantos dias?", min_value=1, step=1)
    qtd_minima = st.number_input("Quantidade mínima de envio?", min_value=1, step=1)

    data = carregar_dados()

    # Carregar produtos do CSV
    produtos_csv = carregar_produtos_csv()

    if not produtos_csv.empty:
        produtos_v = produtos_csv[produtos_csv['ATIVO']]['PRODUTO'].tolist()
        data_filtrada = data[data['num_fab'].isin(produtos_v)]
    else:
        st.error("Nenhum produto ativo encontrado no CSV.")
        data_filtrada = data

    if st.button("Calcular Reposição"):
        reposicoes = calcular_reposicao(dias, data_filtrada, qtd_minima)

        st.subheader("Resultados de Reposição:")
        df_result = pd.DataFrame(reposicoes, columns=["Loja", "Reposição"])
        df_result['Estoque Atual'] = data_filtrada['estoque'].values
        df_result['DIAS'] = data_filtrada['dias'].values

        styled_df = df_result.style.applymap(lambda x: colorir_estoque(x) if isinstance(x, (int, float)) else '', subset=['DIAS'])
        styled_df = styled_df.format({'Estoque Atual': "{:.0f}", 'DIAS': "{:.1f}"})

        st.dataframe(styled_df)

if __name__ == "__main__":
    main()
