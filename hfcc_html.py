"""Read official HFCC broadcaster schedule tables.
HTML schedule layout checked against HFCC A26 broadcaster pages (Oct 2026).
Reject unexpected formats rather than publishing incorrect data.
"""
from concurrent.futures import ThreadPoolExecutor,as_completed
from html.parser import HTMLParser
from html import unescape
import datetime
import re
from urllib.parse import urljoin
from urllib.request import urlopen,Request
BANDS=((4750,5060),(5600,6400),(6800,7600),(9200,10000),(11450,12250),(13400,14200),(15000,15900),(17100,18000),(21200,22000))
BASE="https://new.hfcc.org/data/"
def fetch(url):
    with urlopen(Request(url,headers={"User-Agent":"ToniWorldReceiver/0.3 (+personal research project)"}),timeout=35) as reply:
        data=reply.read(4_000_001)
    if len(data)>4_000_000:raise ValueError("HFCC page size limit exceeded")
    return data.decode("utf-8",errors="replace")
def minutes(value):
    s=str(value).strip().replace(":","").zfill(4)
    if not re.fullmatch(r"\d{4}",s):return None
    h,m=int(s[:2]),int(s[2:])
    return 60*h+m if (0<=h<=23 or (h==24 and m==0)) and m<60 else None
class Tables(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows=[];self.row=None;self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=="tr":self.row=[]
        elif tag in ("td","th") and self.row is not None:self.cell=[]
    def handle_data(self,data):
        if self.cell is not None:self.cell.append(data)
    def handle_endtag(self,tag):
        if tag in ("td","th") and self.cell is not None and self.row is not None:
            self.row.append(" ".join("".join(self.cell).split()));self.cell=None
        elif tag=="tr" and self.row is not None:
            if self.row:self.rows.append(self.row)
            self.row=None
def parse_schedule(html,season,code):
    parser=Tables();parser.feed(html)
    result=[]
    for c in parser.rows:
        if len(c)<13:continue
        try:freq=int(c[0])
        except ValueError:continue
        if not any(lo<=freq<=hi for lo,hi in BANDS):continue
        start,end=minutes(c[1]),minutes(c[2])
        if start is None or end is None:continue
        if not re.fullmatch(r"\d{1,2}[NS]\d{2}",c[8]):continue
        if not re.fullmatch(r"\d{1,3}[EW]\d{2}",c[9]):continue
        day_code=c[12]
        if not re.fullmatch(r"[1-7]{1,7}",day_code):continue
        days=sorted(set(int(z)-1 for z in day_code))
        try:power=float(c[11])
        except ValueError:power=None
        result.append({"frequency":freq,"start":start,"end":end,"days":days,
            "name":c[4],"language":c[6],"site":c[7],"latitude":c[8],
            "longitude":c[9],"azimuth":c[10],"power":power,
            "target":c[3],"fromDate":c[13] if len(c)>13 else "",
            "toDate":c[14] if len(c)>14 else "",
            "source":"HFCC","season":season,"code":code,
            "sourceURL":BASE+"schedbybrc.php?broadc="+code+"&seas="+season})
    return result
def broadcaster_codes(index_html):
    # The public index has schedules by broadcaster and by FMO.
    # Deduped broadcasters only: both sections use the same query field.
    codes=re.findall(r"broadc=([A-Z0-9]{2,5})",unescape(index_html),flags=re.I)
    return sorted(set(s.upper() for s in codes))
def fetch_records(season):
    index=fetch(BASE+season.lower()+"/")
    codes=broadcaster_codes(index)
    if len(codes)<15:raise ValueError(f"HFCC index format unexpected: only {len(codes)} broadcaster links")
    rows=[];errors=[]
    def work(code):
        url=BASE+"schedbybrc.php?broadc="+code+"&seas="+season
        return code,parse_schedule(fetch(url),season,code)
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures={executor.submit(work,code):code for code in codes}
        for future in as_completed(futures):
            try:
                code,group=future.result()
                rows.extend(group)
            except Exception as exc:errors.append(f"{futures[future]}: {exc}")
    if errors:print(f"WARNING: {len(errors)} of {len(codes)} HFCC broadcaster pages unavailable; examples: {'; '.join(errors[:3])}")
    if len(rows)<100:
        raise ValueError(f"HFCC parsed only {len(rows)} valid band rows across {len(codes)} broadcasters; refusing to publish")
    if len(errors)>len(codes)//3:
        raise ValueError(f"Too many HFCC pages failed ({len(errors)}/{len(codes)}); refusing partial publication")
    unique={}
    for r in rows:
        key=(r["frequency"],r["start"],r["end"],r["name"],r["site"],tuple(r["days"]))
        unique[key]=r
    print(f"HFCC: parsed {len(unique)} unique band schedules from {len(codes)} broadcaster pages")
    return sorted(unique.values(),key=lambda r:(r["frequency"],r["start"],r["name"]))
