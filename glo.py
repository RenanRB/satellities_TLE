"""Atualiza os TLEs do GLONASS a partir do Celestrak."""

from tle_fetch import buscar, salvar

# Piso de seguranca: hoje a constelacao publica bem mais que isso, entao um
# valor abaixo daqui significa resposta truncada, nao satelite desativado.
MINIMO_SATELITES = 20

tles = buscar('glo-ops', MINIMO_SATELITES)
salvar(tles, 'new_glo.json')
