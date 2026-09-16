"""Busca TLEs no Celestrak com timeout, retry e validacao antes de gravar.

O Celestrak responde HTTP 200 mesmo em caso de erro (ex.: o corpo
'Invalid query: ...' de uma unica linha), entao checar o status code nao
basta: o conteudo precisa ser validado antes de virar JSON.
"""

import json
import sys
import time

import requests

URL = 'https://celestrak.org/NORAD/elements/gp.php?GROUP={grupo}&FORMAT=tle'

# (conectar, ler) em segundos. O modo de falha mais comum e a conexao
# pendurar, entao o timeout de connect e curto de proposito.
TIMEOUT = (10, 30)

TENTATIVAS = 4
BACKOFF = 5  # segundos ate a proxima tentativa; dobra a cada falha

# As duas linhas de orbita de um TLE tem largura fixa, com o digito
# verificador na ultima coluna.
LARGURA_TLE = 69


class TLEInvalido(Exception):
    """A resposta do Celestrak nao e um conjunto de TLEs utilizavel."""


def _checksum(linha):
    """Digito verificador do TLE: soma dos digitos (com '-' valendo 1) mod 10."""
    total = 0
    for caractere in linha[:LARGURA_TLE - 1]:
        if caractere.isdigit():
            total += int(caractere)
        elif caractere == '-':
            total += 1
    return total % 10


def _valida_linha_orbita(linha, prefixo):
    if not linha.startswith(prefixo):
        raise TLEInvalido(f'esperava linha comecando com {prefixo!r}, veio {linha[:20]!r}')

    # Pega download cortado no meio de uma linha, que sozinho passaria no
    # teste de prefixo.
    if len(linha) != LARGURA_TLE:
        raise TLEInvalido(
            f'linha com {len(linha)} caracteres, esperava {LARGURA_TLE} '
            f'(truncada?): {linha[:30]!r}'
        )

    esperado = _checksum(linha)
    if not linha[-1].isdigit() or int(linha[-1]) != esperado:
        raise TLEInvalido(
            f'digito verificador nao confere (esperava {esperado}, '
            f'veio {linha[-1]!r}): {linha[:30]!r}'
        )


def _parse(tle_data, minimo, filtro=None):
    linhas = [linha.strip() for linha in tle_data.strip().split('\n')]

    if len(linhas) % 3 != 0:
        raise TLEInvalido(
            f'esperava um multiplo de 3 linhas, veio {len(linhas)}; '
            f'primeira linha: {linhas[0][:120]!r}'
        )

    tles = []
    for i in range(0, len(linhas), 3):
        nome, linha1, linha2 = linhas[i], linhas[i + 1], linhas[i + 2]

        try:
            _valida_linha_orbita(linha1, '1 ')
            _valida_linha_orbita(linha2, '2 ')
        except TLEInvalido as erro:
            raise TLEInvalido(f'bloco {i // 3} ({nome[:40]!r}): {erro}') from erro

        if filtro is None or filtro(nome):
            tles.append([nome, linha1, linha2])

    # Pega download truncado que por acaso terminou num multiplo de 3, e
    # filtro que deixou de casar porque o Celestrak renomeou os satelites.
    if len(tles) < minimo:
        raise TLEInvalido(
            f'veio so {len(tles)} satelites, esperava ao menos {minimo} '
            f'(download truncado ou filtro sem correspondencia?)'
        )

    return tles


def buscar(grupo, minimo, filtro=None):
    url = URL.format(grupo=grupo)
    erro_final = None

    for tentativa in range(1, TENTATIVAS + 1):
        try:
            resposta = requests.get(url, timeout=TIMEOUT)
            resposta.raise_for_status()
            return _parse(resposta.text, minimo, filtro)
        except requests.HTTPError as erro:
            # 4xx nao melhora com retry, exceto 429, que e throttling.
            status = erro.response.status_code
            if 400 <= status < 500 and status != 429:
                raise
            erro_final = erro
        except (requests.RequestException, TLEInvalido) as erro:
            erro_final = erro

        print(
            f'tentativa {tentativa}/{TENTATIVAS} falhou: {erro_final}',
            file=sys.stderr,
        )
        if tentativa == TENTATIVAS:
            raise erro_final
        time.sleep(BACKOFF * 2 ** (tentativa - 1))


def salvar(tles, filename):
    with open(filename, 'w') as file:
        json.dump(tles, file, indent=4)
