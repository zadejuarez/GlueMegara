# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

VERSION = '0.0.1' 
DESCRIPTION = 'Paquete visualizador MEGARA'
LONG_DESCRIPTION = 'Paquete para visualizador de MEGARA empleando Glue'

# Configurando
setup(
       # el nombre debe coincidir con el nombre de la carpeta 	  
       #'modulomuysimple'
        name="megara_vis_glue", 
        version=VERSION,
        author="Sherezade Juarez",
        #author_email="<tuemail@email.com>",
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        packages=find_packages(),
        install_requires=['numpy', 'glue', 'astropy'],
        url= 'https://github.com/zadejuarez/GlueMegara'
        

)