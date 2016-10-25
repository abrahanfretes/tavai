#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
# ##############################################################
#                                                            ###
# Universidad Nacional de Asunción - Facultad Politécnica    ###
# Ingenieria en Informática - Proyecto Final de Grado        ###
#                                                            ###
# Autores:                                                   ###
#           - Arsenio Ferreira (arse.ferreira@gmail.com)     ###
#           - Abrahan Fretes (abrahan.fretes@gmail.com)      ###
#                                                            ###
# Creado:  1/9/2016                                          ###
#                                                            ###
# ##############################################################
'''

from pandas.core.frame import DataFrame
import sys
import wx
from wx.lib import platebtn
from wx.lib.agw import customtreectrl as CT
from wx.lib.mixins.listctrl import CheckListCtrlMixin

import numpy as np
import pandas as pd
from views.wrapper.vdialog.vvisualization import ClusterConfig, V_M_CLUSTER,\
    V_M_SUMMARY, V_M_CLUSTER_SUMMARY, SelectedData, FilterClusterDialog
from views.wrapper.wraview.cluster.shape import Shape
from views.wrapper.wraview.cluster.tkmeans import Kmeans
from views.wrapper.wraview.vcontrolm import KMSG_EMPTY_DATA_SELECTED, \
    KMessage, KMSG_EMPTY_CLUSTER_SELECTED, \
    KMSG_EMPTY_CLUSTER_DATA, KMSG_EMPTY_DATA_GENERATE_CLUSTER, \
    KMSG_GENERATE_CLUSTER
import wx.lib.agw.aui as aui

from wx import GetTranslation as L
from wx.lib.pubsub import Publisher as pub
from languages import topic as T
import threading

K_MANY_PAGE = 0
K_3D_PAGE = 1
K_2D_PAGE = 2
K_1D_PAGE = 3

KURI_AUI_NB_STYLE = aui.AUI_NB_TOP | aui.AUI_NB_TAB_SPLIT | \
    aui.AUI_NB_TAB_MOVE | aui.AUI_NB_SCROLL_BUTTONS | \
    aui.AUI_NB_MIDDLE_CLICK_CLOSE | aui.AUI_NB_DRAW_DND_TAB

KURI_AUI_NB_STYLE1 = aui.AUI_NB_TOP | \
    aui.AUI_NB_TAB_MOVE | aui.AUI_NB_SCROLL_BUTTONS | \
    aui.AUI_NB_MIDDLE_CLICK_CLOSE | aui.AUI_NB_DRAW_DND_TAB

KURI_TR_STYLE = CT.TR_HIDE_ROOT | CT.TR_NO_LINES | \
    CT.TR_HAS_BUTTONS | CT.TR_AUTO_CHECK_CHILD

KURI_TR_STYLE1 = CT.TR_HIDE_ROOT | CT.TR_TWIST_BUTTONS

option_figures_3d = ['Lineas 3D', 'Scatter 3D', 'Barras vertical 3D',
                     'Poligono']


K_DATE_DUPLICATE_TRUE = 0
K_DATE_DUPLICATE_FALSE = 1
K_DATE_DUPLICATE_ONLY = 2

K_PLOT_ALL_IN_ONE = 0
K_PLOT_BLOCK = 1

K_COLOR_ONE = 0
K_COLOR_BLOCK = 1
K_COLOR_SUB_BLOCK = 2
K_COLOR_VALUE = 3

CLUS_SHAPE = 0
CLUS_KMEANS = 1
CLUS_BOTH = 2


class ControlPanel(wx.Panel):

    def __init__(self, parent, kfigure, ksub_blocks, mainpanel):
        wx.Panel.__init__(self, parent)

        pub().subscribe(self.update_language, T.LANGUAGE_CHANGED)

        self.parent = parent
        self.mainpanel = mainpanel
        self.kfigure = kfigure
        self.SetBackgroundColour("#3B598D")

        self.init_arrays()

        self.data_selected = None
        self.normalization = 0
        self.cluster_or_date = 0

        self.duplicate_true = K_DATE_DUPLICATE_TRUE
        self.k_plot = K_PLOT_BLOCK
        self.k_color = K_COLOR_SUB_BLOCK
        self.cluster_config = None
        self.cluster_filter = None
        self.visualization_mode = V_M_CLUSTER_SUMMARY
        self.legends_cluster = [False, False, False, True]
        self.legends_summary = [True, False, False, False]
        self.clus_one_axe = True
        self.summ_one_axe = True
        self.clus_summ_axs = [True, False, False, False]

        # ---- Lista de Datos
        self.data_seccion = DataSeccion(self, ksub_blocks)

        # ---- datos - normalización de datos
        panel_control = wx.Panel(self)
        panel_control.SetBackgroundColour('#DCE5EE')
        panel_radio = wx.Panel(panel_control)
        grid_radio = wx.BoxSizer(wx.HORIZONTAL)
        radio1 = wx.RadioButton(panel_radio, -1, 'Cluster', style=wx.RB_GROUP)
        self.radio2 = wx.RadioButton(panel_radio, -1, L('DATA'))
        grid_radio.Add(radio1, 0, wx.ALL, 5)
        grid_radio.Add(self.radio2, 0, wx.ALL, 5)
        radio1.Bind(wx.EVT_RADIOBUTTON, self.on_check_cluster)
        self.radio2.Bind(wx.EVT_RADIOBUTTON, self.on_check_data)
        panel_radio.SetSizer(grid_radio)
        panel_radio.SetBackgroundColour('#DCE5EE')
        panel_sizer = wx.BoxSizer(wx.VERTICAL)
        panel_sizer.Add(panel_radio, 1, wx.ALIGN_CENTER_HORIZONTAL)
        panel_control.SetSizer(panel_sizer)

        grid = wx.FlexGridSizer(cols=2)
        self.tbtn0 = platebtn.PlateButton(self, -1,
                                          self.NORMA_METO[self.normalization],
                                          None,
                                          style=platebtn.PB_STYLE_SQUARE |
                                          platebtn.PB_STYLE_NOBG)
        menu = wx.Menu()
        m_n1 = wx.MenuItem(menu, 0, self.NORMA_METO[0])
        self.m_n2 = wx.MenuItem(menu, 1, self.NORMA_METO[1])
        self.m_n3 = wx.MenuItem(menu, 2, self.NORMA_METO[2])
        m_n4 = wx.MenuItem(menu, 3, self.NORMA_METO[3])

        menu.AppendItem(m_n1)
        menu.AppendItem(self.m_n2)
        menu.AppendItem(self.m_n3)
        menu.AppendItem(m_n4)

        self.tbtn0.SetMenu(menu)
        self.tbtn0.SetLabelColor(wx.Colour(0, 0, 255))
        self.tbtn0.Bind(wx.EVT_MENU, self.on_nor_menu)
        grid.Add(self.tbtn0, 0, wx.ALIGN_LEFT | wx.ALL, 5)

        # ---- Configuración de Clusters
        c_sizer = wx.BoxSizer()
        self.sc_count_clusters = wx.SpinCtrl(self, -1, "", size=(80, 30))
        self.sc_count_clusters.SetRange(0, 1000)
        self.sc_count_clusters.SetValue(0)
        tbtna = platebtn.PlateButton(self, -1, self.ANALISIS_LABEL[0], None,
                                     style=platebtn.PB_STYLE_DEFAULT |
                                     platebtn.PB_STYLE_NOBG)
        tbtna.SetPressColor(wx.Colour(255, 165, 0))
        tbtna.SetLabelColor(wx.Colour(0, 0, 255))
        tbtna.Bind(wx.EVT_BUTTON, self.on_generate)
        self.tbtna = tbtna
        c_sizer.Add(self.sc_count_clusters, 0, wx.TOP | wx.RIGHT | wx.LEFT |
                    wx.ALIGN_CENTER_HORIZONTAL, 5)
        c_sizer.Add(tbtna, 0, wx.TOP | wx.RIGHT | wx.LEFT |
                    wx.ALIGN_CENTER_VERTICAL, 5)

        # ---- seleccionar - analizar
        a_sizer = wx.BoxSizer()
        tbtnb = platebtn.PlateButton(self, -1, self.ANALISIS_LABEL[1], None,
                                     style=platebtn.PB_STYLE_DEFAULT |
                                     platebtn.PB_STYLE_NOBG)
        tbtnb.SetPressColor(wx.Colour(165, 42, 42))
        tbtnb.SetLabelColor(wx.Colour(0, 0, 255))
        tbtnb.Bind(wx.EVT_BUTTON, self.on_filter)
        self.tbtnb = tbtnb

        tbtnc = platebtn.PlateButton(self, -1, self.ANALISIS_LABEL[2], None,
                                     style=platebtn.PB_STYLE_DEFAULT |
                                     platebtn.PB_STYLE_NOBG)
        tbtnc.SetPressColor(wx.Colour(165, 42, 42))
        tbtnc.SetLabelColor(wx.Colour(0, 0, 255))
        tbtnc.Bind(wx.EVT_BUTTON, self.on_config)
        self.tbtnc = tbtnc

        a_sizer.Add(tbtnb, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)
        a_sizer.Add(tbtnc, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

        # ---- Lista de Clusters
        self.clusters_seccion = ClusterSeccion(self)

        # ---- marco visualización
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.data_seccion, 2, wx.EXPAND | wx.ALL |
                       wx.ALIGN_CENTER_HORIZONTAL, 2)
        self.sizer.Add(panel_control, 0, wx.EXPAND | wx.TOP | wx.RIGHT |
                       wx.LEFT | wx.ALIGN_RIGHT, 2)
        self.sizer.Add(grid, 0, wx.TOP | wx.RIGHT | wx.LEFT |
                       wx.ALIGN_CENTER_HORIZONTAL, 2)
        self.sizer.Add(a_sizer, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 2)
        self.sizer.Add(c_sizer, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 2)
        self.sizer.Add(self.clusters_seccion, 4, wx.EXPAND | wx.ALL, 1)

        self.SetSizer(self.sizer)
        self.Fit()

    def on_check_cluster(self, event):
        self.sc_count_clusters.Enable()
        self.tbtna.Enable()
        self.tbtnb.Enable()
        self.tbtnc.Enable()
        self.tbtna.SetLabelColor(wx.Colour(0, 0, 255))
        self.tbtnb.SetLabelColor(wx.Colour(0, 0, 255))
        self.tbtnc.SetLabelColor(wx.Colour(0, 0, 255))
        self.m_n2.Enable()
        self.m_n3.Enable()
        self.cluster_or_date = 0

    def on_check_data(self, event):
        self.sc_count_clusters.Disable()
        self.tbtna.SetLabelColor(wx.Colour(191, 191, 191))
        self.tbtnb.SetLabelColor(wx.Colour(191, 191, 191))
        self.tbtnc.SetLabelColor(wx.Colour(191, 191, 191))
        self.tbtna.Disable()
        self.tbtnb.Disable()
        self.tbtnc.Disable()
        self.m_n2.Enable(False)
        self.m_n3.Enable(False)
        self.cluster_or_date = 1

    def update_language(self, msg):
        self.init_arrays()

        self.radio2.SetLabel(L('DATA'))

        self.tbtn0.SetLabel(self.NORMA_METO[self.normalization])
        self.tbtn0.GetMenu().SetLabel(0, self.NORMA_METO[0])
        self.tbtn0.GetMenu().SetLabel(1, self.NORMA_METO[1])
        self.tbtn0.GetMenu().SetLabel(2, self.NORMA_METO[2])
        self.tbtn0.GetMenu().SetLabel(3, self.NORMA_METO[3])
        self.tbtn0.Refresh()

        self.tbtna.SetLabel(self.ANALISIS_LABEL[0])
        self.tbtna.Refresh()
        self.tbtnb.SetLabel(self.ANALISIS_LABEL[1])
        self.tbtnb.Refresh()
        self.tbtnc.SetLabel(self.ANALISIS_LABEL[2])
        self.tbtnc.Refresh()

    def init_arrays(self):
        self.NORMA_METO = [L('NORMALIZED_FULL'), L('NORMALIZED_CLUSTER'),
                           L('NORMALIZED_SELECTED'), L('DATA_CRUDE')]
        self.ANALISIS_LABEL = [L('GENERATE'), L('SELECT'), L('VISUALIZE')]

    def run_fig(self):

        # ---- Se desea visualizar Clusters
        if self.cluster_or_date == 0:
            self.v_clusters()

        # ---- Se desea visualizar Datos
        if self.cluster_or_date == 1:
            self.v_datas()

    def v_datas(self):

        # ---- se obtine la lista de bloques marcados

        blocks = self.data_seccion.get_checkeds()

        if blocks == []:
            KMessage(self.mainpanel, KMSG_EMPTY_DATA_SELECTED).kshow()
            return

        df = pd.concat(blocks)

        # ---- normalización de datos
        _s = []
        if self.normalization == 0:
            _s.append(self._nor(df))
        else:
            _s.append(df)

        # update figure
        self.kfigure.kdraw(_s)

    def v_clusters(self):

        # ---- verificar valores en clusters
        if not self.clusters_seccion.contain_elemens():
            KMessage(self.mainpanel, KMSG_EMPTY_CLUSTER_DATA).kshow()
            return
        if not self.clusters_seccion.checked_elemens():
            KMessage(self.mainpanel, KMSG_EMPTY_CLUSTER_SELECTED).kshow()
            return

        # ---- selección de clusters a visualizar
        shape = self.clusters_seccion.g_for_view()
        s_clusters = shape.g_checkeds()

        # ---- se obtienen los datos/normalizado
        _v = []
        crude = False if self.normalization == 0 else True
        if self.visualization_mode == V_M_CLUSTER:
            _v = shape.g_data_for_fig(s_clusters, self.legends_cluster, crude)

            # ---- si se trae crudo
            if crude:
                if self.normalization == 1:
                    _v = self._nor_by_cluster(_v)
                elif self.normalization == 2:
                    _v = self._nor_by_selected(_v, shape.column_name)

            if self.clus_one_axe:
                _v = [pd.concat(_v)]

        if self.visualization_mode == V_M_SUMMARY:
            _ls = self.legends_summary
            _v = shape.g_resume_for_fig(s_clusters, _ls, crude)

            if self.summ_one_axe:
                _v = [pd.concat(_v)]

        if self.visualization_mode == V_M_CLUSTER_SUMMARY:

            # ---- todo en un axe
            _c, _r = shape.g_data_by_dr(s_clusters, self.legends_cluster,
                                        self.legends_summary, crude)
            if self.normalization == 1:
                # ----  normalizar cada cluster y recalcular resumen
                _c, _r = self._nor_by_cr_one(_c, _r, shape.column_name)

            elif self.normalization == 2:
                _c, _r = self._nor_by_cr_two(_c, _r, shape.column_name)

            # ---- mescla de datos de acuerdo a la opción seleccionada
            if self.clus_summ_axs[0]:
                for i, cr in enumerate(_c):
                    _v.append(cr)
                    _v.append(_r[i])
                _v = [pd.concat(_v)]

            if self.clus_summ_axs[1]:
                for i, cr in enumerate(_c):
                    _v.append(cr)
                    _v.append(_r[i])

            if self.clus_summ_axs[2]:
                for i, cr in enumerate(_c):
                    _v.append(pd.concat([cr, _r[i]]))

            if self.clus_summ_axs[3]:
                _v.append(pd.concat(_c))
                _v.append(pd.concat(_r))

        # ---- update figure
        self.kfigure.kdraw(_v)

    def _nor_by_cr_one(self, v, r, column_name):
        _r = []
        _v = self._nor_by_cluster(v)
        for i, df in enumerate(_v):
            leg = r[i][column_name].drop_duplicates()[0]
            _dnr = self.g_resume_by_df(df, leg, column_name)
            _r.append(_dnr)

        return _v, _r

    def _nor_by_cr_two(self, v, r, column_name):
        _r = []
        _v = self._nor_by_selected(v, column_name)
        for i, df in enumerate(_v):
            leg = r[i][column_name].drop_duplicates()[0]
            _dnr = self.g_resume_by_df(df, leg, column_name)
            _r.append(_dnr)
        return _v, _r

    def g_resume_by_df(self, df, legend, column_name):

        serie_mean = df[df.columns[:-1]].mean()
        df_mean = serie_mean.to_frame()
        df_mean = df_mean.transpose()
        df_mean[column_name] = legend
        return df_mean

    def _nor_by_cluster(self, v):
        _v = []
        for df in v:
            _v.append(self._nor(df))
        return _v

    def _nor_by_selected(self, v, column_name):
        _v = []
        df = pd.concat(v)
        df = self._nor(df)

        df_group = df.groupby(column_name)
        for _, group in df_group:
            _v.append(group)
        return _v

    def rangecero_nor(self, df):
        for cols in df.columns[:-1]:
            vals = df[cols]
            _min = vals.min()
            _max = vals.max()
            _vnor = [(x - _min) / (_max - _min) for x in vals]
            df[cols] = _vnor
        return df

    def _nor(self, df):
        def normalize(series):
            a = min(series)
            b = max(series)
            return (series - a) / (b - a)
        class_column = df.columns[-1]
        class_col = df[class_column]
        df = df.drop(class_column, axis=1).apply(normalize)
        df[class_column] = class_col
        return df

    def on_generate(self, event):
        self.data_selected = None
        # ---- controlar valores consistentes para clusters
        if not self.data_seccion.contain_elemens():
            KMessage(self.mainpanel, KMSG_EMPTY_DATA_GENERATE_CLUSTER).kshow()
            return

        if not self.data_seccion.checked_elemens():
            KMessage(self.mainpanel, KMSG_GENERATE_CLUSTER).kshow()
            return

        dfpopulation = self.clusters_seccion.get_dfpopulation()

        self.start_busy()
        task = GenerateClusterThread(self, dfpopulation)
        task.start()

    def on_filter(self, event):

        # ---- controlar valores consistentes para clusters
        if not self.clusters_seccion.contain_elemens():
            KMessage(self.mainpanel, KMSG_EMPTY_CLUSTER_DATA).kshow()
            return

        if self.data_selected is None:
            self.data_selected = SelectedData()
            _data = self.data_selected
            _shape = self.clusters_seccion.shape

            # --- opción de selección
            _data.option = 0

            # ---- cantidad de tendencias
            _data.count_tendency = _shape.clusters_count

            # ---- clusters más representativos - en número de individuos
            _data.more_repre = 0

            # ---- clusters menos representativos - en número de individuos
            _data.less_repre = 0

            # ---- clusters por valor de objetivos mayores
            _shape.name_objectives
            _data.max_objetives = list(_shape.name_objectives)
        if self.cluster_filter is None:
            self.cluster_filter = FilterClusterDialog(self, self.data_selected)
        else:
            self.cluster_filter.ShowModal()

        # ---- se cancela - retorna sin seleccionar
        if self.data_selected.cancel:
            return

        _data = self.clusters_seccion
        # ---- seleccionar clusters automáticamente
        if self.data_selected.option == 0:
            # ---- seleccionar los mas representativos
            # ---- seleccionar los menos representativos
            _max = self.data_selected.more_repre
            _ten = self.data_selected.count_tendency
            _min = self.data_selected.less_repre

            self.clusters_seccion.more_representative(_max, _ten - _min)

        if self.data_selected.option == 1:
            # seleccionar los menos representativos
            _o_max = self.data_selected.max_objetives_use
            _o_min = self.data_selected.min_objetives_use
            self.clusters_seccion.max_min_objective(_o_max, _o_min)

    def on_config(self, event):
        # ---- controlar valores consistentes para clusters
        if not self.data_seccion.contain_elemens():
            KMessage(self.mainpanel, KMSG_EMPTY_DATA_GENERATE_CLUSTER).kshow()
            return

        if not self.data_seccion.checked_elemens():
            KMessage(self.mainpanel, KMSG_GENERATE_CLUSTER).kshow()
            return

        if self.cluster_config is None:
            self.cluster_config = ClusterConfig(self)
        self.cluster_config.ShowModal()

    def on_nor_menu(self, evt):
        """Events from button menus"""

        e_obj = evt.GetEventObject()
        mitem = e_obj.FindItemById(evt.GetId())
        if mitem != wx.NOT_FOUND:
            label = mitem.GetItemLabel()
            self.tbtn0.SetLabel(label)
            self.normalization = self.NORMA_METO.index(label)

    def start_busy(self):
        pub().sendMessage(T.START_BUSY)
        self.tbtna.SetLabelColor(wx.Colour(191, 191, 191))
        self.tbtna.Disable()
        self.tbtnb.SetLabelColor(wx.Colour(191, 191, 191))
        self.tbtnb.Disable()
        self.sc_count_clusters.Disable()

    def stop_busy(self):
        pub().sendMessage(T.STOP_BUSY)
        self.tbtna.Enable()
        self.tbtna.SetLabelColor(wx.Colour(0, 0, 255))
        self.tbtnb.Enable()
        self.tbtnb.SetLabelColor(wx.Colour(0, 0, 255))
        self.sc_count_clusters.Enable()
        self.clusters_seccion.update_list()


class GenerateClusterThread(threading.Thread):
    def __init__(self, panel, dfpopulation):
        super(GenerateClusterThread, self).__init__()
        # Attributes
        self.panel = panel
        self.dfpopulation = dfpopulation

    def run(self):
        sel = self.panel.clusters_seccion.nb.GetSelection()
        if sel == CLUS_SHAPE:
            self.panel.clusters_seccion.\
                generate_shapes(self.dfpopulation,
                                self.panel.sc_count_clusters.GetValue(),
                                self.panel.normalization)
        if sel == CLUS_KMEANS:
            self.panel.clusters_seccion.\
                generate_kmeans(self.dfpopulation,
                                self.panel.sc_count_clusters.GetValue(),
                                self.panel.normalization)
        if sel == CLUS_BOTH:
            self.panel.clusters_seccion.\
                generate_shapes(self.dfpopulation,
                                self.panel.sc_count_clusters.GetValue(),
                                self.panel.normalization)
            self.panel.clusters_seccion.\
                generate_kmeans(self.dfpopulation,
                                self.panel.sc_count_clusters.GetValue(),
                                self.panel.normalization)
        wx.CallAfter(self.panel.stop_busy)


# -------------------                                  ------------------------
# -------------------                                  ------------------------
class ClusterSeccion(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)

        pub().subscribe(self.update_language, T.LANGUAGE_CHANGED)

        self.SetBackgroundColour('#FFFFFF')
        self.shape = None
        self.row_index = []

        sizer = wx.BoxSizer(wx.VERTICAL)

        panel_cluster = self.get_panel_cluster()

        self._checked_all = wx.CheckBox(self, -1, L('SELECT_ALL'))
        self._checked_all.Bind(wx.EVT_CHECKBOX, self.on_checked_all)

        sizer.Add(self._checked_all, flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(panel_cluster, 1, wx.EXPAND | wx.ALL)
        self.SetSizer(sizer)

    def get_panel_cluster(self):

        p = wx.Panel(self)
        self.nb = wx.Choicebook(p, -1)

        self.nb.AddPage(self.get_shape_panel(self.nb), "Shape")
        self.nb.AddPage(self.get_kmeans_panel(self.nb), "Kmeans")
        self.nb.AddPage(self.get_shape_kmeans_panel(self.nb), "Ambos")
        self.nb.SetSelection(CLUS_SHAPE)

        sizer = wx.BoxSizer()
        sizer.Add(self.nb, 1, wx.EXPAND | wx.ALL)
        p.SetSizer(sizer)

        return p

    def get_shape_panel(self, parent):

        panel = wx.Panel(parent)

        sizer = wx.BoxSizer(wx.VERTICAL)

        panel.shape_list = CheckListCtrl(panel)
        panel.shape_list.InsertColumn(0, L('NAME'))

        sizer.Add(panel.shape_list, 1, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(sizer)

        return panel

    def get_kmeans_panel(self, parent):
        panel = wx.Panel(parent)

        sizer = wx.BoxSizer(wx.VERTICAL)

        panel.kmeans_list = CheckListCtrl(panel)
        panel.kmeans_list.InsertColumn(0, L('NAME'))

        sizer.Add(panel.kmeans_list, 1, wx.EXPAND | wx.ALL, 5)

        panel.SetSizer(sizer)
        return panel

    def get_shape_kmeans_panel(self, parent):
        p = wx.Panel(parent)
        p.nb = wx.Notebook(p)

        p.nb.AddPage(self.get_shape_panel(p.nb), "Shape")
        p.nb.AddPage(self.get_kmeans_panel(p.nb), "Kmeans")

        sizer = wx.BoxSizer()
        sizer.Add(p.nb, 1, wx.EXPAND | wx.ALL)
        p.SetSizer(sizer)

        return p

    def g_for_view(self):
        position_checked = []
        position_unchecked = []
        for i, r_i in enumerate(self.row_index):
            if self.list_control.IsChecked(r_i):
                position_checked.append(i)
            else:
                position_unchecked.append(i)
        self.shape.cluster_checkeds = position_checked
        self.shape.cluster_uncheckeds = position_unchecked
        return self.shape

    def get_dfpopulation(self):
        # ----- bloques marcados para generar clusters
        blocks_checkeds = self.GetParent().data_seccion.\
                             get_checkeds_for_cluster()
        # ----- mezclar bloques marcados para crear un solo bloques
        blocks_checkeds_merge = []
        for _key, data in blocks_checkeds.iteritems():
            blocks_checkeds_merge.append(data[1].dframe)

        df_population = pd.concat(blocks_checkeds_merge)
        return df_population

    def generate_shapes(self, df_population, clus, nor):
        # ---- generar clusters
        self.shape = Shape(df_population, clus=clus, nor=nor)

    def generate_kmeans(self, df_population, clus, nor):
        # ---- generar clusters
        self.kmeans = Kmeans(df_population, clus=clus, nor=nor)

    def update_list(self):

        sel = self.nb.GetSelection()
        if sel == CLUS_SHAPE:
            self.shape_row_index = []
            shape_list = self.nb.GetPage(CLUS_SHAPE).shape_list
            self.populate_list(shape_list, self.shape.clusters,
                               self.shape_row_index)
        if sel == CLUS_KMEANS:
            self.kmeans_row_index = []
            kmeans_list = self.nb.GetPage(CLUS_KMEANS).kmeans_list
            self.populate_list(kmeans_list, self.kmeans.clusters,
                               self.kmeans_row_index)
        if sel == CLUS_BOTH:
            self.kmeans_row_index = []
            self.shape_row_index = []
            shape_list = self.nb.GetPage(CLUS_BOTH).nb.GetPage(0).shape_list
            self.populate_list(shape_list, self.shape.clusters,
                               self.shape_row_index)
            kmeans_list = self.nb.GetPage(CLUS_BOTH).nb.GetPage(1).kmeans_list
            self.populate_list(kmeans_list, self.kmeans.clusters,
                               self.kmeans_row_index)

    def populate_list(self, _list, _clusters, _row_index):
        # ----- limpiar clusters anteriores
        _list.DeleteAllItems()

        # ---- agregar clusters a la vista
        for i, c in enumerate(_clusters):
            name = 'cluster_' + str(i + 1) + ': ' + c.g_percent_format()
            index = _list.InsertStringItem(sys.maxint, name)
            _list.SetItemData(index, index)
            _row_index.append(index)

        _list.SetColumnWidth(0, wx.LIST_AUTOSIZE)

    def pre_un_select_all(self):
        sel = self.nb.GetSelection()
        if sel == CLUS_SHAPE:
            shape_list = self.nb.GetPage(CLUS_SHAPE).shape_list
            self.un_select_all(shape_list, self.shape_row_index)
        if sel == CLUS_KMEANS:
            kmeans_list = self.nb.GetPage(CLUS_KMEANS).kmeans_list
            self.un_select_all(kmeans_list, self.kmeans_row_index)
        if sel == CLUS_BOTH:
            shape_list = self.nb.GetPage(CLUS_BOTH).nb.GetPage(0).shape_list
            kmeans_list = self.nb.GetPage(CLUS_BOTH).nb.GetPage(1).kmeans_list
            self.un_select_all(shape_list, self.shape_row_index)
            self.un_select_all(kmeans_list, self.kmeans_row_index)

    def on_checked_all(self, event):
        if event.IsChecked():
            sel = self.nb.GetSelection()
            if sel == CLUS_SHAPE:
                shape_list = self.nb.GetPage(CLUS_SHAPE).shape_list
                self.select_all(shape_list, self.shape_row_index)
            if sel == CLUS_KMEANS:
                kmeans_list = self.nb.GetPage(CLUS_KMEANS).kmeans_list
                self.select_all(kmeans_list, self.kmeans_row_index)
            if sel == CLUS_BOTH:
                shape_list = self.nb.GetPage(CLUS_BOTH).nb.GetPage(0).shape_list
                kmeans_list = self.nb.GetPage(CLUS_BOTH).nb.GetPage(1).kmeans_list
                self.select_all(shape_list, self.shape_row_index)
                self.select_all(kmeans_list, self.kmeans_row_index)
        else:
            self.pre_un_select_all()

    def select_all(self, _list, _row_index):
        for index in _row_index:
            _list.CheckItem(index)

    def un_select_all(self, _list, _row_index):
        for index in _row_index:
            _list.CheckItem(index, False)

    def contain_elemens(self):
        sel = self.nb.GetSelection()
        if sel == CLUS_SHAPE:
            shape_list = self.nb.GetPage(CLUS_SHAPE).shape_list
            return shape_list.GetItemCount()
        if sel == CLUS_KMEANS:
            kmeans_list = self.nb.GetPage(CLUS_KMEANS).kmeans_list
            return kmeans_list.GetItemCount()
        if sel == CLUS_BOTH:
            shape_list = self.nb.GetPage(CLUS_BOTH).nb.GetPage(0).shape_list
            return shape_list.GetItemCount()

    def checked_elemens(self):
        sel = self.nb.GetSelection()
        if sel == CLUS_SHAPE:
            _list = self.nb.GetPage(CLUS_SHAPE).shape_list
            _row_index = self.shape_row_index
        if sel == CLUS_KMEANS:
            _list = self.nb.GetPage(CLUS_KMEANS).kmeans_list
            _row_index = self.kmeans_row_index
        if sel == CLUS_BOTH:
            _list = self.nb.GetPage(CLUS_BOTH).nb.GetPage(0).shape_list
            _row_index = self.shape_row_index
        for index in _row_index:
            if _list.IsChecked(index):
                return True
            return False

    # ---- funciones para análisis

    def more_representative(self, repre, less_rep):
        self.pre_un_select_all()

        # ---- más representativos
        for index in self.row_index[:repre]:
            self.list_control.CheckItem(index)

        # ---- menos representativos
        for index in self.row_index[less_rep:]:
            self.list_control.CheckItem(index)

    def less_representative(self, repre):
        self.pre_un_select_all()
        for index in self.row_index[repre:]:
            self.list_control.CheckItem(index)

    def max_min_objective(self, v_max, v_min):
        self.pre_un_select_all()
        for index in self.shape.g_clusters_max_min_in_var(v_max, v_min):
            self.list_control.CheckItem(index)

    def update_language(self, msg):
        self._checked_all.SetLabel(L('SELECT_ALL'))


# -------------------                                  ------------------------
# -------------------                                  ------------------------
class DataSeccion(wx.Panel):

    def __init__(self, parent, kblocks):
        wx.Panel.__init__(self, parent, -1)

        pub().subscribe(self.update_language, T.LANGUAGE_CHANGED)

        self.SetBackgroundColour('#FFFFFF')
        self.kblocks = kblocks
        self.row_index = []

        self.list_control = CheckListCtrl(self)
        sizer = wx.BoxSizer(wx.VERTICAL)

        self._checked_all = wx.CheckBox(self, -1, L('SELECT_ALL'))
        self._checked_all.Bind(wx.EVT_CHECKBOX, self.on_checked_all)

        sizer.Add(self._checked_all, flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.list_control, 1, wx.EXPAND)

        self.SetSizer(sizer)
        self.init()

    def init(self):
        self.list_control.InsertColumn(0, L('BLOCK'))

        for key, data in self.kblocks.iteritems():
            index = self.list_control.InsertStringItem(sys.maxint, data[0])
            self.list_control.SetItemData(index, key)
            self.row_index.append(index)

        self.list_control.SetColumnWidth(0, wx.LIST_AUTOSIZE)

    def get_checkeds(self):
        _subblocks_checked = []

        for index in self.row_index:
            if self.list_control.IsChecked(index):
                key = self.list_control.GetItemData(index)
                kblock = self.kblocks[key][1]
                _subblocks_checked.append(kblock.dframe)
        return _subblocks_checked

    def get_checkeds_for_cluster(self):
        block_checked = {}

        for index in self.row_index:
            if self.list_control.IsChecked(index):
                key = self.list_control.GetItemData(index)
                block_checked[key] = self.kblocks[key]
        return block_checked

    def on_checked_all(self, event):
        if event.IsChecked():
            for index in self.row_index:
                self.list_control.CheckItem(index)
        else:
            for index in self.row_index:
                self.list_control.CheckItem(index, False)

    def contain_elemens(self):
        return self.list_control.GetItemCount()

    def checked_elemens(self):
        for index in self.row_index:
            if self.list_control.IsChecked(index):
                return True
        return False

    def update_language(self, msg):
        self._checked_all.SetLabel(L('SELECT_ALL'))


class CheckListCtrl(wx.ListCtrl, CheckListCtrlMixin):

    def __init__(self, parent):
        wx.ListCtrl.__init__(self, parent, -1,
                             style=wx.LC_REPORT | wx.LC_NO_HEADER)
        CheckListCtrlMixin.__init__(self)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated)

    def OnItemActivated(self, evt):
        self.ToggleItem(evt.m_itemIndex)


# -------------------                                  ------------------------
# -------------------                                  ------------------------
class KBlock():

    def __init__(self, name, dframe):
        self.name = name
        self.dframe = dframe
#         self.dframe_nor = self.normalized()
        self.columns = self.g_columns(dframe)
        self.order = 0

    def normalized(self):
        class_column = 'Name'

        df = self.dframe.drop(class_column, axis=1)
        nor = (lambda x: x / np.linalg.norm(x))
        dframe_nor = DataFrame(nor(df.values), columns=df.columns.tolist())
        dframe_nor[class_column] = self.dframe[class_column].tolist()

        return dframe_nor

    def g_columns(self, df):
        cols = df.columns.tolist()
        return cols[:-1]


# -------------------                                  ------------------------
# -------------------                                  ------------------------
class KCluster():

    def __init__(self, name, dframe):
        self.name = name
        self.dframe = dframe
        # self.dframe_nor = self.normalized()
        self.columns = self.g_columns(dframe)
        self.order = 0

    def normalized(self):
        class_column = 'Name'

        df = self.dframe.drop(class_column, axis=1)
        nor = (lambda x: x / np.linalg.norm(x))
        dframe_nor = DataFrame(nor(df.values), columns=df.columns.tolist())
        dframe_nor[class_column] = self.dframe[class_column].tolist()

        return dframe_nor

    def g_columns(self, df):
        cols = df.columns.tolist()
        return cols[:-1]
