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

import wx
from wx.lib.agw.genericmessagedialog import GenericMessageDialog
from wx.lib.agw.genericmessagedialog import GMD_USE_GRADIENTBUTTONS


KMSG_EMPTY_DATA_SELECTED = 0
H_EMPTY_DATA_SELECTED = 'Selección Vacío de Datos'
EMPTY_DATA_SELECTED = "Selección de datos para Visualizar.\n\n" + \
    "No has seleccionado ninguna opción de \n" + \
    "Datos para Visualizar, checkee algunas de\n" + \
    "las casillas disponibles en la parte\n" + \
    'superior derecha "Datas" o "Clusters".\n\n' + \
    "            TAVA-TOOL  "

KMSG_EMPTY_CLUSTER_DATA = 3
H_EMPTY_CLUSTER_DATA = 'Visualización de Clusters'
EMPTY_CLUSTER_DATA = "Falta Generar Clusters\n\n" + \
    "Debe generar los clusters correspondientes para\n" + \
    "luego poder visualizarlos:\n" + \
    "1. Seleccione almenos un dato.\n" + \
    "2. Establesca cantidad de clusters.\n" + \
    "3. Presione button generar cluster.\n\n" + \
    "            TAVA-TOOL  "
KMSG_EMPTY_CLUSTER_SELECTED = 4
H_EMPTY_CLUSTER_SELECTED = 'Visualización de Clusters'
EMPTY_CLUSTER_SELECTED = "Falta Seleccionar Clusters\n\n" + \
    "Debe seleccionar almenos un cluster para ser \n" + \
    "visualizado:\n" + \
    "1. Seleccionar almenos un clusters.\n" + \
    "2. Vuelva a a intentar visualizar.\n\n" + \
    "            TAVA-TOOL  "

KMSG_EMPTY_DATA_GENERATE_CLUSTER = 5
H_EMPTY_DATA_GENERATE_CLUSTER = 'Generación de Clusters'
EMPTY_EMPTY_DATA_GENERATE_CLUSTER = "No Contiene Datos\n\n" + \
    "No tiene datos para ser agrupados. La lista\n" + \
    "de datos que se encuentra en la esquina superior\n" + \
    "derecho se encuentra vacía. Agregue datos a la Vista.\n\n" + \
    "            TAVA-TOOL  "
KMSG_GENERATE_CLUSTER = 6
H_GENERATE_CLUSTER = 'Generación de Clusters'
EMPTY_GENERATE_CLUSTER = "Falta Seleccionar Datos\n\n" + \
    "Debe seleccionar almenos un dato para ser \n" + \
    "agrupado. La lista de datos se encuentra en\n" + \
    "la parte superior derecho:\n" + \
    "1. Seleccionar almenos un dato.\n" + \
    "2. Establesca cantidad de clusters.\n" + \
    "3. Vuelva a a intentar agrupar.\n\n" + \
    "            TAVA-TOOL  "


K_ICON_INFORMATION = wx.ICON_INFORMATION
K_ICON_QUESTION = wx.ICON_QUESTION
K_ICON_ERROR = wx.ICON_ERROR
K_ICON_HAND = wx.ICON_HAND
K_ICON_EXCLAMATION = wx.ICON_EXCLAMATION

K_OK = wx.OK
K_CANCEL = wx.CANCEL
K_YES_NO = wx.YES_NO
K_YES_DEFAULT = wx.YES_DEFAULT
K_NO_DEFAULT = wx.NO_DEFAULT


from wx import GetTranslation as L


class KMessage():

    def __init__(self, parent, key_message, key_ico=K_ICON_INFORMATION,
                 key_button=K_OK):

        self.parent = parent

        if key_message == KMSG_EMPTY_DATA_SELECTED:
            self.h_msg = H_EMPTY_DATA_SELECTED
            self.m_msg = EMPTY_DATA_SELECTED
            self.k_ico = key_ico
            self.k_but = key_button
        elif key_message == KMSG_EMPTY_CLUSTER_DATA:
            self.h_msg = L('H_EMPTY_CLUSTER_DATA') # H_EMPTY_CLUSTER_DATA
            self.m_msg = L('EMPTY_CLUSTER_DATA')
            self.k_ico = key_ico
            self.k_but = key_button
        elif key_message == KMSG_EMPTY_CLUSTER_SELECTED:
            self.h_msg = H_EMPTY_CLUSTER_SELECTED
            self.m_msg = EMPTY_CLUSTER_SELECTED
            self.k_ico = key_ico
            self.k_but = key_button
        elif key_message == KMSG_EMPTY_DATA_GENERATE_CLUSTER:
            self.h_msg = H_EMPTY_DATA_GENERATE_CLUSTER
            self.m_msg = EMPTY_EMPTY_DATA_GENERATE_CLUSTER
            self.k_ico = key_ico
            self.k_but = key_button
        elif key_message == KMSG_GENERATE_CLUSTER:
            self.h_msg = H_GENERATE_CLUSTER
            self.m_msg = EMPTY_GENERATE_CLUSTER
            self.k_ico = key_ico
            self.k_but = key_button

        else:
            self.h_msg = 'Defaul'
            self.m_msg = 'Defaul'
            self.k_ico = key_ico
            self.k_but = key_button

    def kshow(self):
        dlg = GenericMessageDialog(self.parent, self.m_msg,
                                   self.h_msg,
                                   self.k_ico | self.k_but |
                                   GMD_USE_GRADIENTBUTTONS)
        dlg.ShowModal()
        dlg.Destroy()
