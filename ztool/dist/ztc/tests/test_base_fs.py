import unittest
from base import *
import os
import tempfile
import shutil
import json

class TestBaseFs(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tmpfile = os.path.join(self.tmpdir,"ztestfile")
        self.srcfile =  os.path.join(self.tmpdir,"zsrcfile")
        self.dstfile =  os.path.join(self.tmpdir,"zdstfile")

    def test_fs_json(self):
        # create json file
        fs.set_json({"test":True},self.tmpfile)
        self.assertTrue(os.path.exists(self.tmpfile))

        # read it
        res = fs.get_json(self.tmpfile)
        self.assertTrue(res["test"])

        # corrupt it and read it back again
        fs.write_file(b'\x00\x00\x00\x00',self.tmpfile)
        with self.assertRaises(json.decoder.JSONDecodeError):
            fs.get_json(self.tmpfile)

    def test_fs_abspath(self):
        pth = "."
        pth1 = fs.path(pth,"1")
        pth2 = fs.apath(pth1)
        self.assertNotEqual(pth1,pth2)

    def test_fs_rw(self):
        # create binary src
        wdata = b'\x00\x01\x02\x03'
        fs.write_file(wdata,self.srcfile)
        self.assertTrue(os.path.exists(self.srcfile))

        # read back binary
        rdata = fs.readfile(self.srcfile,"b")
        self.assertEqual(wdata,rdata)

        # create string src
        wdata = "teststring"
        fs.write_file(wdata,self.srcfile)
        self.assertTrue(os.path.exists(self.srcfile))

        # read back string
        rdata = fs.readfile(self.srcfile)
        self.assertEqual(wdata,rdata)

    def test_fs_copy(self):
        # create binary src
        wdata = b'\x00\x01\x02\x03'
        fs.write_file(wdata,self.srcfile)
        self.assertTrue(os.path.exists(self.srcfile))

        # copy1
        fs.copyfile(self.srcfile,self.dstfile)
        self.assertTrue(os.path.exists(self.dstfile))
        rdata = fs.readfile(self.dstfile,"b")
        self.assertEqual(wdata,rdata)

        # delete dst
        fs.rm_file(self.dstfile)
        self.assertFalse(os.path.exists(self.dstfile))

        # copy2
        fs.copyfile2(self.srcfile,self.dstfile)
        self.assertTrue(os.path.exists(self.dstfile))
        rdata = fs.readfile(self.dstfile,"b")
        self.assertEqual(wdata,rdata)



    def tearDown(self):
        shutil.rmtree(self.tmpdir)
