"""EiBi CSV parser and HTTPS mirror fetch with strict provenance/shape checks.

EiBi copyright/redistribution: Eike Bierwirth, eibispace.de/dx/README.TXT
Upstream has an invalid HTTPS certificate; never disable TLS validation.
The HTTPS transport is a third-party mirror, identified in published metadata.
"""
import csv
import datetime as dt
import io
import json
import re
import urllib.request

MIRROR_BASE="https://raw.githubusercontent.com/cdburgess75/SkyWave/data/"
ORIGINAL_URL="http://www.eibispace.de/dx/"
BANDS=((4750,5060),(5600,6400),(6800,7600),(9200,10000),(11450,12250),(13400,14200),(15000,15900),(17100,18000),(21200,22000))
WEEKDAY={"Mo":1,"Tu":2,"We":3,"Th":4,"Fr":5,"Sa":6,"Su":0}

def fetch_https(name,max_bytes=1_500_000):
    if name not in ("eibi.json",) and not re.fullmatch(r"sked-[ab]\d{2}\.csv",name):
        raise ValueError("Unexpected mirror path")
    req=urllib.request.Request(MIRROR_BASE+name,headers={"User-Agent":"ToniWorldReceiver/0.4"})
    with urllib.request.urlopen(req,timeout=40) as response:
        if not response.geturl().startswith("https://raw.githubusercontent.com/"):
            raise ValueError("Unexpected source redirect")
        blob=response.read(max_bytes+1)
    if len(blob)>max_bytes:raise ValueError("Mirror file too large")
    return blob

def time_minutes(value):
    m=re.fullmatch(r"(\d{4})-(\d{4})",value.strip())
    if not m:return None
    def t(s):
        hour,minute=int(s[:2]),int(s[2:])
        if hour==24 and minute==0:return 1440
        if hour>23 or minute>59:return None
        return hour*60+minute
    a,b=t(m.group(1)),t(m.group(2))
    return (a,b) if a is not None and b is not None and a!=b else None

def days_from_code(text):
    text=text.strip()
    if not text:return list(range(7))
    if re.fullmatch(r"[1-7]{1,7}",text):
        return sorted({int(c)%7 for c in text})
    # Examples: We-Mo, Mo-Fr, Tu,Th, SaSu, Sa/Su
    found=set()
    for token in re.split(r"[,/]",text):
        token=token.strip()
        if "-" in token:
            chunks=token.split("-")
            if len(chunks)!=2 or chunks[0] not in WEEKDAY or chunks[1] not in WEEKDAY:return None
            d=WEEKDAY[chunks[0]]
            while True:
                found.add(d)
                if d==WEEKDAY[chunks[1]]:break
                d=(d+1)%7
        elif token in WEEKDAY:found.add(WEEKDAY[token])
        elif re.fullmatch(r"(Mo|Tu|We|Th|Fr|Sa|Su){2,3}",token):
            found.update(WEEKDAY[token[i:i+2]] for i in range(0,len(token),2))
        else:return None
    return sorted(found) if found else None

def season_date(value,year):
    """EiBi partial-season dates: ddmm (not [last-heard-date])."""
    if not re.fullmatch(r"\d{4}",value):return None
    try:return dt.date(year,int(value[2:]),int(value[:2]))
    except ValueError:return None

def valid_partial(row,today):
    start=season_date(row[9],today.year)
    stop=season_date(row[10],today.year)
    if start is None or stop is None:return False
    if stop>=start:return start<=today<=stop
    # A/B seasonal entries may span the new year.
    return today>=start or today<=stop

def parse_csv(raw,season,today=None):
    if today is None:today=dt.datetime.now(dt.timezone.utc).date()
    rows=list(csv.reader(io.StringIO(raw),delimiter=";"))
    if not rows or not rows[0] or not rows[0][0].lower().startswith("khz:"):
        raise ValueError("EiBi CSV header not recognized")
    parsed=[];unresolved=0;inactive=0;out_of_band=0
    for row in rows[1:]:
        if len(row)<11:continue
        try:frequency=float(row[0])
        except ValueError:continue
        if not any(a<=frequency<=b for a,b in BANDS):
            out_of_band+=1;continue
        tm=time_minutes(row[1])
        if tm is None:continue
        days=days_from_code(row[2])
        if days is None:
            unresolved+=1;continue  # no invented daily schedule for special codes
        persist=row[8].strip()
        try:code=int(persist)
        except ValueError:continue
        if code==8 or (code==4 and season.startswith("A")) or (code==5 and season.startswith("B")):
            inactive+=1;continue
        if code==6 and not valid_partial(row,today):
            inactive+=1;continue
        name=row[4].strip()
        if not name:continue
        freq=int(frequency) if frequency.is_integer() else frequency
        parsed.append({"frequency":freq,"start":tm[0],"end":tm[1],
            "days":days,"name":name,"language":row[5].strip(),
            "site":row[7].strip(),"target":row[6].strip(),
            "country":row[3].strip(),"source":"EiBi","season":season,
            "dayCode":row[2].strip(),"persistence":code,
            "sourceURL":ORIGINAL_URL+f"sked-{season.lower()}.csv",
            "mirrorURL":MIRROR_BASE+f"sked-{season.lower()}.csv"})
    key=lambda r:(r["frequency"],r["start"],r["end"],r["name"],r["country"],r["site"],tuple(r["days"]))
    distinct={key(r):r for r in parsed}
    return sorted(distinct.values(),key=lambda r:(r["frequency"],r["start"],r["name"])),{"skippedAmbiguousDays":unresolved,"skippedInactive":inactive,"outOfBand":out_of_band,"totalCSVRows":len(rows)-1}

def fetch_records(season,today=None):
    name=f"sked-{season.lower()}.csv"
    meta=json.loads(fetch_https("eibi.json",50_000))
    info=meta.get("seasons",{}).get(season.lower())
    if not isinstance(info,dict):raise ValueError("Season missing from mirror metadata")
    blob=fetch_https(name)
    if len(blob)!=int(info["bytes"]):raise ValueError("Mirror size differs from metadata")
    if abs(len(blob.splitlines())-1-int(info["rows"]))>2:
        raise ValueError("Mirror row count differs from metadata")
    records,statistics=parse_csv(blob.decode("utf-8-sig",errors="replace"),season,today=today)
    if len(records)<500:
        raise ValueError(f"Only {len(records)} EiBi band records parsed; refusing update")
    timestamp=dt.datetime.fromtimestamp(int(meta["ts"])/1000,dt.timezone.utc)
    if dt.datetime.now(dt.timezone.utc)-timestamp>dt.timedelta(days=35):
        raise ValueError("EiBi mirror is stale")
    statistics["mirrorUpdated"]=timestamp.isoformat()
    statistics["mirrorURL"]=MIRROR_BASE+name
    statistics["upstream"]=ORIGINAL_URL+name
    print(f"EiBi: {len(records)} band entries via TLS-verified third-party mirror; {statistics}")
    return records,statistics
