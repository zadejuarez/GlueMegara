#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  3 13:47:59 2023

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
from glue.core.subset import RoiSubsetState
from glue.core.roi import RectangularROI

from glue.config import link_helper
from glue.core.link_helpers import LinkCollection



class MegaraViewerState(MatplotlibDataViewerState):

    z_att = SelectionCallbackProperty(docstring='The attribute to use on the z-axis')
    #y_att = SelectionCallbackProperty(docstring='The attribute to use on the y-axis')
    x1_att = SelectionCallbackProperty(docstring='The attribute to use on x1')
    d_spin1 = DDCProperty(docstring='The attribute to use on the spin', default=1)
    d_spin2 = DDCProperty(docstring='The attribute to use on the spin', default=4300)

    

    def __init__(self, *args, **kwargs):
        super(MegaraViewerState, self).__init__(*args, **kwargs)
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


class MegaraLayerState(MatplotlibLayerState):
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

        super(MegaraLayerState, self).__init__(layer=layer, viewer_state=viewer_state)

        self.attribute_lim_helper = StateAttributeLimitsHelper(self, attribute='attribute',
                                                                percentile='percentile',
                                                                lower='v_min', upper='v_max')

        self.attribute_att_helper = ComponentIDComboHelper(self, 'attribute',
                                                            numeric=True, categorical=False)

        
        stretch_display = {'linear': 'Linear','sqrt': 'Square Root','asinh': 'Arcsinh',
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

    _layer_state_cls = MegaraLayerState

    def __init__(self, axes, *args, **kwargs):

        super(MegaraLayerArtist, self).__init__(axes, *args, **kwargs)

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

        # def maximum(d_spin1, d_spin2):
        #     if d_spin1 >= d_spin2:
        #         return
            

        
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


class MegaraViewerStateWidget(QWidget):

    def __init__(self, viewer_state=None, session=None):

        super(MegaraViewerStateWidget, self).__init__()

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
        
        # d_spin1.editingFinished.connect(lambda: spin1_method())

        # def spin1_method():
  
        # # getting current value of spin box
            
      
        #     label.setText("Value Changed Signal")
      
        
        layout = QVBoxLayout() 
        layout.addWidget(d_spin1)
        layout.addWidget(d_spin2)

        

        self._conn1 = connect_value(self.viewer_state, 'd_spin1', d_spin1)

        self._conn2 = connect_value(self.viewer_state, 'd_spin2', d_spin2)

        self.setLayout(layout)




class MegaraLayerStateWidget(QWidget):

    def __init__(self, layer_artist):

        super(MegaraLayerStateWidget, self).__init__()

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


    
    
class MegaraDataViewer(MatplotlibDataViewer):

    LABEL = 'MEGARA viewer'
    _state_cls = MegaraViewerState
    _options_cls = MegaraViewerStateWidget
    _layer_style_widget_cls = MegaraLayerStateWidget
    _data_artist_cls = MegaraLayerArtist
    _subset_artist_cls = MegaraLayerArtist
    # _toolbar_cls = BasicToolbar

    inherit_tools = True
    tools = ['select:rectangle']

    def apply_roi(self, roi, override_mode=None):
        #from glue.core.subset import roi_to_subset_state
        print("METHOD APPLY ROI")
        ##roi = RectangularROI(xmin=1, xmax=3, ymin=2, ymax=5)
        print(roi, type(roi))
        print(override_mode)
        
        datos = self.state.z_att.parent
        print(datos, type(datos))
        axis0 = datos.component[0]
        subset_state = datos > 300
        subset_state = (axis0 == 1 ) & (axis0 == 20) & (axis0 > 300)
        fibs = [1, 23, 45, 56, 89, 200]
        subset_state = None
        
        
        for f in fibs:
            subset_state = subset_state & (datos == f)
            
        # import megaradrp.datamodel as dm
        
        fp_conf=dm.get_fiberconf_default('LCB')
        x0 = np.empty((fp_conf.nfibers,))
        y0 = np.empty((fp_conf.nfibers,))
        
        # Bucle para sacar las coordenadas de todas las fibras 
        
        # xfib, yfib   
        for _, fiber in sorted(fp_conf.fibers.items()):
            idx = fiber.fibid - 1
            x0[idx] = fiber.x
            y0[idx] = fiber.y
        
        
        mask = roi.contains(x0, y0)
        subset_state = [axis0 == f for f in fibs[mask]]
        # fibs a partir de mask
        subset_state = None
        for f in fibs:
             subset_state = subset_state & (axis0 == f)
             
        self.apply_subset_state(subset_state,override_mode=override_mode)

        #use_transform = False
        # subset_state = roi_to_subset_state(roi,
        #                                   x_att=self.state.x_att, x_categories=self.state.x_categories,
        #                                   y_att=self.state.y_att, y_categories=self.state.y_categories,
        #                                   use_pretransform=use_transform)

        # subset_state = RoiSubsetState()
        # subset_state.xatt = [-1, 0, 1]
        # subset_state.yatt = [-1, 0, 1]
        
        # # from glue.core import Data
        # # data = Data(x=[1,2,3], y=[2,3,4])
        # # state = data.id['x'] > 1.5
        # # state

        # self.apply_subset_state(subset_state, override_mode=override_mode)


        
# =============================================================================
#         
#         from glue.core import Data
#         data = Data(x=[1,2,3], y=[2,3,4])
#         state = data.id['x'] > 1.5
#         # state
#         
#         from glue.core import DataCollection
#         data_collection = DataCollection([data])
#         subset_group = data_collection.new_subset_group('x > 1.5', state)
# 
#         subset = subset_group.subsets[0]
#         subset
#     
#     def plot_subset(self, axes, x0, y0, style):
#             axes.plot(x0, y0, 'o',
#                       alpha=style.alpha,
#                       mec=style.color,
#                       mfc=style.color,
#                       ms=style.markersize)
# =============================================================================
        
# @link_helper(category="Join")
# class JoinLink(LinkCollection):
#     cid_independent = False

#     display = "Join on ID"
#     description = "Join two datasets on a common ID. Other links \
# in glue connect data columns (two datasets have 'age' columns but \
# the rows are different objects), while Join on ID connects the same \
# rows/items across two datasets."

#     labels1 = ["Identifier in dataset 1"]
#     labels2 = ["Identifier in dataset 2"]

#     def __init__(self, *args, cids1=None, cids2=None, data1=None, data2=None):
#         # only support linking by one value now, even though link_by_value supports multiple
#         assert len(cids1) == 1
#         assert len(cids2) == 1

#         self.data1 = data1
#         self.data2 = data2
#         self.cids1 = cids1
#         self.cids2 = cids2

#         self._links = []

#     def __str__(self):
#         # The >< here is one symbol for a database join
#         return '%s >< %s' % (self.cids1, self.cids2)

#     def __repr__(self):
#         return "<JoinLink: %s>" % self

#     # Define __eq__ and __ne__ to facilitate removing
#     # these kinds of links from the link_manager
#     def __eq__(self, other):
#         if not isinstance(other, JoinLink):
#             return False
#         same = ((self.data1 == other.data1) and
#                 (self.data2 == other.data2) and
#                 (self.cids1 == other.cids1) and
#                 (self.cids2 == other.cids2))
#         flip = ((self.data1 == other.data2) and
#                 (self.data2 == other.data1) and
#                 (self.cids1 == other.cids2) and
#                 (self.cids2 == other.cids1))
#         return same or flip

#     def __ne__(self, other):
#         return not self.__eq__(other)


qt_client.add(MegaraDataViewer)









