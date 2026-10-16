#!/usr/bin/env python3
"""Refresh schedule snapshot. Fail without replacing database when source fetch or parsing fails."""
import argparse,calendar,datetime,json,pathlib,tempfile,urllib.request
from import_schedules import build
def last_sunday(y,m):
 d=datetime.date(y,m,calendar.monthrange(y,m)[1]);return d-datetime.timedelta(days=(d.weekday()+1)%7)
def season_for(d):
 return ('A'+str(d.year%100).zfill(2)) if last_sunday(d.year,3)<=d<last_sunday(d.year,10) else ('B'+str((d.year if d>=last_sunday(d.year,10) else d.year-1)%100).zfill(2))
p=argparse.ArgumentParser();p.add_argument('--season');p.add_argument('--eibi-url');p.add_argument('--out',default='senderdaten.json');a=p.parse_args()
season=a.season or season_for(datetime.datetime.now(datetime.timezone.utc).date())
urls={'HFCC':f'https://new.hfcc.org/data/{season.lower()}/{season.lower()}allx2.zip','EiBi':a.eibi_url or f'http://eibispace.de/dx/sked-{season.lower()}.csv'}
with tempfile.TemporaryDirectory() as folder:
 paths={}
 for src,url in urls.items():
  dest=pathlib.Path(folder)/(src+('.zip' if src=='HFCC' else '.csv'))
  req=urllib.request.Request(url,headers={'User-Agent':'ToniWorldReceiver/0.2'})
  with urllib.request.urlopen(req,timeout=40) as response:
   data=response.read(15000001)
  if len(data)<1000 or len(data)>15000000:raise ValueError(f'{src} download size invalid')
  dest.write_bytes(data);paths[src]=dest
 result=build([paths['HFCC']],[paths['EiBi']],season)
 if min(result['counts'].values())<100:raise ValueError('Too few valid records: not replacing database')
 out=pathlib.Path(a.out);temp=out.with_suffix('.tmp')
 temp.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')),encoding='utf-8');temp.replace(out)
 print(f"Updated {len(result['records'])} records for {season}")
