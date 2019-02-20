"""
Warning:
    this module is unfinished, so it is undocumented.
"""

# renders a standalone webpage with bokeh of trial data for all mice in the data folder
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


from glob import glob
import argparse
from bokeh.plotting import figure
from bokeh.io import show
from bokeh.models import ColumnDataSource, Legend, LegendItem
from bokeh.layouts import gridplot
from bokeh.transform import factor_cmap
from bokeh.palettes import Spectral10
from tqdm import tqdm
from rpilot.core import mouse
import colorcet as cc
import numpy as np
import json

def load_mouse_data(data_dir, steps=True, grad=True):
    """
    Args:
        data_dir (str): A path to a directory with :class:`~.core.mouse.Mouse` style hdf5 files
        steps (bool): Whether to return full trial-level data for each step
        grad (bool): Whether to return summarized step graduation data.

    """
    mouse_fn = [fn for fn in os.listdir(data_dir) if fn.endswith('.h5')]

    pilot_db = [fn for fn in os.listdir(data_dir) if fn == 'pilot_db.json'][0]
    pilot_db = os.path.join(data_dir, pilot_db)
    with open(pilot_db) as pilot_file:
        pilot_db = json.load(pilot_file)

    # simplify pilot db
    pilot_db = {k:v['mice'] for k, v in pilot_db.items()}
    pilot_dict = {}
    for pilot, mouselist in pilot_db.items():
        for ms in mouselist:
            pilot_dict[ms] = pilot

    for mouse_name in tqdm(mouse_fn):
        mouse_name = os.path.splitext(mouse_name)[0]
        amus = mouse.Mouse(mouse_name, dir=data_dir)

        # get trial data - corrects, targets, etc.
        if steps:
            step_data = amus.get_trial_data()
            step_data['mouse'] = mouse_name
            step_data['pilot'] = pilot_dict[mouse_name]
            try:
                all_mice_steps = all_mice_steps.append(step_data)
            except NameError:
                all_mice_steps = step_data

        if grad:
            try:
                # get historical graduation data
                grad_data = amus.get_step_history()
                grad_data['mouse'] = mouse_name
                grad_data['pilot'] = pilot_dict[mouse_name]
                try:
                    all_mice_grad = all_mice_grad.append(grad_data)
                except NameError:
                    all_mice_grad = grad_data
            except:
                pass

    if steps and not grad:
        return all_mice_steps
    elif grad and not steps:
        return all_mice_grad
    elif grad and steps:
        return all_mice_steps, all_mice_grad

def step_viewer(grad_data):
    mice = sorted(grad_data['mouse'].unique())
    palette = [cc.rainbow[i] for i in range(len(grad_data['pilot'].unique()))]

    current_step = grad_data.groupby('mouse').last().reset_index()
    current_step = current_step[['mouse', 'step_n', 'pilot']]

    pilots = current_step['pilot'].unique()
    pilot_colors = {p:palette[i] for i,p in enumerate(pilots) }
    pilot_colors = [pilot_colors[p] for p in current_step['pilot']]
    current_step['colors'] = pilot_colors




    p = figure(x_range=current_step['mouse'].unique(),title='Mouse Steps',
               plot_height=600,
               plot_width=1000)
    p.xaxis.major_label_orientation = np.pi / 2
    bars = p.vbar(x='mouse', top='step_n', width=0.9,
           fill_color=factor_cmap('pilot', palette=Spectral10, factors=pilots),
           legend='pilot',
           source=ColumnDataSource(current_step))
    p.legend.location = 'top_center'
    p.legend.orientation = 'horizontal'
    #p.add_layout(legend,'below')

    show(p)




def trial_viewer(step_data, grad_data):
    """
    Args:
        step_data:
        grad_data:
    """
    step_data.loc[step_data['response'] == 'L','response'] = 0
    step_data.loc[step_data['response'] == 'R','response'] = 1
    step_data.loc[step_data['target'] == 'L','target'] = 0
    step_data.loc[step_data['target'] == 'R','target'] = 1

    palette = [cc.rainbow[i] for i in range(len(step_data['mouse'].unique()))]
    palette = [cc.rainbow[i*15] for i in range(5)]

    mice = sorted(step_data['mouse'].unique())
    current_step = step_data.groupby('mouse').last().reset_index()
    current_step = current_step[['mouse','step']]

    plots = []
    p = figure(x_range=step_data['mouse'].unique(),title='Mouse Steps',
               plot_height=200)
    p.xaxis.major_label_orientation = np.pi / 2
    p.vbar(x=current_step['mouse'], top=current_step['step'], width=0.9)
    plots.append(p)
    for i, (mus, group) in enumerate(step_data.groupby('mouse')):
        meancx = group['correct'].ewm(span=100,ignore_na=True).mean()
        p = figure(plot_height=100,y_range=(0,1),title=mus)

        p.line(group['trial_num'], meancx, color=palette[group['step'].iloc[0]-1])
        plots.append(p)
    grid = gridplot(plots, ncols=1)
    show(grid)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Visualize Trial Data")
    parser.add_argument('-d', '--dir', help="Data directory")
    args = parser.parse_args()

    if not args.dir:
        data_dir = '/usr/rpilot/data'

        if not os.path.exists(data_dir):
            raise Exception("No directory file passed, and default location doesn't exist")

        raise Warning('No directory passed, loading from default location. Should pass explicitly with -d')
    else:
        data_dir = args.dir

    # load mouse data
    print('loading mouse data...')
    #step_data, grad_data = load_mouse_data(data_dir)
    grad_data = load_mouse_data(data_dir, steps=False, grad=True)

    step_viewer(grad_data)








