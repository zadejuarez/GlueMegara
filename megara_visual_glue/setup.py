# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

VERSION = '0.0.0' 
DESCRIPTION = 'Paquete visualizador MEGARA'
LONG_DESCRIPTION = 'Paquete para visualizador de MEGARA empleando Glue'

# Configurando
setup(
       # el nombre debe coincidir con el nombre de la carpeta 	  
       #'modulomuysimple'
        name="megara_visual_glue", 
        version=VERSION,
        author="Sherezade Juarez",
        author_email="shjuarez@ucm.es",
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        packages=find_packages(),
        install_requires=['numpy', 'glue', 'astropy'],
        url= 'https://github.com/zadejuarez/GlueMegara/tree/zadejuarez-patch-2/megara_visual_glue'
        

)