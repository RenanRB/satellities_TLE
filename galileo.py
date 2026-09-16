"""Atualiza os TLEs do Galileo a partir do Celestrak."""

from tle_fetch import buscar, salvar

# Piso de seguranca: hoje a constelacao publica bem mais que isso, entao um
# valor abaixo daqui significa resposta truncada, nao satelite desativado.
MINIMO_SATELITES = 24

tles = buscar('galileo', MINIMO_SATELITES)
salvar(tles, 'new_galileo.json')
