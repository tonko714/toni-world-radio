#!/usr/bin/env python3
"""HFCC and EiBi import: do not infer unknown sender names or transmission sites."""
import argparse,csv,datetime,io,json,pathlib,re,zipfile
BANDS=[(4750,5060),(5600,6400),(6800,7600),(9200,10000),(11450,12250),(13400,14200),(15000,15900),(17100,18000),(21200,22000)]
def in_band(f):return any(a<=f<=b for a,b in BANDS)
def minutes(v):
 s=str(v).strip().replace(':','').zfill(4)
 if not re.fullmatch(r'\d{4}',s):return None
 h,m=int(s[:2]),int(s[2:])
 return 60*h+m if (h<24 or (h==24 and m==0)) and m<60 else None
def read(path):
 p=pathlib.Path(path)
 if p.suffix.lower()=='.zip':
  with zipfile.ZipFile(p) as z:
   names=[n for n in z.namelist() if n.lower().endswith(('.txt','.csv'))]
   names.sort(key=lambda n:(not ('all' in n.lower() or 'sked' in n.lower()),len(n)))
   if not names:raise ValueError('Archive contains no text schedule')
   return z.read(names[0]).decode('utf-8-sig',errors='replace')
 return p.read_text(encoding='utf-8-sig',errors='replace')
def eibi(raw,season):
 rows=list(csv.reader(io.StringIO(raw),delimiter=';'))
 if rows and len(rows[0])<5:rows=list(csv.reader(io.StringIO(raw),delimiter=','))
 if not rows:return []
 header=[re.sub(r'[^a-z0-9]','',s.lower()) for s in rows[0]]
 def col(*keys):return next((i for i,k in enumerate(header) if k in keys),-1)
 f,t,n,l,d,site=col('khz','freq','frequency'),col('timeutc','time'),col('station','name'),col('lng','language','lang'),col('days'),col('remarks','site','transmitter')
 if min(f,t,n)<0:raise ValueError('Unsupported EiBi header')
 out=[]
 for row in rows[1:]:
  def get(i):return row[i].strip() if i>=0 and i<len(row) else ''
  try:freq=int(float(get(f)))
  except ValueError:continue
  if not in_band(freq):continue
  tm=re.fullmatch(r'(\d{3,4})\s*[-–]\s*(\d{3,4})',get(t))
  if not tm:continue
  start,end=minutes(tm[1]),minutes(tm[2])
  if start is None or end is None:continue
  dc=get(d);days=sorted({int(i)%7 for i in dc}) if re.fullmatch(r'[1-7]+',dc) else None
  out.append(dict(frequency=freq,start=start,end=end,days=days,dayCode=dc,name=get(n),language=get(l),site=get(site),source='EiBi',season=season))
 return out
def hfcc(raw,season):
 out=[]
 for line in raw.splitlines():
  a=[s.strip() for s in line.split(';')]
  if len(a)<13:continue
  try:freq=int(a[0])
  except ValueError:continue
  if not in_band(freq):continue
  st,en=minutes(a[1]),minutes(a[2])
  if st is None or en is None:continue
  if not re.fullmatch(r'\d{1,2}[NS]\d{2}',a[8]) or not re.fullmatch(r'\d{1,3}[EW]\d{2}',a[9]):continue
  dc=a[12];days=sorted({(int(i)-1)%7 for i in dc}) if re.fullmatch(r'[1-7]+',dc) else None
  try:power=float(a[11])
  except ValueError:power=None
  out.append(dict(frequency=freq,start=st,end=en,days=days,dayCode=dc,name=a[4],language=a[6],site=a[7],latitude=a[8],longitude=a[9],azimuth=a[10],power=power,source='HFCC',season=season,code=a[4],target=a[3]))
 return out
def build(hfcc_files=(),eibi_files=(),season='A26'):
 records=hfcc_records=eibi_records=None
 hfcc_records=[r for p in hfcc_files for r in hfcc(read(p),season)]
 eibi_records=[r for p in eibi_files for r in eibi(read(p),season)]
 records=hfcc_records+eibi_records
 if not records:raise ValueError('No valid rows, refusing replacement')
 seen={}
 for r in records:seen[(r['source'],r['frequency'],r['start'],r['end'],r['name'],r.get('site'),r.get('dayCode'))]=r
 return {'generated':datetime.datetime.now(datetime.timezone.utc).isoformat(),'season':season,'counts':{'HFCC':len(hfcc_records),'EiBi':len(eibi_records)},'records':sorted(seen.values(),key=lambda r:(r['frequency'],r['start'],r['name']))}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--hfcc',action='append',default=[]);p.add_argument('--eibi',action='append',default=[]);p.add_argument('--season',default='A26');p.add_argument('-o','--output',default='senderdaten.json');a=p.parse_args()
 data=build(a.hfcc,a.eibi,a.season);dst=pathlib.Path(a.output);tmp=dst.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8');tmp.replace(dst)
 print(data['counts'])
