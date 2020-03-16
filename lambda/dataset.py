import urllib.request
import json
import dateutil
import pandas as pd

class DataSet:
    
    def __init__(self, path, repo='pcm-dpc/COVID-19', date_cols=['data'], index_cols=['data'], resample=False):
        self.repo = repo
        self.path = path
        self.commit_url = f'https://api.github.com/repos/{self.repo}/commits?path={self.path}&page=1&per_page=1'
        with urllib.request.urlopen(self.commit_url) as url:
            data = json.loads(url.read().decode())
            date = data[0]['commit']['committer']['date']
            utc_date = dateutil.parser.parse(date)
            self.last_modified = utc_date.astimezone(dateutil.tz.gettz('Italy/Rome'))
        self.data_url = f'https://raw.githubusercontent.com/{self.repo}/master/{self.path}'
        self.df = pd.read_csv(self.data_url, parse_dates=date_cols, index_col=index_cols)
        if resample:
            self.df = self.df.resample('D').last()
        
    def __repr__(self):
        return (f'DataSet\n  repo: {self.repo}\n  path: {self.path}\n  commit_url: {self.commit_url}\n'
                f'  last_modified: {self.last_modified}\n  data_url: {self.data_url}\n  df: {len(self.df)} items')
