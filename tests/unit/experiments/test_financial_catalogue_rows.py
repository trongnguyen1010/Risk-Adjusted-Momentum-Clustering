import unittest
from delta_t1.ingestion.cafef_financial import digest
from delta_t1.experiments.financial_catalogue_rows import parse_catalogue


class CatalogueRowTests(unittest.TestCase):
    def body(self,href='/Handlers/DownloadFinancialStatement.ashx?FileName=X-17-Q3-Financial%20Statements.pdf',period='Q3/2017',symbol='X',filename='X-17-Q3-Financial Statements.pdf'):
        return (f'<div class="stockName">Company ({symbol} : HNX)</div><table><tr><td></td><td>{filename}</td><td>Báo cáo tài chính hợp nhất</td><td>{period}</td>'
            f'<td><a id="ctl_rptDownload_ctl01_lnkDownload" href="{href}">Tải về</a></td></tr></table><footer>Ngày31/12/2026</footer>').encode()

    def parse(self,body):return parse_catalogue(body,dict(symbol='X',registry_id='R1',provider_partition_id='PROVISIONAL:R1'),dict(exchange='HNX'),'raw.html',digest(body))

    def test_report_period_never_becomes_publication_date(self):
        row=self.parse(self.body())[0];self.assertEqual(row['status'],'OBSERVED_FINANCIAL_PDF_LINK_CANDIDATE')
        self.assertEqual((row['provider_year'],row['provider_quarter']),(2017,3));self.assertIsNone(row['publication_date'])
        self.assertIn('%20',row['resolved_url']);self.assertFalse(row['pit_ready'])

    def test_issuer_and_exchange_header_mismatch_fails(self):
        with self.assertRaises(ValueError):self.parse(self.body(symbol='OTHER'))
        with self.assertRaises(ValueError):self.parse(self.body().replace(b'HNX',b'HOSE'))

    def test_external_or_unsupported_handler_not_download_candidate(self):
        for url in ['https://other.example/Handlers/DownloadFinancialStatement.ashx?FileName=X.pdf','/Handlers/DownloadCompanyDocument.ashx?FileName=X.pdf']:
            self.assertEqual(self.parse(self.body(href=url))[0]['status'],'NONFINANCIAL_OR_UNSUPPORTED_HANDLER_LEAD')

    def test_filename_difference_and_unknown_period_retained_for_review(self):
        row=self.parse(self.body(period='6T/2017',filename='DIFFERENT.pdf'))[0]
        self.assertEqual(row['status'],'DOCUMENT_LINK_REVIEW_REQUIRED');self.assertIn('LINK_FILENAME_DIFFERS_FROM_CELL',row['reasons'])
        self.assertIn('PERIOD_LABEL_REVIEW_REQUIRED',row['reasons'])

    def test_other_issuer_filename_not_silently_assigned(self):
        row=self.parse(self.body(href='/Handlers/DownloadFinancialStatement.ashx?FileName=Y-2017.pdf',filename='Y-2017.pdf'))[0]
        self.assertIn('FILENAME_IDENTITY_REVIEW_REQUIRED',row['reasons'])

    def test_changed_raw_hash_is_fatal(self):
        with self.assertRaises(ValueError):parse_catalogue(self.body(),{},{} ,'raw.html','0'*64)

    def test_vietnamese_annual_period_is_not_a_publication_date(self):
        row=self.parse(self.body(period='Năm 2015'))[0]
        self.assertEqual((row['provider_year'],row['provider_quarter']),(2015,0));self.assertIsNone(row['publication_date'])


if __name__=='__main__':unittest.main()
