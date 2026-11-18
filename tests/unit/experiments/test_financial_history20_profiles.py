import unittest
from delta_t1.ingestion.cafef_financial import digest
from delta_t1.experiments.financial_history20_profiles import parse_profile


class ProfileEvidenceTests(unittest.TestCase):
    def fixture(self):
        return dict(registry_id='REG1',symbol='ACV',exchange='UPCOM',provider_partition_id='PROVISIONAL:REG1',
                    proposed_company_type='Regular',profile_url='https://web.stockbiz.vn/Stocks/ACV/Overview.aspx')

    def html(self,header='Company (ACV : UPCOM)',links=True):
        text='<div class="stockName"><span>'+header+'</span></div>'
        if links:
            for kind,code in [('Sector','2000'),('Industry','2770')]:
                text+=f'<a id="ctl_lnk{kind}" href="/IndustryOverview.aspx?Code={code}">{kind}</a>'
        return text.encode()

    def parse(self,body):
        return parse_profile(body,self.fixture(),'raw.html',digest(body))

    def test_exact_current_quote_does_not_open_history_or_scores(self):
        row=self.parse(self.html())
        self.assertEqual(row['status'],'CURRENT_PROFILE_OBSERVED')
        self.assertEqual(row['categories']['industry']['provider_code'],'2770')
        self.assertFalse(row['historical_identity_ready']);self.assertFalse(row['score_applicability_accepted'])

    def test_wrong_issuer_or_exchange_requires_review(self):
        for header in ['Company (XYZ : UPCOM)','Company (ACV : HOSE)']:
            self.assertIn('CURRENT_PROVIDER_IDENTITY_DIFFERENCE',self.parse(self.html(header))['reasons'])

    def test_footer_category_does_not_replace_labelled_provider_links(self):
        row=self.parse(self.html(links=False)+b'<footer><a href="/IndustryOverview.aspx?Code=2000">Industry</a></footer>')
        self.assertIn('MISSING_PROVIDER_SECTOR_OR_INDUSTRY',row['reasons'])

    def test_conflicting_quote_headers_are_not_silently_chosen(self):
        row=self.parse(self.html()+b'<div class="stockName">Other (XYZ : HOSE)</div>')
        self.assertIn('MISSING_OR_AMBIGUOUS_QUOTE_HEADER',row['reasons'])

    def test_external_category_link_and_conflicting_labels_rejected(self):
        body=self.html()+b'<a id="x_lnkSector" href="https://other.example/IndustryOverview.aspx?Code=1000">Other</a>'
        self.assertIn('UNRECOGNIZED_CATEGORY_LINK',self.parse(body)['reasons'])
        body=self.html()+b'<a id="x_lnkSector" href="/IndustryOverview.aspx?Code=1000">Other</a>'
        self.assertIn('CONFLICTING_CATEGORY_LABELS',self.parse(body)['reasons'])

    def test_hash_mismatch_is_integrity_error(self):
        with self.assertRaises(ValueError):parse_profile(self.html(),self.fixture(),'raw.html','0'*64)


if __name__=='__main__':unittest.main()
