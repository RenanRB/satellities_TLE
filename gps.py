"""Atualiza os TLEs do GPS a partir do Celestrak."""

from tle_fetch import buscar, salvar

# Piso de seguranca: hoje a constelacao publica bem mais que isso, entao um
# valor abaixo daqui significa resposta truncada, nao satelite desativado.
MINIMO_SATELITES = 24

tles = buscar('gps-ops', MINIMO_SATELITES)
salvar(tles, 'new_gps.json')
