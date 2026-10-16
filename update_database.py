#!/usr/bin/env python3
"""Atomic HFCC schedule update using official HTML broadcaster schedules.
EiBi is temporarily disabled because the upstream TLS certificate does not
validate. Never disable certificate verification or label HFCC-only as merged.
"""
import argparse,calendar,datetime,json,pathlib
from hfcc_html import fetch_records
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
    records=fetch_records(season)
    if len(records)<100:raise ValueError("Invalid empty/incomplete schedule")
    data={"generated":now.isoformat(),"season":season,
          "sources":{"HFCC":{"count":len(records),"base":"https://new.hfcc.org/data/"},
                     "EiBi":{"count":0,"status":"temporarily disabled: upstream TLS certificate"}},
          "records":records}
    path=pathlib.Path(args.out);tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(data,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    tmp.replace(path)
    print(f"Published {len(records)} verified HFCC schedule entries for {season}; EiBi pending")
if __name__=="__main__":main()
