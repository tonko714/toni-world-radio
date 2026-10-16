import datetime as dt
import unittest
from eibi_mirror import parse_csv,days_from_code,time_minutes,valid_partial

HEADER="kHz:75;Time(UTC):93;Days:59;ITU:49;Station:201;Lng:49;Target:62;Remarks:135;P:35;Start:60;Stop:60;"
class EiBiTests(unittest.TestCase):
    def test_time(self):
        self.assertEqual(time_minutes("0000-2400"),(0,1440))
        self.assertEqual(time_minutes("2023-0600"),(1223,360))
        self.assertIsNone(time_minutes("2460-0100"))
    def test_days(self):
        self.assertEqual(days_from_code(""),list(range(7)))
        self.assertEqual(days_from_code("Mo-Fr"),[1,2,3,4,5])
        self.assertEqual(days_from_code("We-Mo"),[0,1,3,4,5,6])
        self.assertEqual(days_from_code("SaSu"),[0,6])
        self.assertEqual(days_from_code("157"),[0,1,5])
        self.assertIsNone(days_from_code("irr"))
        self.assertIsNone(days_from_code("24Oct"))
    def test_parse_real_eibi_shape(self):
        s=HEADER+"\n"+"9600;1200-1300;;CHN;China Radio Int.;E;SEA;k;0;;\n"+"7300;2200-2300;Mo-Fr;CHN;China Radio Int.;EPO;Eu;ka;1;;\n"
        records,stats=parse_csv(s,"A26",dt.date(2026,10,16))
        self.assertEqual(len(records),2)
        self.assertEqual(records[1]["language"],"E")
        self.assertEqual(records[0]["days"],[1,2,3,4,5])
        self.assertEqual(records[0]["frequency"],7300)
    def test_inactive_and_special_days(self):
        s=HEADER+"\n"+"9600;1200-1300;irr;CHN;Uncertain;E;SEA;k;0;;\n"+"9600;1200-1300;;CHN;Inactive;E;SEA;k;8;;\n"+"9600;1200-1300;;CHN;Winter only;E;SEA;k;4;;\n"
        rows,stats=parse_csv(s,"A26",dt.date(2026,10,16))
        self.assertEqual(rows,[])
        self.assertEqual(stats["skippedAmbiguousDays"],1)
        self.assertEqual(stats["skippedInactive"],2)
    def test_partial(self):
        row=["9600","1200-1300","","CHN","Some","E","SEA","k","6","0110","2410"]
        self.assertTrue(valid_partial(row,dt.date(2026,10,16)))
        self.assertFalse(valid_partial(row,dt.date(2026,10,25)))
if __name__=="__main__":unittest.main()
