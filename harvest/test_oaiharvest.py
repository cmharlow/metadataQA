"""Testing the OAI-PMH Harvest Module."""
import unittest
from harvestOAI import getFile
from harvestOAI import writeHarvest
import re
import requests
import codecs

error_urls = [400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 415, 416, 500,
              501, 502, 504, 505, 511, 520]
time_urls = [503, 504, 522, 524]
redirect_url = 'http://bit.ly/2ncrczY'
url_base = 'http://httpstat.us/'
good_url = 'https://ecommons.cornell.edu/dspace-oai/request'
good_opts = 'ListRecords&set=com_1813_2936&metadataPrefix=oai_dc'


class TestGetFile(unittest.TestCase):

    def setUp(self):
        pass

    def testErrorURLs(self):
        """Should Exit Process. To Do: Testing Exit Message."""
        for error_code in error_urls:
            error_url = url_base + str(error_code)
            with self.assertRaises(SystemExit) as cm:
                getFile(error_url, 'ListRecords', sleepTime=0)
                self.assertEqual(cm.exception.code, 1)

    def testGoodURLs(self):
        """Should return remoteData XML object."""
        golden_out = open('harvest/fixtures/test_goodurl_fixture.txt', 'r').read()
        golden_out = re.sub('<responseDate>(.*)</responseDate>', '', golden_out)
        with open('harvest/fixtures/test_goodurl_test.txt', 'w') as fh:
            test_out = getFile(good_url, good_opts)
            fh.write(test_out)
        test_fout = open('harvest/fixtures/test_goodurl_test.txt', 'r').read()
        test_fout = re.sub('<responseDate>(.*)</responseDate>', '', test_fout)
        self.assertEqual(test_fout, golden_out)

    def testRedirectURLs(self):
        """Should Reset Process with new URL then Process + return XML."""
        golden_out = open('harvest/fixtures/test_goodurl_fixture.txt', 'r').read()
        golden_out = re.sub('<responseDate>(.*)</responseDate>', '', golden_out)
        with open('harvest/fixtures/test_redirecturl_test.txt', 'w') as fh:
            test_out = getFile(good_url, good_opts)
            fh.write(test_out)
        test_fout = open('harvest/fixtures/test_redirecturl_test.txt', 'r').read()
        test_fout = re.sub('<responseDate>(.*)</responseDate>', '', test_fout)
        self.assertEqual(test_fout, golden_out)


class WriteHarvest(unittest.TestCase):

    def setUp(self):
        pass

    def testNoResumption(self):
        """Pass Good OAI-PMH Link, Info, & Filename, Return non-0 Count."""
        id_resp = requests.get('https://ecommons.cornell.edu/dspace-oai/request?verb=ListIdentifiers&metadataPrefix=oai_dc&set=com_1813_2939')
        golden_recCount = len(re.findall('<identifier>', id_resp.text))
        dataClean = open('harvest/fixtures/test_OAINoResumptionDataClean_fixture.txt').read()
        ofile = codecs.lookup('utf-8')[-1](open('harvest/fixtures/test_OAINoResumptionDataOut_test.xml', 'wb'))
        test_recCount = writeHarvest('https://ecommons.cornell.edu/dspace-oai', dataClean, ofile)
        ofile.close()
        self.assertEqual(golden_recCount, test_recCount)

    def testResumption(self):
        """TBD."""
        pass

    def testWriteXML(self):
        """TBD."""
        pass


if __name__ == '__main__':
    unittest.main()
