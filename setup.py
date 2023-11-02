# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

VERSION = '0.0.2' 
DESCRIPTION = 'Paquete visualizador MEGARA'
LONG_DESCRIPTION = 'Paquete para visualizador de MEGARA empleando Glue'

# Configurando
setup(
        name="megara_visual_glue", 
        version=VERSION,
        author="Sherezade JM",
        author_email="shjuarez@ucm.es",
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        packages=find_packages(),
        install_requires=[
            'numpy', 
            'glueviz', 
            'astropy',
            'matplotlib',
            'megaradrp',
            'qtpy',
            ],
        url= 'https://github.com/zadejuarez/GlueMegara'
)
