import os
import shutil
import logging
import re

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

class TimeSeriesViz:

    def __init__(self, series, last_modified, fig_folder=None, csv_folder=None, figsize=(16, 10)):
        self.series = series
        self.last_modified = last_modified
        self.figsize = figsize
        self.fig_folder = fig_folder
        self.csv_folder = csv_folder
        self.logger = logging.getLogger()
    
    def diff(self):
        return self.series - self.series.shift()
    
    def _config_axis(self, ax=None, figsize=None):
        _figsize = figsize if figsize is not None else self.figsize
        if ax is None:
            fig, ax = plt.subplots(figsize=_figsize)
        else:
            fig = plt.gcf()
        return fig, ax

    def _get_title(self, title):
        full_title = title
        if self.last_modified is not None:
            full_title += f'\n(dati aggiornati: {self.last_modified:%d/%m/%Y %H:%M:%S})'
        return full_title
    
    def _save_fig(self, fig_name):
        series_name = re.sub("\W", '_', self.series.name).lower()
        fn_date = f'{series_name}-{fig_name}-{self.last_modified:%Y%m%d}.png'
        fn_last = f'{series_name}-{fig_name}.png'
        if self.fig_folder is not None:
            fn_date = os.path.join(self.fig_folder, fn_date)
            fn_last = os.path.join(self.fig_folder, fn_last)
        plt.savefig(fn_date)
        shutil.copyfile(fn_date, fn_last)
        self.logger.info(f'Figure saved to {fn_date} and {fn_last}')
        return fn_date, fn_last
        
    def _save_csv(self, df, csv_name):
        series_name = re.sub("\W", '_', self.series.name).lower()
        fn_date = f'{series_name}-{csv_name}-{self.last_modified:%Y%m%d}.csv'
        fn_last = f'{series_name}-{csv_name}.csv'
        if self.csv_folder is not None:
            fn_date = os.path.join(self.csv_folder, fn_date)
            fn_last = os.path.join(self.csv_folder, fn_last)
        df.to_csv(fn_date)
        shutil.copyfile(fn_date, fn_last)
        self.logger.info(f'Data saved to {fn_date} and {fn_last}')
        return fn_date, fn_last
    
    def show_series(self, title, save_fig=False, save_csv=False, **kwargs):
        fig, ax = self._config_axis(**kwargs)
        ax.plot(self.series.index, self.series)
        ax.set_title(self._get_title(title))
        ax.xaxis.grid(True, which='major')
        ax.yaxis.grid(True, which='major')
        locator = mdates.DayLocator(interval=2)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
        ax.xaxis.set_label_text('')
        ax.set_xlim((self.series.index.min(), self.series.index.max()))
        if save_fig:
            self._save_fig('series')
        if save_csv:
            self._save_csv(self.series.to_frame(), 'series')

    def show_new(self, title, save_fig=False, save_csv=False, **kwargs):
        fig, ax = self._config_axis(**kwargs)
        diff = self.diff()
        ax.bar(diff.index, diff, align='center')
        ax.set_title(self._get_title(title))
        ax.yaxis.grid(True, which='major')
        locator = mdates.DayLocator(interval=2)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
        ax.set_xlim((diff.index.min() + pd.Timedelta(days=.5), diff.index.max() + pd.Timedelta(days=.5)))
        if save_fig:
            self._save_fig('new')
        if save_csv:
            self._save_csv(diff.to_frame(), 'new')
        
    def show_growth_factor(self, title, lookback=1, window=3, raw=True, sma=True, ema=True, ylim=None, 
                           save_fig=False, save_csv=False, **kwargs):
        diff = self.diff()
        growth_factor = diff / diff.shift(lookback)
        fig, ax = self._config_axis(**kwargs)
        ax.set_title(self._get_title(title))
        
        gf_sma = growth_factor.rolling(window).mean()
        gf_sma.name = f'{diff.name} (SMA {window} giorni)'

        gf_ema = growth_factor.ewm(span=window).mean()
        gf_ema.name = f'{diff.name} (EMA {window} giorni)'

        if raw:
            ax.plot(growth_factor.index, growth_factor, label=growth_factor.name)

        if sma:
            ax.plot(gf_sma.index, gf_sma, label=gf_sma.name)

        if ema:
            ax.plot(gf_ema.index, gf_ema, label=gf_ema.name)

        ax.axhline(1.0, linestyle='--', linewidth=1, color='r')
        ax.xaxis.grid(True, which='major')
        ax.yaxis.grid(True, which='major')
        locator = mdates.DayLocator(interval=2)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
        ax.xaxis.set_label_text('')
        ax.set_xlim((self.series.index.min(), self.series.index.max()))
        ax.legend()
        if ylim is not None:
            ax.set_ylim(ylim)
        if save_fig:
            self._save_fig('gf')
        if save_csv:
            df = pd.DataFrame({growth_factor.name: growth_factor, gf_sma.name: gf_sma, gf_ema.name: gf_ema})
            self._save_csv(df, 'gf')



class OverviewViz:
    
    def __init__(self, area_name, df, last_modified=None, fig_folder=None, csv_folder=None, figsize=(20, 16)):
        self.area_name = area_name
        self.df = df
        self.figsize = figsize
        self.last_modified = last_modified
        self.fig_folder = fig_folder
        self.logger = logging.getLogger()
        total_series = df['totale_casi'].resample('D').last()
        total_series.name = f'totali {area_name}'
        self.total_viz = TimeSeriesViz(series=total_series, last_modified=None, 
                                       fig_folder=fig_folder, csv_folder=csv_folder)
        deaths_series = df['deceduti'].resample('D').last()
        deaths_series.name = f'deceduti {area_name}'
        self.deaths_viz = TimeSeriesViz(series=deaths_series, last_modified=None, 
                                        fig_folder=fig_folder, csv_folder=csv_folder)
        ti_series = df['terapia_intensiva'].resample('D').last()
        ti_series.name = f'terapia intensiva {area_name}'
        self.ti_viz = TimeSeriesViz(series=ti_series, last_modified=None, 
                                    fig_folder=fig_folder, csv_folder=csv_folder)

    def _save_fig(self, fig_name):
        series_name = re.sub("\W", '_', self.area_name).lower()
        fn_date = f'{series_name}-{fig_name}-{self.last_modified:%Y%m%d}.png'
        fn_last = f'{series_name}-{fig_name}.png'
        if self.fig_folder is not None:
            fn_date = os.path.join(self.fig_folder, fn_date)
            fn_last = os.path.join(self.fig_folder, fn_last)
        plt.savefig(fn_date)
        shutil.copyfile(fn_date, fn_last)
        self.logger.info(f'Figure saved to {fn_date} and {fn_last}')
        return fn_date, fn_last
        
    def show_overview(self, save_fig=False):
        plt.figure(figsize=self.figsize)
        fig_names = ['', 'deceduti', 'in terapia intensiva']
        vizualizers = [self.total_viz, self.deaths_viz, self.ti_viz]
        for idx, (fig_name, viz) in enumerate(zip(fig_names, vizualizers)):
            viz.show_series(title=f'Casi {fig_name}{" " if fig_name else ""}in {self.area_name}', ax=plt.subplot(331 + idx * 3))
            viz.show_new(title=f'Nuovi casi giornalieri {fig_name}{" " if fig_name else ""}in {self.area_name}', ax=plt.subplot(332 + idx * 3))
            viz.show_growth_factor(title=f'Tasso di crescita dei casi {fig_name}{" " if fig_name else ""}in {self.area_name}', 
                                   sma=False, ax=plt.subplot(333 + idx * 3), ylim=(0, 5))
        plt.suptitle(f'Situazione COVID-19 in {self.area_name}\n(dati aggiornati: {self.last_modified:%d/%m/%Y %H:%M:%S})',
                    fontsize='x-large', y=0.95)
        plt.subplots_adjust(hspace=0.3)
        if save_fig:
            return self._save_fig('overview')
        return None
