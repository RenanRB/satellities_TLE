"""Monta os arquivos GNSS a partir do menor numero possivel de requisicoes.

O GROUP=gnss do Celestrak e um superset exato de gps-ops, glo-ops, galileo,
beidou e sbas, mais os satelites NavIC, entao uma requisicao rende seis
constelacoes de navegacao. Como a maioria das falhas deste projeto e timeout
do Celestrak, reduzir requisicoes reduz falhas na mesma proporcao, e de
quebra todas as constelacoes saem da mesma epoca.

Os satelites SBAS ja vem dentro dessa mesma resposta, com os rotulos PRN
intactos, entao nao ha requisicao extra para eles: quem nao casa com nenhuma
constelacao de navegacao e, por construcao do grupo, augmentacao.

Os arquivos por constelacao continuam separados: cada modelo de drone aceita
um subconjunto das constelacoes, entao o consumidor busca so o que precisa.
"""

import json
import os
import sys

from tle_fetch import buscar, salvar

DESTINO = os.path.join('data', 'gnss')

# Constelacoes de navegacao, todas extraidas da unica requisicao ao gnss.
# (chave, rotulo, regra de nome, minimo de satelites)
CONSTELACOES = [
    ('gps',     'GPS (EUA)',        lambda n: n.startswith('GPS '),            24),
    ('glo',     'GLONASS (Russia)', lambda n: n.startswith('COSMOS '),         20),
    ('galileo', 'Galileo (UE)',     lambda n: 'GALILEO' in n.upper(),          24),
    ('beidou',  'BeiDou (China)',   lambda n: n.startswith('BEIDOU'),          40),
    ('qzss',    'QZSS (Japao)',     lambda n: n.startswith('QZS-'),             4),
    ('navic',   'NavIC (India)',    lambda n: n.startswith(('IRNSS', 'NVS-')),  5),
]

# Piso dos satelites de augmentacao, que sao a sobra da classificacao.
MINIMO_SBAS = 10

# Piso do superset. Abaixo disso a resposta veio incompleta.
MINIMO_TOTAL = 150


def classificar(tles):
    """Separa os TLEs por constelacao e devolve tambem o que nao casou."""
    grupos = {chave: [] for chave, _, _, _ in CONSTELACOES}
    sobras = []

    for tle in tles:
        nome = tle[0]
        for chave, _, regra, _ in CONSTELACOES:
            if regra(nome):
                grupos[chave].append(tle)
                break
        else:
            sobras.append(tle)

    return grupos, sobras


saida = {}

tles = buscar('gnss', MINIMO_TOTAL)
grupos, sobras = classificar(tles)

for chave, rotulo, _, minimo in CONSTELACOES:
    encontrados = grupos[chave]
    if len(encontrados) < minimo:
        sys.exit(
            f'ERRO: {rotulo} veio com {len(encontrados)} satelites, esperava ao '
            f'menos {minimo}. O Celestrak pode ter renomeado os satelites e '
            f'quebrado a regra de classificacao.'
        )
    saida[chave] = encontrados
    print(f'{rotulo}: {len(encontrados)} satelites', file=sys.stderr)

# O que sobra da classificacao sao os GEO de augmentacao (WAAS, EGNOS, GAGAN,
# SDCM), que o Celestrak ja entrega aqui com o rotulo PRN. Os nomes vao para o
# log a cada execucao: e por ali que se percebe o Celestrak incluindo uma rede
# nova no grupo.
if len(sobras) < MINIMO_SBAS:
    sys.exit(
        f'ERRO: SBAS veio com {len(sobras)} satelites, esperava ao menos '
        f'{MINIMO_SBAS}. O Celestrak pode ter mudado o conteudo do GROUP=gnss.'
    )
saida['sbas'] = sobras
print(f'SBAS (augmentacao): {len(sobras)} satelites', file=sys.stderr)
for tle in sobras:
    print(f'    {tle[0]}', file=sys.stderr)

os.makedirs(DESTINO, exist_ok=True)
for chave, tles_da_chave in saida.items():
    salvar(tles_da_chave, os.path.join(DESTINO, f'{chave}.json'))

# Fonte unica, para quem preferir um arquivo so. Sem timestamp de proposito:
# qualquer campo que mude a cada execucao geraria um commit por rodada.
with open(os.path.join(DESTINO, 'all.json'), 'w') as arquivo:
    json.dump(saida, arquivo, indent=4)

print(f'Total: {sum(len(v) for v in saida.values())} satelites em '
      f'{len(saida)} arquivos', file=sys.stderr)
