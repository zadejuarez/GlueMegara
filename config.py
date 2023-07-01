#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  3 13:47:59 2023

@author: sherezadejuarezmartin
"""

import numpy as np

from qtpy.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QComboBox, QLineEdit, QLabel, QSpinBox

from glue.config import qt_client
from glue.core.data_combo_helper import ComponentIDComboHelper

from echo import CallbackProperty, SelectionCallbackProperty
from echo.qt import (connect_checkable_button, connect_combo_selection, connect_float_text,
                     connect_value)

from glue.viewers.matplotlib.layer_artist import MatplotlibLayerArtist
from glue.viewers.matplotlib.state import (MatplotlibDataViewerState,
                                           MatplotlibLayerState,
                                           DeferredDrawCallbackProperty as DDCProperty,
                                           DeferredDrawSelectionCallbackProperty as DDSCProperty)
from glue.viewers.matplotlib.qt.data_viewer import MatplotlibDataViewer

from astropy.visualization import simple_norm
import megaradrp.visualization as vis
import megaradrp.datamodel as dm
import matplotlib.cm

from glue.core.state_objects import StateAttributeLimitsHelper
from glue.core.subset import Subset


class MegaraViewerState(MatplotlibDataViewerState):
    """
    Esta clase contiene los datos de interés con los que se va a trabajar
    
    """

    z_att = SelectionCallbackProperty(docstring='The attribute to use on the z-axis')
    x1_att = SelectionCallbackProperty(docstring='The attribute to use on x1')
    d_spin1 = DDCProperty(docstring='The attribute to use on the spin button', default=1)
    d_spin2 = DDCProperty(docstring='The attribute to use on the spin button', default=4300)

    def __init__(self, *args, **kwargs):
        super(MegaraViewerState, self).__init__(*args, **kwargs)
        self._z_att_helper = ComponentIDComboHelper(self, 'z_att')
        self._x1_att_helper = ComponentIDComboHelper(self, 'x1_att')

        self.add_callback('layers', self._on_layers_change)
        self.add_callback('z_att', self._on_attribute_change)

        self.add_callback('x1_att', self._on_attribute_change)

        self.add_callback('d_spin1', self._on_attribute_change)
        self.add_callback('d_spin2', self._on_attribute_change)

    def _on_layers_change(self, value):

        """
        Esta función se llama cuando cambia layers
        
        """
        self._z_att_helper.set_multiple_data(self.layers_data)
        self._x1_att_helper.set_multiple_data(self.layers_data)

    def _on_attribute_change(self, value):

        """
        Esta función ejecuta los cambios deseados
        
        """
        if self.z_att is not None:
            self.z_axislabel = self.z_att.label

        if self.x1_att is not None:
            self.x1_axislabel = self.x1_att.label

        print(self.d_spin1)
        print(self.d_spin2)


class MegaraLayerState(MatplotlibLayerState):
    """
    En esta clase se definen las distintas opciones que pueden mostrarse
    en el apartado Plot Layers de Glue
    
    """

    grid = CallbackProperty(False, docstring='Plot grid')

    grayscale = CallbackProperty(False, docstring='grayscale')

    attribute = DDSCProperty(docstring='The attribute shown in the layer')

    v_min = DDCProperty(docstring='The lower level shown')

    v_max = DDCProperty(docstring='The upper level shown')

    percentile = DDSCProperty(docstring='The percentile value used to '
                                        'automatically calculate levels')

    stretch = DDSCProperty(docstring='The stretch used to render the layer, '
                                     'which should be one of ``linear``, '
                                     '``sqrt``, ``log``, or ``arcsinh``')

    global_sync = DDCProperty(False, docstring='Whether the color and transparency '
                                               'should be synced with the global '
                                               'color and transparency for the data')

    def __init__(self, layer=None, viewer_state=None, **kwargs):
        super(MegaraLayerState, self).__init__(layer=layer, viewer_state=viewer_state)

        self.attribute_lim_helper = StateAttributeLimitsHelper(self, attribute='attribute',
                                                               percentile='percentile',
                                                               lower='v_min', upper='v_max')

        self.attribute_att_helper = ComponentIDComboHelper(self, 'attribute',
                                                           numeric=True, categorical=False)

        stretch_display = {'linear': 'Linear', 'sqrt': 'Square Root', 'asinh': 'Arcsinh',
                           'log': 'Logarithmic'}

        MegaraLayerState.stretch.set_choices(self, ['linear', 'sqrt', 'asinh', 'log'])
        MegaraLayerState.stretch.set_display_func(self, stretch_display.get)

        percentile_display = {100: 'Min/Max',
                              99.5: '99.5%',
                              99: '99%',
                              95: '95%',
                              90: '90%',
                              'Custom': 'Custom'}

        MegaraLayerState.percentile.set_choices(self, [100, 99.5, 99, 95, 90, 'Custom'])
        MegaraLayerState.percentile.set_display_func(self, percentile_display.get)


class MegaraLayerArtist(MatplotlibLayerArtist):
    """
    En esta clase se llaman a los parámetros definidos en la clase anterior
    para que se muestre su funcionalidad por pantalla en Glue
    
    """

    _layer_state_cls = MegaraLayerState

    def __init__(self, axes, *args, **kwargs):

        super(MegaraLayerArtist, self).__init__(axes, *args, **kwargs)

        self.artist = vis.hexplot(axes, [], [], [], scale=0.443)  # Para visualización en hexágonos
        self.mpl_artists.append(self.artist)

        # Se añaden todos los callbacks de los parámetros para ejecutar el cambio en el visualizador
        self.state.add_callback('grid', self._on_visual_change)
        self.state.add_callback('grayscale', self._on_visual_change)
        self.state.add_callback('stretch', self._on_visual_change)
        self.state.add_callback('v_min', self._on_visual_change)
        self.state.add_callback('v_max', self._on_visual_change)
        self.state.add_callback('percentile', self._on_visual_change)
        self.state.add_callback('visible', self._on_visual_change)
        self.state.add_callback('zorder', self._on_visual_change)
        self.state.add_callback('color', self._on_visual_change)
        self.state.add_callback('alpha', self._on_visual_change)

        # Configuración del plano focal. Se crean vectores vacíos para las fibras
        fp_conf = dm.get_fiberconf_default('LCB')
        x0 = np.empty((fp_conf.nfibers,))
        y0 = np.empty((fp_conf.nfibers,))

        # Key is fibid
        for _, fiber in sorted(fp_conf.fibers.items()):
            idx = fiber.fibid - 1
            x0[idx] = fiber.x
            y0[idx] = fiber.y

        self._viewer_state.add_callback('z_att', self._on_attribute_change)
        self._viewer_state.add_callback('d_spin1', self._on_attribute_change)
        self._viewer_state.add_callback('d_spin2', self._on_attribute_change)

    def _on_visual_change(self, value=None):

        """ 
        Esta función se utiliza para representar algunos de los parámetros definidos
        
        """

        # Ejes
        self.axes.grid(self.state.grid)

        # Escala de grises y color
        if self.state.grayscale:
            cmap = matplotlib.cm.get_cmap('gray')
            self.artist.set_cmap(cmap)

        else:
            cmap = matplotlib.cm.get_cmap('viridis')
            self.artist.set_cmap(cmap)

        # Se define un array de la imagen 2D colapsada
        zlim = self.artist.get_array()

        # Esta condición es para evitar un error si se tomara un array vacío
        if zlim is None or len(zlim) == 0:
            return

        # Esta condición es para evitar un error cuando el valor del percentil
        # es customizable
        if self.state.percentile == 'Custom':
            percent = None

        else:
            percent = self.state.percentile

        # Normalización para representación de la imagen en Matplotlib
        norm = simple_norm(zlim, self.state.stretch,
                           min_cut=self.state.v_min,
                           max_cut=self.state.v_max,
                           percent=percent
                           )

        self.artist.set_norm(norm)
        self.artist.set_visible(self.state.visible)
        self.artist.set_zorder(self.state.zorder)
        self.artist.set_alpha(self.state.alpha)

        self.redraw()

    def _on_attribute_change(self, value=None):

        """
        Callbacks for change on attribute values
        
        """

        # Configuración del plano focal. Se crean vectores vacíos para las fibras
        fp_conf = dm.get_fiberconf_default('LCB')
        x0 = np.empty((fp_conf.nfibers,))
        y0 = np.empty((fp_conf.nfibers,))

        # Key is fibid
        for _, fiber in sorted(fp_conf.fibers.items()):
            idx = fiber.fibid - 1
            x0[idx] = fiber.x
            y0[idx] = fiber.y

        offsets = np.column_stack([x0, y0])

        # Se implementa la máscara para la selección en imagen 2D y visualización en viewer
        if isinstance(self.state.layer, Subset):
            ss = self.state.layer
            print(ss.label)
            print(ss.style)
            print(ss.style.color)
            print(ss.subset_state)
            mask2 = ss.to_mask()
            mask3 = mask2.any(axis=1)
            self.artist.set_offsets(offsets[mask3])
            colors = ss.style.color
            self.artist.set_edgecolors(colors)

        else:

            z = self.state.layer[self._viewer_state.z_att]

            # Definimos el rango espectral de la imagen para los dos parámetros
            # que dan los valores de z_att (d_spin1 y d_spin2), con botones de tipo spin
            if self._viewer_state.d_spin1 is None:
                d_spin1 = 1
            else:
                d_spin1 = self._viewer_state.d_spin1

            if self._viewer_state.d_spin2 is None:
                d_spin2 = 1
            else:
                d_spin2 = self._viewer_state.d_spin2

            if d_spin1 >= d_spin2:  # Esta condición sirve para evitar un error en la definición de zlim
                return

            zlim = z[:, d_spin1:d_spin2].mean(axis=1)

            self.artist.set_array(zlim)

            # Se establecen los límites de los ejes
            self.axes.set_xlim(-6, 6)
            self.axes.set_ylim(-6, 6)

            self.artist.set_offsets(offsets)

            self.axes.autoscale_view(tight=True)

        self.redraw()

    def update(self):
        self._on_attribute_change()
        self._on_visual_change()


class MegaraViewerStateWidget(QWidget):
    """
    En esta clase se definen los parámetros de los widgets que aparecen 
    en el apartado Plot Options de Glue
    
    """

    def __init__(self, viewer_state=None, session=None):
        super(MegaraViewerStateWidget, self).__init__()

        self.viewer_state = viewer_state

        # Botones de tipo spin para el rango espectral 
        d_spin1 = QSpinBox(self)

        d_spin1.setMinimum(1)
        d_spin1.setMaximum(4300)

        d_spin2 = QSpinBox(self)

        d_spin2.setMinimum(1)
        d_spin2.setMaximum(4300)

        label = QLabel("Spectral range", self)
        label.setWordWrap(True)

        d_spin1.valueChanged.connect(lambda: spin1_method())
        d_spin2.valueChanged.connect(lambda: spin2_method())

        def spin1_method():
            # setting text to the label
            label.setText("Value Changed Signal")

        def spin2_method():
            # setting text to the label
            label.setText("Value 2 Changed Signal")

        layout = QVBoxLayout()
        layout.addWidget(d_spin1)
        layout.addWidget(d_spin2)

        # Conexión de la spin box
        self._conn1 = connect_value(self.viewer_state, 'd_spin1', d_spin1)

        self._conn2 = connect_value(self.viewer_state, 'd_spin2', d_spin2)

        self.setLayout(layout)


class MegaraLayerStateWidget(QWidget):
    """
    En esta clase se crean los apartados de selección de las distintas funciones
    definidas como checkboxes o líneas de edición
    
    """

    def __init__(self, layer_artist):
        super(MegaraLayerStateWidget, self).__init__()

        # Se crean los botones y líneas de selección
        self.checkbox = QCheckBox('Plot grid')
        self.checkbox2 = QCheckBox('Grayscale')
        self.combo1 = QComboBox()
        self.valuetext_v_max = QLineEdit()
        self.valuetext_v_min = QLineEdit()
        self.percentile = QComboBox()

        # Etiquetado de los distintos apartados
        self.nameLabel1 = QLabel(self.percentile)
        self.nameLabel1.setText('Percentil')
        self.nameLabel2 = QLabel(self.valuetext_v_max)
        self.nameLabel2.setText('v_max')
        self.nameLabel3 = QLabel(self.valuetext_v_min)
        self.nameLabel3.setText('v_min')

        # Poscición de las etiquetas
        self.nameLabel1.move(3, -6)
        self.nameLabel2.move(3, -6)
        self.nameLabel3.move(3, -6)

        # Se añaden los botones creados
        layout = QVBoxLayout()
        layout.addWidget(self.checkbox)
        layout.addWidget(self.checkbox2)
        layout.addWidget(self.combo1)
        layout.addWidget(self.valuetext_v_max)
        layout.addWidget(self.valuetext_v_min)
        layout.addWidget(self.percentile)

        self.setLayout(layout)

        self.layer_state = layer_artist.state

        # Conexión de los apartados creados
        self._conn1 = connect_checkable_button(self.layer_state, 'grid', self.checkbox)
        self._conn2 = connect_checkable_button(self.layer_state, 'grayscale', self.checkbox2)
        self._conn3 = connect_combo_selection(self.layer_state, 'stretch', self.combo1)
        self._conn4 = connect_float_text(self.layer_state, 'v_max', self.valuetext_v_max)
        self._conn5 = connect_float_text(self.layer_state, 'v_min', self.valuetext_v_min)
        self._conn6 = connect_combo_selection(self.layer_state, 'percentile', self.percentile)


class MegaraDataViewer(MatplotlibDataViewer):
    """
    Main class for MEGARA
    
    """

    LABEL = 'MEGARA viewer'
    _state_cls = MegaraViewerState
    _options_cls = MegaraViewerStateWidget
    _layer_style_widget_cls = MegaraLayerStateWidget
    _data_artist_cls = MegaraLayerArtist
    _subset_artist_cls = MegaraLayerArtist

    inherit_tools = True
    tools = ['select:rectangle']

    def apply_roi(self, roi, override_mode=None):

        """
        Esta función define la región de interés seleccionada por el usuario
        
        """

        datos = self.state.z_att.parent
        axis0 = datos.components[0]

        fp_conf = dm.get_fiberconf_default('LCB')
        x0 = np.empty((fp_conf.nfibers,))
        y0 = np.empty((fp_conf.nfibers,))

        # Bucle para sacar las coordenadas de todas las fibras   
        for _, fiber in sorted(fp_conf.fibers.items()):
            idx = fiber.fibid - 1
            x0[idx] = fiber.x
            y0[idx] = fiber.y

        mask = roi.contains(x0, y0)
        values = mask.nonzero()
        fibs = values[0]
        subset_state = axis0 == fibs[0]

        for f in fibs[1:]:
            subset_state = subset_state | (axis0 == f)

        self.apply_subset_state(subset_state, override_mode=override_mode)


qt_client.add(MegaraDataViewer)
