#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 23 17:50:49 2023

@author: sherezadejuarezmartin
"""

import os

import uuid

import numpy as np

from qtpy.QtWidgets import QWidget, QVBoxLayout, QCheckBox, QComboBox, QLineEdit, QLabel, QSpinBox

from glue.config import qt_client
from glue.core.data_combo_helper import ComponentIDComboHelper

from echo import CallbackProperty, SelectionCallbackProperty
from echo.qt import (connect_checkable_button,connect_combo_selection,connect_float_text,
                                   autoconnect_callbacks_to_qt, connect_value)

from glue.viewers.matplotlib.layer_artist import MatplotlibLayerArtist
from glue.viewers.matplotlib.state import (MatplotlibDataViewerState,
                                           MatplotlibLayerState,
                                           DeferredDrawCallbackProperty as DDCProperty,
                                           DeferredDrawSelectionCallbackProperty as DDSCProperty)
from glue.viewers.matplotlib.qt.data_viewer import MatplotlibDataViewer

from glue.utils.qt import load_ui

from astropy.visualization import simple_norm
import megaradrp.visualization as vis
import megaradrp.datamodel as dm
import matplotlib.cm

from glue.core.state_objects import StateAttributeLimitsHelper



class TutorialViewerState(MatplotlibDataViewerState):

    z_att = SelectionCallbackProperty(docstring='The attribute to use on the z-axis')
    #y_att = SelectionCallbackProperty(docstring='The attribute to use on the y-axis')
    x1_att = SelectionCallbackProperty(docstring='The attribute to use on x1')
    d_spin1 = DDCProperty(docstring='The attribute to use on the spin', default=1)
    d_spin2 = DDCProperty(docstring='The attribute to use on the spin', default=4300)

    

    def __init__(self, *args, **kwargs):
        super(TutorialViewerState, self).__init__(*args, **kwargs)
        self._z_att_helper = ComponentIDComboHelper(self, 'z_att')
        #self._y_att_helper = ComponentIDComboHelper(self, 'y_att')
        
        self._x1_att_helper = ComponentIDComboHelper(self, 'x1_att')

        
        self.add_callback('layers', self._on_layers_change)
        self.add_callback('z_att', self._on_attribute_change)
        #self.add_callback('y_att', self._on_attribute_change)
        
        self.add_callback('x1_att', self._on_attribute_change)

        
        self.add_callback('d_spin1', self._on_attribute_change)
        self.add_callback('d_spin2', self._on_attribute_change)


    def _on_layers_change(self, value):
        self._z_att_helper.set_multiple_data(self.layers_data)
        #self._y_att_helper.set_multiple_data(self.layers_data)
        self._x1_att_helper.set_multiple_data(self.layers_data)



    def _on_attribute_change(self, value):
        if self.z_att is not None:
            self.z_axislabel = self.z_att.label
            
        
        if self.x1_att is not None:
            self.x1_axislabel = self.x1_att.label
            
        print(self.d_spin1)
        print(self.d_spin2)

        
        #if self.y_att is not None:
         #   self.y_axislabel = self.y_att.label


class TutorialLayerState(MatplotlibLayerState):
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
        
        #self.uuid = str(uuid.uuid4())

        super(TutorialLayerState, self).__init__(layer=layer, viewer_state=viewer_state)

        self.attribute_lim_helper = StateAttributeLimitsHelper(self, attribute='attribute',
                                                                percentile='percentile',
                                                                lower='v_min', upper='v_max')

        self.attribute_att_helper = ComponentIDComboHelper(self, 'attribute',
                                                            numeric=True, categorical=False)

        
        stretch_display = {'linear': 'Linear','sqrt': 'Square Root','asinh': 'Arcsinh',
                             'log': 'Logarithmic'}
        
        TutorialLayerState.stretch.set_choices(self, ['linear', 'sqrt', 'asinh', 'log'])
        TutorialLayerState.stretch.set_display_func(self, stretch_display.get)
        
        percentile_display = {100: 'Min/Max',
                                  99.5: '99.5%',
                                  99: '99%',
                                  95: '95%',
                                  90: '90%',
                                  'Custom': 'Custom'}
        
        TutorialLayerState.percentile.set_choices(self, [100, 99.5, 99, 95, 90, 'Custom'])
        TutorialLayerState.percentile.set_display_func(self, percentile_display.get)



class TutorialLayerArtist(MatplotlibLayerArtist):

    _layer_state_cls = TutorialLayerState

    def __init__(self, axes, *args, **kwargs):

        super(TutorialLayerArtist, self).__init__(axes, *args, **kwargs)

        self.artist = vis.hexplot(axes, [], [], [], scale=0.443)
        self.mpl_artists.append(self.artist)

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
        
        
        
        fp_conf = dm.get_fiberconf_default('LCB')
        x0 = np.empty((fp_conf.nfibers,))
        y0 = np.empty((fp_conf.nfibers,))
        
        #z0 = np.zeros_like(x0)

        
        # Key is fibid
        for _, fiber in sorted(fp_conf.fibers.items()):
            idx = fiber.fibid - 1
            x0[idx] = fiber.x
            y0[idx] = fiber.y

            

        self._viewer_state.add_callback('z_att', self._on_attribute_change)
        #self._viewer_state.add_callback('y_att', self._on_attribute_change)
        
        self._viewer_state.add_callback('d_spin1', self._on_attribute_change)
        self._viewer_state.add_callback('d_spin2', self._on_attribute_change)


        

    def _on_visual_change(self, value=None):
        
        print('on visual change')
                
        
        print('percentile')
        print(self.state.percentile)  
        
        print('v_max')
        print(self.state.v_max) 
        
        print('v_min')
        print(self.state.v_min)
        
        

        self.axes.grid(self.state.grid)
        
        
        #cbar = pyqtgraph.ColorBarItem(values=None, width=25, colorMap=None, label=None, interactive=True, limits=None, rounding=1, orientation='vertical', pen='w', hoverPen='r', hoverBrush='#FF000080', cmap=None)
        
        #cbar = matplotlib.addColorBar( img_item, colorMap='viridis', values=(0, 1) )
        
        #cbar=matplotlib.pyplot.colorbar(mappable=None, cax=None, ax=None, **kwargs)
        
        
        # if self.state.grayscale:
        #     cmap = matplotlib.cm.get_cmap('gray')
            
        # else:
        #     cmap = matplotlib.cm.get_cmap('viridis')
        #     self.artist.set_cmap(cmap)


        if self.state.grayscale:
            cmap = matplotlib.cm.get_cmap('gray')
            self.artist.set_cmap(cmap)
            
        else:
            cmap = matplotlib.cm.get_cmap('viridis')
            self.artist.set_cmap(cmap)

        zlim = self.artist.get_array()
        
        
        if self.state.percentile == 'Custom':
            percent=None
                               
        else:
            percent= self.state.percentile
                               
            
        norm = simple_norm(zlim, self.state.stretch,
                               min_cut= self.state.v_min,
                               max_cut= self.state.v_max,
                               percent=percent
                               )
        
    
       
        

        self.artist.set_norm(norm)
        self.artist.set_visible(self.state.visible)
        self.artist.set_zorder(self.state.zorder)
        self.artist.set_alpha(self.state.alpha)

        self.redraw()
        
        

    def _on_attribute_change(self, value=None):

        #if self._viewer_state.x_att is None or self._viewer_state.y_att is None:
            #return

        z = self.state.layer[self._viewer_state.z_att]
        #y = self.state.layer[self._viewer_state.y_att]
        
        #x1 = self.state.layer[self._viewer_state.x1_att]
        
        # if self._viewer_state.d_spin1 is None or self._viewer_state.d_spin2 is None:
        #     return
        
        #d_spin1 = self.state.layer[self._viewer_state.d_spin1]
        #d_spin2 = self.state.layer[self._viewer_state.d_spin2]
        
        if self._viewer_state.d_spin1 is None:
            d_spin1 = 1
        else: 
            d_spin1 = self._viewer_state.d_spin1
        
        print('d_spin1', d_spin1)
        
        
        if self._viewer_state.d_spin2 is None:
            d_spin2 = 1
        else: 
            d_spin2 = self._viewer_state.d_spin2
        
        print('d_spin2', d_spin2)

        # print(d_spin1)
        # print(d_spin2)

        #def maximum(d_spin1, d_spin2):
        # if d_spin1 >= d_spin2:
        #     return
        
        # d_spin1 = self._viewer_state.d_spin1
        # d_spin2 = self._viewer_state.d_spin2
        
        if d_spin1 >= d_spin2:
            return
            

        print('DEBUG', z.shape)
        #zlim = z[:, d_spin1:4300].mean(axis=1)
        
        
        zlim = z[:, d_spin1:d_spin2].mean(axis=1)

        self.artist.set_array(zlim)

        # self.axes.set_xlim(np.nanmin(x), np.nanmax(x))
        # self.axes.set_ylim(np.nanmin(y), np.nanmax(y))
        
        self.axes.set_xlim(-6,6)
        self.axes.set_ylim(-6,6)
        
        
        #collection.set_cmap(cmap)
        #collection.set_norm(norm)
        
        fp_conf = dm.get_fiberconf_default('LCB')
        x0 = np.empty((fp_conf.nfibers,))
        y0 = np.empty((fp_conf.nfibers,))
        
        #z0 = np.zeros_like(x0)

        
        # Key is fibid
        for _, fiber in sorted(fp_conf.fibers.items()):
            idx = fiber.fibid - 1
            x0[idx] = fiber.x
            y0[idx] = fiber.y
        
        offsets = np.column_stack([x0, y0])
        
        self.artist.set_offsets(offsets)
        
        corners = ((-6, -6), (6, 6))
        self.axes.update_datalim(corners)
        self.axes.autoscale_view(tight=True)
        
        # def make_selector(self, roi, x0, y0):

        #     state = RoiSubsetState()
        #     state.roi = roi
        #     state.xatt = x0[idx]
        #     state.yatt = y0[idx]

        #     return state
        

        self.redraw()

    def update(self):
        self._on_attribute_change()
        self._on_visual_change()


class TutorialViewerStateWidget(QWidget):

    def __init__(self, viewer_state=None, session=None):

        super(TutorialViewerStateWidget, self).__init__()

        # self.ui = load_ui('viewer_state.ui', self,
        #                   directory=os.getcwd())

        self.viewer_state = viewer_state
        #self._connections = autoconnect_callbacks_to_qt(self.viewer_state, self.ui)
        
        
        d_spin1 = QSpinBox(self)
        #d_spin1.setGeometry(100, 100, 150, 40)
        #d_spin.setDecimals(0)
        d_spin1.setMinimum(1)
        d_spin1.setMaximum(4300)
        
        d_spin2 = QSpinBox(self)
        #d_spin2.setGeometry(100, 100, 150, 40)
        #d_spin.setDecimals(0)
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

        

        self._conn1 = connect_value(self.viewer_state, 'd_spin1', d_spin1)

        self._conn2 = connect_value(self.viewer_state, 'd_spin2', d_spin2)

        self.setLayout(layout)




class TutorialLayerStateWidget(QWidget):

    def __init__(self, layer_artist):

        super(TutorialLayerStateWidget, self).__init__()

        self.checkbox = QCheckBox('Plot grid')
        self.checkbox2 = QCheckBox('Grayscale')
        self.combo1 = QComboBox()
        self.valuetext_v_max = QLineEdit()
        self.valuetext_v_min = QLineEdit()
        self.percentile = QComboBox()
        
        self.nameLabel1 = QLabel(self.percentile)
        self.nameLabel1.setText('Percentil')
        self.nameLabel2 = QLabel(self.valuetext_v_max)
        self.nameLabel2.setText('v_max')

        #self.line.move(80, 20)
        #self.line.resize(200, 32)
        self.nameLabel1.move(3, -6)
        self.nameLabel2.move(3, -6)


        layout = QVBoxLayout()
        layout.addWidget(self.checkbox)
        layout.addWidget(self.checkbox2)
        layout.addWidget(self.combo1)
        layout.addWidget(self.valuetext_v_max)
        layout.addWidget(self.valuetext_v_min)
        layout.addWidget(self.percentile)

        # self.ComboLabel = QLabel('test')
        # #_ComboLabel -> setText("testing")
        # layout.addLabel(self.percentile)
        
        
        
        
        self.setLayout(layout)

        self.layer_state = layer_artist.state

        self._conn1 = connect_checkable_button(self.layer_state, 'grid', self.checkbox)
        self._conn2 = connect_checkable_button(self.layer_state, 'grayscale', self.checkbox2)
        self._conn3 = connect_combo_selection(self.layer_state, 'stretch', self.combo1)
        self._conn4 = connect_float_text(self.layer_state, 'v_max', self.valuetext_v_max)
        self._conn5 = connect_float_text(self.layer_state, 'v_min', self.valuetext_v_min)
        self._conn6 = connect_combo_selection(self.layer_state, 'percentile', self.percentile)



class TutorialDataViewer(MatplotlibDataViewer):

    LABEL = 'Tutorial viewer'
    _state_cls = TutorialViewerState
    _options_cls = TutorialViewerStateWidget
    _layer_style_widget_cls = TutorialLayerStateWidget
    _data_artist_cls = TutorialLayerArtist
    _subset_artist_cls = TutorialLayerArtist


qt_client.add(TutorialDataViewer)