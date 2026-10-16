#!/usr/bin/env python3
"""Atomic HFCC + EiBi schedule refresh.
HFCC from verified official HTTPS, EiBi from a disclosed third-party HTTPS mirror.
Upstream EiBi TLS certificate is invalid; SSL verification stays enabled.
"""
import argparse,calendar,datetime,json,pathlib
from hfcc_html import fetch_records as fetch_hfcc
from eibi_mirror import fetch_records as fetch_eibi

def last_sunday(year,month):
    date=datetime.date(year,month,calendar.monthrange(year,month)[1])
    return date-datetime.timedelta(days=(date.weekday()+1)%7)

def season_for(date):
    if last_sunday(date.year,3)<=date<last_sunday(date.year,10):
        return "A"+str(date.year%100).zfill(2)
    year=date.year if date>=last_sunday(date.year,10) else date.year-1
    return "B"+str(year%100).zfill(2)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--season",help="For manual tests, e.g. A26")
    p.add_argument("--out",default="senderdaten.json")
    args=p.parse_args()
    now=datetime.datetime.now(datetime.timezone.utc)
    season=args.season or season_for(now.date())
    hfcc=fetch_hfcc(season)
    if len(hfcc)<100:raise ValueError("Invalid HFCC schedule: refusing replacement")
    ei=[];ei_stats={};status="ok"
    try:
        ei,ei_stats=fetch_eibi(season,today=now.date())
    except Exception as exc:
        status=f"unavailable: {type(exc).__name__}: {exc}"
        print("WARNING EiBi: "+status+"; verified HFCC data remain available")
    combined=hfcc+ei
    data={
        "generated":now.isoformat(),"season":season,
        "sources":{
            "HFCC":{"count":len(hfcc),"status":"ok","base":"https://new.hfcc.org/data/"},
            "EiBi":{"count":len(ei),"status":status,
                    "original":"http://www.eibispace.de/",
                    "mirror":"https://github.com/cdburgess75/SkyWave/tree/data",
                    **ei_stats}},
        "records":sorted(combined,key=lambda r:(r["frequency"],r["start"],r["name"],r["source"]))
    }
    target=pathlib.Path(args.out);tmp=target.with_suffix(target.suffix+".tmp")
    tmp.write_text(json.dumps(data,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    tmp.replace(target)
    print(f"Validated published schedules: {len(hfcc)} HFCC, {len(ei)} EiBi ({season})")
if __name__=="__main__":main()
