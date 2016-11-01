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
# Creado:  1/9/2016                                        ###
#                                                            ###
# ##############################################################
'''

from matplotlib import patches as mpatches
from matplotlib import pyplot as plt
from matplotlib.path import Path
from matplotlib.projections import register_projection
from matplotlib.projections.polar import PolarAxes
from matplotlib.spines import Spine

import numpy as np
from views.wrapper.wraview.vgraphic.fuse import square_plot, g_colors


# #######################################################################
#        Radar Chart (circle - polygon)
# #######################################################################
def unit_poly_verts(theta):
    """Return vertices of polygon for subplot axes.

    This polygon is circumscribed by a unit circle centered at (0.5, 0.5)
    """
    x0, y0, r = [0.5] * 3
    verts = [(r * np.cos(t) + x0, r * np.sin(t) + y0) for t in theta]
    return verts


def radar_factory(num_vars, frame):
    """Create a radar chart with `num_vars` axes.

    This function creates a RadarAxes projection and registers it.

    Parameters
    ----------
    num_vars : int
        Number of variables for radar chart.
    frame : {'circle' | 'polygon'}
        Shape of frame surrounding axes.

    """
    # calculate evenly-spaced axis angles
    theta = np.linspace(0, 2 * np.pi, num_vars, endpoint=False)
    # rotate theta such that the first axis is at the top
    theta += np.pi / 2

    def draw_poly_patch(self):
        verts = unit_poly_verts(theta)
        return plt.Polygon(verts, closed=True, edgecolor='k')

    def draw_circle_patch(self):
        # unit circle centered on (0.5, 0.5)
        return plt.Circle((0.5, 0.5), 0.5)

    patch_dict = {'polygon': draw_poly_patch, 'circle': draw_circle_patch}
    if frame not in patch_dict:
        raise ValueError('unknown value for `frame`: %s' % frame)

    class RadarAxes(PolarAxes):

        name = 'radar'
        # use 1 line segment to connect specified points
        RESOLUTION = 1
        # define draw_frame method
        draw_patch = patch_dict[frame]

        def fill(self, *args, **kwargs):
            """Override fill so that line is closed by default"""
            closed = kwargs.pop('closed', True)
            return super(RadarAxes, self).fill(closed=closed, *args, **kwargs)

        def plot(self, *args, **kwargs):
            """Override plot so that line is closed by default"""
            lines = super(RadarAxes, self).plot(*args, **kwargs)
            for line in lines:
                self._close_line(line)

        def _close_line(self, line):
            x, y = line.get_data()
            # FIXME: markers at x[0], y[0] get doubled-up
            if x[0] != x[-1]:
                x = np.concatenate((x, [x[0]]))
                y = np.concatenate((y, [y[0]]))
                line.set_data(x, y)

        def set_varlabels(self, labels):
            self.set_thetagrids(np.degrees(theta), labels)

        def _gen_axes_patch(self):
            return self.draw_patch()

        def _gen_axes_spines(self):
            if frame == 'circle':
                return PolarAxes._gen_axes_spines(self)
            # The following is a hack to get the spines (i.e. the axes frame)
            # to draw correctly for a polygon frame.

            # spine_type must be 'left', 'right', 'top', 'bottom', or `circle`.
            spine_type = 'circle'
            verts = unit_poly_verts(theta)
            # close off polygon by repeating first vertex
            verts.append(verts[0])
            path = Path(verts)

            spine = Spine(self, spine_type, path)
            spine.set_transform(self.transAxes)
            return {'polar': spine}

    register_projection(RadarAxes)
    return theta


def radarchart(dframes, class_column, fig, ax_conf, rc_config, colors):

    s_row, s_col = square_plot(len(dframes), False)
    for i, df in enumerate(dframes):
        # ---- configuración de axe para radar chart
        spoke_labels = df.columns[:-1]
        theta = radar_factory(len(spoke_labels), rc_config.type)
        ax = fig.add_subplot(s_row, s_col, i + 1, projection='radar')
        ax.set_varlabels(spoke_labels)

        _radarchart(df, ax, fig, ax_conf, class_column, rc_config, theta,
                    colors[i])
    return fig


def _radarchart(frame, ax, fig, ax_conf, class_column, rc_config,
                theta, color_values=None):

    alpha = 0.15
    _classes_colors = []

    # ---- varaibles globales
    n = len(frame)
    classes = frame[class_column].drop_duplicates()
    class_col = frame[class_column]
    df = frame.drop(class_column, axis=1)

    # ---- selección de colores - automático/personalizado
    if color_values is None:
        color_values = g_colors(len(classes), ax_conf.color)
    colors = dict(zip(classes, color_values))

    # ---- configuración de relleno
    if rc_config.fill:
        for ii in range(n):
            d = df.iloc[ii].values
            kls = class_col.iat[ii]
            ax.plot(theta, d, color=colors[kls])
            ax.fill(theta, d, facecolor=colors[kls], alpha=alpha)
    else:
        for ii in range(n):
            d = df.iloc[ii].values
            kls = class_col.iat[ii]
            ax.plot(theta, d, color=colors[kls])

    # ---- configuración de leyenda
    if ax_conf.legend_show:

        r_patch = []
        classes = []

        for k in colors.keys():
            r_patch.append(mpatches.Patch(color=colors[k]))
            classes.append(k)

        fig.legend(r_patch, classes)

    # ---- configuración de grid
    if ax_conf.grid_lines:
        ax.grid(True)
        ax.grid(color=ax_conf.grid_color,
                linestyle=ax_conf.grid_lines_style,
                linewidth=ax_conf.grid_linewidth,
                alpha=ax_conf.grid_color_alpha)
    else:
        ax.grid(False)
