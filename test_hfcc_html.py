import unittest
from hfcc_html import parse_schedule,broadcaster_codes,minutes
class TestHFCC(unittest.TestCase):
    def test_minutes(self):
        self.assertEqual(minutes("2130"),1290)
        self.assertEqual(minutes("2400"),1440)
        self.assertIsNone(minutes("2460"))
    def test_broadcaster_index(self):
        html='<a href="schedbybrc.php?broadc=CRI&amp;seas=A26">CRI</a><a href="schedbybrc.php?broadc=BBC&amp;seas=A26">BBC</a>'
        self.assertEqual(broadcaster_codes(html),["BBC","CRI"])
    def test_real_table_shape(self):
        sample='''<table><tr><th>Frequency</th><th>Start UTC</th></tr>
        <tr><td>6075</td><td>0000</td><td>0100</td><td>41</td>
        <td>China Radio International</td><td>RTC</td><td>Eng</td>
        <td>Kashi</td><td>39N30</td><td>076E00</td><td>174</td>
        <td>100</td><td>1234567</td><td>29-Mar-2026</td><td>25-Oct-2026</td><td></td></tr></table>'''
        rows=parse_schedule(sample,'A26','CRI')
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['frequency'],6075)
        self.assertEqual(rows[0]['name'],'China Radio International')
        self.assertEqual(rows[0]['days'],[0,1,2,3,4,5,6])
        self.assertEqual(rows[0]['start'],0)
        self.assertEqual(rows[0]['end'],60)
    def test_reject_shifted_fields(self):
        bad='<table><tr><td>6075</td><td>0000</td><td>0100</td><td>41</td><td>CRI</td><td>RTC</td><td>Eng</td><td>Kashi</td><td>174</td><td>100</td><td>39N30</td><td>076E00</td><td>1234567</td></tr></table>'
        self.assertEqual(parse_schedule(bad,'A26','CRI'),[])
if __name__=='__main__':unittest.main()
