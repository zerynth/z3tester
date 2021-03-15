#   Zerynth - Toolchain - tests/test_ztc_commands.py
#   
#   Test for Zerynth Toolchain Commands
# 
# @Author: g.baldi
# 
# @Date:   2017-05-16 12:49:17
# @Last Modified by:   m.cipriani
# @Last Modified time: 2017-05-16 15:30:36

import unittest
import sys
from base import *
import os
import json
import random

##
## @brief      Class for test ztc commands.
##
class TestZTCCommands(unittest.TestCase):

    ##
    ## @brief      built and run zerynth tooclhain command
    ##
    ## @param      self  The object
    ## @param      args  The arguments
    ##
    ## @return     process.returncode, process.stdout
    ##
    def cmd(self,*args):
        # run ZTC
        pycmd = "python3"
        if fs.exists(fs.path(fs.homedir(),self.homepath,"sys","python")):
            if sys.platform.startswith("win"):
                pycmd = fs.path(fs.homedir(),self.homepath,"sys","python","python.exe")
            else:
                pycmd = fs.path(fs.homedir(),self.homepath,"sys","python","bin","python")
        e,out,_ = proc.run(pycmd,fs.path(fs.dirname(__file__),"..","ztc.py"),*args,outfn=log)
        return e,out

    ##
    ## @brief      create minimal setup for zerynth cfg;
    ##             create a Zerynth user and login or fail
    ##
    ## @param      self  The object
    ##
    ## @return     None
    ##
    def setUp(self):
        # setting cfg
        self.testpath = fs.path(fs.homedir())
        if sys.platform.startswith("win"):
            self.testpath = fs.path(self.testpath,"zerynth2_test")
            self.homepath = "zerynth2"
        else:
            self.testpath = fs.path(self.testpath,".zerynth2_test")
            self.homepath = ".zerynth2"
        self.cfgdir = fs.path(self.testpath,"cfg")
        fs.makedirs(self.cfgdir)
        self.assertTrue(fs.exists(self.cfgdir))
        fs.set_json({"version":"r2.0.7"},fs.path(self.cfgdir,"config.json"))
        # create user
        e,out = self.cmd("register","user@zerynth.com","password","User")
        if e:
            # if the user already exists login
            print("LOGIN")
            e,out=self.cmd("--traceback","login","--user","user@zerynth.com","--passwd","password")
            if e:
                sys.exit(e)

    ##
    ## @brief      Test for Get Profile Command in --pretty and normal format;
    ##             in --pretty format validates the json object
    ##
    ## @param      self  The object
    ##
    ## @return     None
    ##
    def test_user_get_profile(self):
        print("PROFILE PRETTY")
        e,out = self.cmd("-J","--pretty","profile")
        self.assertEqual(e,0)
        self.assertIsInstance(json.loads(out), dict)
        print("PROFILE NORMAL")
        e,out = self.cmd("profile")
        self.assertEqual(e,0)

    ##
    ## @brief      Test for Set Profile Command with right and wrong data
    ##             chosen randomly and final check for right data stored and 
    ##             wrong data discarded
    ##
    ## @param      self  The object
    ##
    ## @return     None
    ##
    def test_user_set_profile(self):
        e,out = self.cmd("-J","--pretty","profile")
        self.assertEqual(e,0)
        profile_old = json.loads(out)
        profile_set = {
            "name":"name",
            "surname":"surname",
            "country":"Italy",
            "age":"26-35",
            "job":"iot_architect",
            "company":"test_company",
            "website":"test_website"
        }
        profile = {
            "name":random.choice(["name"," ","wrong_name"]),
            "surname":random.choice(["surname"," ","wrong_surname"]),
            "country":random.choice(["Italy", " ", "wrong_conutry"]),
            "age":random.choice(["26-35", " ", "wrong_age"]),
            "job":random.choice(["iot_architect", " ", "wrong_job"]),
            "company":random.choice(["test_company", " "]),
            "website":random.choice(["test_website", " "])
        }
        for k,v in profile.items():
            print("PROFILE SET", k.upper(), "-->", v)
            e,out = self.cmd("profile", "--set", "--"+k, v)
            self.assertEqual(e,0)
        # check profile set
        e,out = self.cmd("-J","--pretty","profile")
        self.assertEqual(e,0)
        profile_new = json.loads(out)
        for k,v in profile_set.items():
            if profile[k] == profile_set[k]:
                self.assertEqual(profile_new[k],profile[k])
            else:
                self.assertEqual(profile_new[k],profile_old[k])

    ##
    ## @brief      remove testpath folder and its content
    ##
    ## @param      self  The object
    ##
    ## @return     None
    ##
    def tearDown(self):
        fs.rmtree(self.testpath)