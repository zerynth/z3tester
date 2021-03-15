"""
.. _ztc-cmd-user:

************************
Account related commands
************************

The ZTC allows the user to authenticate against the Zerytnh backend and modify profile information.

The following commands are available:

* :ref:`login <ztc-cmd-user-login>` to retrieve an authentication token.
* :ref:`reset <ztc-cmd-user-reset>` reset to request a password reset.
* :ref:`profile <ztc-cmd-user-profile>` set and get profile information.

    """
from base import *
import os
import click
import time
import webbrowser
import json
import base64
import threading
import socket
import http.server
from urllib.parse import urlparse,parse_qs

def check_installation():
    try:
        instfile = fs.path(env.cfg,"installation.json")
        inst = fs.get_json(instfile)
        if not inst.get("uid") and inst.get("offline",None) is not None:
            # save installation info
            try:
                res = zpost(env.api.installation,{"installer":"offline" if inst["offline"] else "online"})
                if res.status_code==200:
                    rj = res.json()
                    if rj["status"]=="success":
                        inst["uid"]=rj["data"]["inst_uid"]
                        fs.set_json(inst,instfile)
                    else:
                        warning(rj["code"],"after checking installation")
                else:
                    warning(res.status_code,"while checking installation")
            except:
                warning("Exception while sending installation data")
    except Exception as e:
        warning("Exception while checking installation",str(e))


supported_local_logins = ["vscode","zstudio","ide"]

@cli.command("login",help="Obtain an authentication token")
@click.option("--token",default=None,help="set the token in non interactive mode")
@click.option("--user",default=None,help="username for manual login")
@click.option("--passwd",default=None,help="password for manual login")
@click.option("--local",default=None,help="get token from localhost")
@click.option("--check",flag_value=True, default=False,help="check if logged")
@click.option("--origin",default=None,help="origin for 3dparty auth")
@click.option("--origin_username",default=None,help="origin username for 3dparty auth")
def __login(token,user,passwd,origin,origin_username,local,check):
    """
.. _ztc-cmd-user-login:

Login
-----

The :command:`login` command enables the user to retrieve an authentication token. The token is used in most ZTC commands to communicate with the Zerynth backend.

The :command:`login` can be issued in interactive and non interactive mode. Interactive mode is started by typing: ::

    ztc login

The ZTC opens the default system browser to the login/registration page and waits for user input.

In the login/registration page, the user can login providing a valid email and the corresponding password. 
It is also possible (and faster) to login using Google plus or Facebook OAuth services. If the user do not have a Zerynth account it is possible to register
providing a valid email, a nick name and a password. Social login is also available for registration via OAuth.

Once a correct login/registration is performed, the browser will display an authentication token. Such token can be copied and pasted to the ZTC prompt.

.. warning:: multiple logins with different methods (manual or social) are allowed provided that the email linked to the social OAuth service is the same as the one used in the manual login.


Non interactive mode is started by typing: ::

    ztc login --token authentication_token

The :samp:`authentication_token` can be obtained by manually opening the login/registration `page <https://backend.zerynth.com/v1/sso>`_


.. warning:: For manual registrations, email address confirmation is needed. An email will be sent at the provided address with instructions.

    """
    if check:
        res = zget(url=env.api.profile)
        rj = res.json()
        if rj["status"]=="success":
            dname = rj["data"]["display_name"]
            mail = rj["data"]["email"]

            if env.human:
                info("Credentials valid")
            else:
                log_json({"logged":True, "nickname":dname, "email":mail})
        else:
            if env.human:
                warning("Credentials are invalid")
            else:
                log_json({"logged":False})
        return




    if not token and not user and not passwd and not local:
        log("Hello!")
        log("In a few seconds a browser will open to the login page")
        log("Once logged, copy the authorization token and paste it here")
        time.sleep(1)
        webbrowser.open(env.api.sso + "?redirect="+env.api.zdmredirect)
        token = input("Paste the token here and press enter -->")

    if not token and local:
        if local.lower() not in supported_local_logins:
            fatal("Unknown local login provider:",local)
        # open a localhost server on a free port
        # open web browser for login
        # catch jwt on localhost redirect
        do_local_sso(local)
        return

    if token:
        env.set_token(token)
        zget(env.api.sso + "?redirect="+env.api.zdmredirectstudio)
        check_installation()
    elif user and passwd:
        try:
            head = {"Authorization":"Basic "+base64.standard_b64encode(bytes(user+":"+passwd,"utf-8")).decode("utf-8")}
            params = {}
            if origin and origin_username:
                params["origin"]=origin
                params["origin_username"]=origin_username
            res = zget(env.api.user,head,params,auth=False)
            if res.status_code==200:
                rj = res.json()
                if rj["status"]=="success":
                    env.set_token(rj["data"]["token"])
                    zget(env.api.sso + "?redirect="+env.api.zdmredirect)
                    info("Ok")
                else:
                    fatal(rj["message"])
            else:
                fatal(res.status_code,"while logging user")
        except Exception as e:
            fatal("Error!",e)
    else:
        fatal("Token needed!")





class TokenRequestHandler(http.server.BaseHTTPRequestHandler):
    result = {
        "token": "",
        "done": False,
        "error": ""
    }


    def do_GET(self):
        o = urlparse(self.path)
        if o.path.startswith("/zerynth/local"):
            params = parse_qs(o.query)
            if "token" in params and "redirect" in params:
                token = params["token"][0]
                redirect = params["redirect"][0]
                # TODO: checkthe validity of the token here
                TokenRequestHandler.result["token"]=token
                TokenRequestHandler.result["error"]=""
                TokenRequestHandler.result["done"]=True
                try:
                    env.set_token(token)
                except:
                    TokenRequestHandler.result["token"]=""
                    TokenRequestHandler.result["error"]="Invalid credentials"
                    redirect=redirect+"/error"

                # redirect to success/error page
                self.send_response(308)
                self.send_header("Location",redirect)
                self.end_headers()
                # self.wfile.write("".encode("utf-8"))
                print("Returning",o)
                return
            else:
                TokenRequestHandler.result["error"]="Missing login response parameters"
                TokenRequestHandler.result["done"]=True

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write("".encode("utf-8"))
        print("Exiting",o)


def do_start_local_webserver():
    # find free port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    port = s.getsockname()[1]
    s.close()


    # create server
    server_address = ("", port)
    httpd = http.server.HTTPServer(server_address, TokenRequestHandler)
    log("Starting http local server on port",port)

    # start server in a thread
    th = threading.Thread(target = httpd.serve_forever)
    th.start()

    return port, httpd, th




def do_local_sso(provider):
    ok = False
    try:
        port, server, th = do_start_local_webserver()
        webbrowser.open(env.api.sso + "?redirect="+env.api.zdmlocalredirect+provider.lower()+"/"+str(port))

        timeout=120  # must be divisible by 20 to have tic - toc sequence
        log("Hello!")
        log("In a few seconds a browser will open the login page")
        log("Once logged, you can go back to",provider)
        while th.is_alive() and timeout>0:
            time.sleep(1)
            if timeout%20==0:
                log("tic")
            elif timeout%10==0:
                log("toc")
            timeout-=1
            if TokenRequestHandler.result["done"]:
                break

        if TokenRequestHandler.result["done"] and not TokenRequestHandler.result["error"] and TokenRequestHandler.result["token"]:
            info("Everything seems good!")
            ok = True

        if not ok:
            warning("Something wrong!")
            if not TokenRequestHandler.result["done"]:
                warning("- never received a login response")
            if not th.is_alive():
                warning("- webserver not started")
            if TokenRequestHandler.result["error"]:
                warning("- there was an error:",TokenRequestHandler.result["error"])
            if not TokenRequestHandler.result["token"]:
                warning("- login failed")
    except Exception as e:
        warning("Can't start SSO local web server",e)

    try:
        # shutdown server
        server.server_close()
        th.join(timeout=2)
    except:
        pass

    if not ok:
        error("Login not successful")
        ## force exit, there might be non daemon threads waiting in the background
        os._exit(1)
    else:
        os._exit(0)



@cli.command(help="Password reset. \n\n Arguments: \n\n EMAIL: email linked to the user account")
@click.argument("email")
def reset(email):
    """
.. _ztc-cmd-user-reset:

Reset Password
--------------

If a manual registration has been performed, it is possible to change the password by issuing a password reset: ::

    ztc reset email

where :samp:`email` is the email address used in the manual registration flow. An email with instruction will be sent to such address in order to allow a password change.

.. note:: on password change, all active sessions of the user will be invalidated and a new token must be retrieved.

    """
    try:
        res = zget(env.api.pwd_reset,auth=False,params={"email":email})
        if res.status_code!=200:
            fatal(res.status_code,"from endpoint")
        else:
            rj = res.json()
            if rj["status"]=="success":
                log("Reset instructions have been sent to",email)
            else:
                fatal("Can't reset password:",rj["message"])
    except Exception as e:
        fatal("Can't reset password:",e)

@cli.command("logout",help="Close current session. A new login is needed")
def __logout():
    """
.. _ztc-cmd-user-logout:

Logout
------

Delete current session with the following command ::

    ztc logout


.. note:: it will be necessary to login again.

    """
    env.rm_token()


@cli.command(help="Manage account info.\n\n")
@click.option("--set","__set",flag_value=True, default=False, help="Flag to set/modify profile informations.")
@click.option("--name","name",default="",help="Your Name")
@click.option("--surname","surname",default="",help="Your Surname")
@click.option("--job","job",default="",help="Your Job")
@click.option("--country","country",default="",help="Your Country")
@click.option("--company","company",default="",help="Your Company")
@click.option("--age","age",default="",help="Your Age")
@click.option("--website","website",default="",help="Your Website")
def profile(job,company,age,name,surname,country,website,__set):
    """
.. _ztc-cmd-user-profile:

Get/Set Profile Info
--------------------

By issuing the command: ::

    ztc profile

the user profile is retrieved and displayed. The user profile consists of the following data:

* Generic Info

    * Username (non mutable)
    * Email (non mutable)
    * Name
    * Surname
    * Age
    * Country
    * Job
    * Company
    * Website

# * Subscription Info

#     * Subscription type
#     * Date of subscription expiration
#     * List of roles
#     * List of active repositories

* Asset and Purchase History list 

    * List of account linked assets
    * List of bought virtual machines

The profile  command can be used to change mutable generic info with the following syntax: ::

    ztc profile --set options

where :samp:`options` is a list of one or more of the following options: 

* :option:`--name name` update the Name field
* :option:`--surname name` update the Surname field
* :option:`--age age` update the Age field
* :option:`--country country` update the Country field
* :option:`--job job` update the Job field
* :option:`--company company` update the Company field
* :option:`--website website` update the Website field

    """
    if __set:
        try:
            res = zput(url=env.api.profile,data = {
                "job":job,
                "company":company,
                "age":age,
                "name":name,
                "surname":surname,
                "country":country,
                "website":website
            })
            if res.status_code!=200:
                error("Can't set profile",res.status_code)
            else:
                info("Profile set")
        except Exception as e:
            critical("Can't set profile",e)
    else:
        try:
            table=[]
            res = zget(url=env.api.profile)
            rj = res.json()
            if rj["status"]=="success":
                if env.human:
                    table.append([
                        rj["data"]["display_name"],
                        rj["data"]["email"],
                        rj["data"]["name"],
                        rj["data"]["surname"],
                        rj["data"]["age"],
                        rj["data"]["country"],
                        rj["data"]["company"],
                        rj["data"]["job"],
                        rj["data"]["website"]
                    ])
                    log()
                    info("General Info\n")
                    log_table(table,headers=["Username","Email","Name","Surname","Age","Country","Company","Job","Website"])
                    
                    table = []
                    table.append([
                        rj["data"]["roles"],
                        rj["data"]["repositories"]
                    ])
                    
                    log()
                    info("Account info\n")
                    log_table(table,headers=["Roles","Repositories"])

                    table = []
                    vmassets = rj["data"]["assets"]["list"]
                    for asset in vmassets:
                        table.append([asset["rtos"],asset["value"],asset["total"],"Premium" if asset["pro"] else "Starter",asset["target"],asset["description"]])
                    log()
                    info("Assets\n")
                    log_table(table,headers=["Rtos","Available","Total","Type","Target","Description"])

                    table = []
                    history = rj["data"].get("history",[])
                    for purchase in history:
                        table.append([purchase["item"],purchase["date"],"%0.2f $" % purchase["price"],purchase["order"]])
                    log()
                    info("Purchase History\n")
                    log_table(table,headers=["Item","Date","Price","Order"])

                else:
                    log_json(rj["data"])
            elif rj["code"]==403:
                log("\"Unauthorized\"")
            else:
                critical("Can't get profile",rj["message"])
        except Exception as e:
            critical("Can't get profile",e)


@cli.command("register",help="Obtain an authentication token")
@click.argument("email")
@click.argument("passwd")
@click.argument("name")
def __register(email,passwd,name):
    try:
        res = zpost(env.api.user,{"username":email,"password":passwd, "display_name":name},auth=False)
        if res.status_code==200:
            rj = res.json()
            if rj["status"]=="success":
                info("Ok")
                info(rj["data"])
                env.set_token(rj["data"]["token"])
            else:
                fatal(rj["message"])
        else:
            fatal(res.status_code,"while registering user")
    except Exception as e:
        fatal("Exception while registering user",e)



################# REDEEM Licenses
@cli.command("redeem",help="Redeem assets with codes")
@click.argument("code")
def redeem(code):
    try:
        res = zpost(env.api.user+"/redeem/",{"code":code})
        rj = res.json()
        if rj["status"]=="success":
            asset = rj["data"]
            if env.human:
                info("Code successfully redeemed! You now have",asset["value"],"premium" if asset["pro"] else "starter","virtual machine(s) for the following targets:",asset["target"])
            else:
                log_json(asset)
        else:
            fatal("Can't redeem code!",rj["message"])
    except Exception as e:
        critical("Can't redeem code",exc=e)





