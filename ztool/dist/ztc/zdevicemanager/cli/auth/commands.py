
import base64
import time
import webbrowser

import click
from zdevicemanager.base.base import cli
from zdevicemanager.base.base import info, log, fatal, warning
from zdevicemanager.base.cfg import env
from zdevicemanager.base.fs import fs
from zdevicemanager.base.zrequests import zget, zpost


@cli.command("login", help="Obtain an authentication token")
@click.option("--token", default=None, help="set the token in non interactive mode")
@click.option("--user", default=None, help="username for manual login")
@click.option("--passwd", default=None, help="password for manual login")
@click.option("--origin", default=None, help="origin for 3dparty auth")
@click.option("--origin_username", default=None, help="origin username for 3dparty auth")
def login(token, user, passwd, origin, origin_username):
    """
.. _zdm-cmd-auth-login:

Login
-----

The :command:`login` command enables the user to retrieve an authentication token. The token is used in most zdm commands to communicate with the Zerynth backend.

The :command:`login` can be issued in interactive and non interactive mode. Interactive mode is started by typing: ::

    zdm login

The zdm opens the default system browser to the login/registration page and waits for user input.

In the login/registration page, the user can login providing a valid email and the corresponding password.
It is also possible (and faster) to login using Google plus or Facebook OAuth services. If the user do not have a Zerynth account it is possible to register
providing a valid email, a nick name and a password. Social login is also available for registration via OAuth.

Once a correct login/registration is performed, the browser will display an authentication token. Such token can be copied and pasted to the zdm prompt.

.. warning:: multiple logins with different methods (manual or social) are allowed provided that the email linked to the social OAuth service is the same as the one used in the manual login.

.. warning:: For manual registrations, email address confirmation is needed. An email will be sent at the provided address with instructions.

    """
    if not token and not user and not passwd:
        log("Hello!")
        log("")
        log("Please note that this is a beta version of the Zerynth Device Manager (ZDM) platform which is still undergoing final testing before its official release.")
        log("The platform, its software and all content found on it are provided on an 'as is' and 'as available' basis.")
        log("Zerynth (TOI.srl) does not give any warranties, whether express or implied, as to the suitability or usability of the website and the CLI, its software or any of its content.")
        log("Zerynth will not be liable for any loss, whether such loss is direct, indirect, special or consequential, suffered by any party as a result of their use of the ZDM platform, its software or content.")
        log("")
        log("Any creation, download or upload of data, devices, firmware to the platform is done at the user’s own risk and the user will be solely responsible for any damage to any system or loss of data that results from such activities.")
        log("Should you encounter any bugs, glitches, lack of functionality or other problems on the website, please let us know immediately so we can rectify these accordingly.")
        log("Your help in this regard is greatly appreciated! You can post on our forum (Your help in this regard is greatly appreciated! You can post on our forum (Your help in this regard is greatly appreciated! You can post on our forum (https://community.zerynth.com/c/zerynth-device-manager-beta/) or visit https://www.zerynth.com/contact/")
        log("")
        log("By using this software you accept al the conditions above described.")

        check = env.get_zdm_conditions()
        if not check.acceptance:
            log("")
            accept = input("Please accept conditions [Y/N]. ")
            if accept == 'Y' or accept == 'y':
                env.set_zdm_conditions()
            else:
                fatal("accepting conditions is mandatory for the zdm usage")
        
        log("")
        log("In a few seconds a browser will open to the login page")
        log("Once logged, copy the authorization token and paste it here")
        time.sleep(2)
        # log into Zerynth backend and rediect to the ZDM in order to login the user also in the ZDM.
        sso_path = env.api.sso + "?redirect=" + env.zdm + "/v1/login/ztc/"
        webbrowser.open(sso_path)
        token = input("Paste the token here and press enter -->")
    if token:
        env.set_token(token)
        check_installation()
    elif user and passwd:
        try:
            head = {"Authorization": "Basic " + base64.standard_b64encode(bytes(user + ":" + passwd, "utf-8")).decode(
                "utf-8")}
            params = {}
            if origin and origin_username:
                params["origin"] = origin
                params["origin_username"] = origin_username
            res = zget(env.api.user, head, params, auth=False)
            if res.status_code == 200:
                rj = res.json()
                if rj["status"] == "success":
                    env.set_token(rj["data"]["token"])
                    # putted here for testing login with unit tests
                    zget(env.api.sso + "?redirect=" + env.zdm + "/v1/login/ztc/")
                    info("Ok")
                else:
                    fatal(rj["message"])
            else:
                fatal(res.status_code, "while logging user")
        except Exception as e:
            fatal("Error!", e)
    else:
        fatal("Token needed!")


def check_installation():
    try:
        instfile = fs.path(env.cfg, "installation.json")
        inst = fs.get_json(instfile)
        if not inst.get("uid") and inst.get("offline", None) is not None:
            # save installation info
            try:
                res = zpost(env.api.installation, {"installer": "offline" if inst["offline"] else "online"})
                if res.status_code == 200:
                    rj = res.json()
                    if rj["status"] == "success":
                        inst["uid"] = rj["data"]["inst_uid"]
                        fs.set_json(inst, instfile)
                    else:
                        warning(rj["code"], "after checking installation")
                else:
                    warning(res.status_code, "while checking installation")
            except:
                warning("Exception while sending installation data")
    except Exception as e:
        warning("Exception while checking installation", str(e))


@cli.command("logout", help="Delete the current session")
def logout():
    """
.. _zdm-cmd-auth-logout:

Logout
------

Delete current session with the following command ::

    zdm logout


.. note:: it will be necessary to login again.

    """
    env.rm_token()
