"""Testing the OAI-PMH Harvest Module."""
import unittest
from harvestDPLA import dataAPIcall
import re
import os

error_urls = [400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 415, 416, 500,
              501, 502, 504, 505, 511, 520]
time_urls = [503, 504, 522, 524]
url_base = 'http://httpstat.us/'
apikey = os.environ['DPLA_APIKEY']


class DataAPIcall(unittest.TestCase):

    def setUp(self):
        pass

    def testErrorURLs(self):
        """Should Exit Process. To Do: Testing Exit Message."""
        for error_code in error_urls:
            error_url = url_base + str(error_code)
            with self.assertRaises(SystemExit) as cm:
                dataAPIcall(error_url, '?api_key=' + apikey, '1')
                self.assertEqual(cm.exception.code, 1)

    def testGoodURLs(self):
        """Should return remoteData XML object."""
        pass

    def testRedirectURLs(self):
        """Should Reset Process with new URL then Process + return XML."""
        pass


class WriteHarvest(unittest.TestCase):

    def setUp(self):
        pass

    def testNoResumption(self):
        """TBD. """
        pass

    def testResumption(self):
        """TBD."""
        pass

    def testWriteXML(self):
        """TBD."""
        pass


if __name__ == '__main__':
    unittest.main()
