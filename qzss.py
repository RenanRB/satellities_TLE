"""Atualiza os TLEs do QZSS (Michibiki, Japao) a partir do Celestrak.

O Celestrak nao publica um GROUP so de QZSS: os satelites aparecem dentro
de 'gnss' (e tambem de 'sbas'), com nome no formato 'QZS-N (QZSS/PRN NNN)'.
Por isso buscamos o grupo gnss inteiro e filtramos pelo nome, o que faz
novos lancamentos entrarem sozinhos.
"""

from tle_fetch import buscar, salvar

# Piso de seguranca: hoje sao 5 operacionais (QZS-1R, 2, 3, 4 e 6).
MINIMO_SATELITES = 4


def e_qzss(nome):
    return nome.upper().startswith('QZS-')


tles = buscar('gnss', MINIMO_SATELITES, filtro=e_qzss)
salvar(tles, 'new_qzss.json')
