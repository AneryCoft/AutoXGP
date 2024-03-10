import re
import os
import sys
import time
import uuid
import json
import base64
import random
import ctypes
import string
import urllib3
import hashlib
import logging
import datetime
import requests
import threading
import configparser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from selenium.common.exceptions import WebDriverException

def print_logo():
    "打印logo"
    print("""     _         _      __  ______ ____                                 _       
    / \  _   _| |_ ___\ \/ / ___|  _ \ _ __ ___  __ _ _   _  ___  ___| |_ ___ 
   / _ \| | | | __/ _ \\\\  / |  _| |_) | '__/ _ \/ _` | | | |/ _ \/ __| __/ __|
  / ___ \ |_| | || (_) /  \ |_| |  __/| | |  __/ (_| | |_| |  __/\__ \ |_\__ \\
 /_/   \_\__,_|\__\___/_/\_\____|_|   |_|  \___|\__, |\__,_|\___||___/\__|___/
                                                   |_|
""")


def del_empty_logs():
    "删除空日志文件"
    try:
        for filename in os.listdir("log"):
            filepath = os.path.join(f"log/{filename}")
            if os.path.isfile(filepath) and os.path.getsize(filepath) == 0:
                os.remove(filepath)
    except:
        pass


def init():
    "初始化"
    ctypes.windll.kernel32.SetConsoleTitleW("Auto Xbox Game Pass") # 设置控制台标题
    if not os.path.exists("log"):
        os.mkdir("log")
    if not os.path.exists("Accounts"):
        os.mkdir("Accounts")
    if not os.path.exists("Accounts/Accounts.txt"):
        with open("Accounts/Accounts.txt", "w") as f:
            pass
    if not os.path.exists("Accounts/XGP.txt"):
        with open("Accounts/XGP.txt", "w") as f:
            pass
    if not os.path.exists("Cookies"):
        os.mkdir("Cookies")
    if not os.path.exists("Cookies/AilpayCookies.json"):
        with open("Cookies/AilpayCookies.json", "w") as f:
            pass
    
    if (not os.path.exists("cfg.ini")) or os.path.getsize("cfg.ini") == 0:
        cfg = configparser.ConfigParser()
        cfg['Log'] = {'log_level': 'INFO',
                      'stream_level': 'INFO'}
        cfg['Thread'] = {'thread': '1'}
        cfg['Proxy'] = {'enable_proxy': 'false',
                        'proxy_host': ''}
        cfg['Alipay'] = {'pay_pwd': '',
                            'save_cookies': 'false'}
        cfg['Prefix'] = {'xbox_prefix': '',
                            'ign_prefix': ''}
        cfg['Skin'] = {'set_skin': 'false',
                        'model': '0'}
        with open('cfg.ini', 'w') as cfg_file:
            cfg.write(cfg_file)
        with open('cfg.ini', 'rb+') as cfg_file:
            content = cfg_file.read()
            cfg_file.seek(0)
            cfg_file.truncate()
            cfg_file.write(content[:-4])
            cfg_file.write(" ; 0-经典 1-纤细".encode('utf-8'))
    del_empty_logs()


def init_logger(timestamp:str) -> logging.Logger:
    "初始化日志记录器"
    class MyFilter(logging.Filter):
        def filter(self, record):
            return record.name in ('__main__')
    cfg = configparser.ConfigParser()
    cfg.read('cfg.ini', encoding='utf-8')
    log_format = '[%(levelname)s] [%(asctime)s] [%(threadName)s] %(message)s'
    logging.basicConfig(
        filename=f'log/log_{timestamp}.log',
        level=logging.INFO,
        format=log_format,
        datefmt='%Y-%m-%d %H:%M:%S',
        encoding='utf-8'
    )
    logger = logging.getLogger(__name__)
    try:
        logger.setLevel(logging.getLevelName(cfg.get('Log', 'log_level').upper()))
    except:
        logger.setLevel(logging.INFO)
    logger.addFilter(MyFilter())

    console_handler = logging.StreamHandler()
    try:
        console_handler.setLevel(logging.getLevelName(cfg.get('Log', 'stream_level').upper()))
    except:
        console_handler.setLevel(logging.INFO)
    stream_format = '[%(asctime)s] [%(threadName)s] %(message)s'
    console_handler.setFormatter(logging.Formatter(stream_format, datefmt='%H:%M:%S'))
    logger.addHandler(console_handler)
    return logger


def get_random_str(length: int) -> str:
    "生成随机字符串"
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))


def edge(headless:bool = True) -> webdriver.Edge:
    "创建Edge浏览器实例"
    options = Options()
    if headless:
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
    options.add_argument("--inprivate")
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    return webdriver.Edge(options=options)


def fix_base64_str(str:str) -> str:
    """
    修复Base64编码字符串长度错误问题
    避免 binascii.Error: Incorrect padding
    """
    length = len(str)
    if length % 4:
        str += "=" * (4 - length % 4)
    return str


def get_proxies():
    "获取代理并检查代理可用性"
    cfg = configparser.ConfigParser()
    cfg.read("cfg.ini")
    try:
        if cfg.getboolean("Proxy","enableProxy"):
            host = cfg["Proxy"]["proxy_host"]
            proxies = {
                "http": "http://" + host,
                "https": "https://" + host
            }
            # 检查代理可用性
            response = requests.get("http://httpbin.org/ip")
            if response.status_code == 200:
                return proxies
    except:
        pass


def get_pay_pwd() -> str:
    "获取支付密码"
    try:
        pay_pwd = str(cfg.get("Alipay", "pay_pwd").strip())
    except:
        pay_pwd = ""
    while True:
        if len(pay_pwd) != 6 or (pay_pwd == "" or not pay_pwd.isdigit()):
            pay_pwd = input("输入你的支付宝支付密码:")
            if len(str(pay_pwd)) != 6:
                print("键入有误! 支付密码必须是6位数字,请重新输入...")
                time.sleep(2)
                os.system("cls")
                continue
            else:
                cfg.set("Alipay", "pay_pwd", pay_pwd)
                cfg_file = open("cfg.ini", "w")
                with open("cfg.ini", "w") as cfg_file:
                    cfg.write(cfg_file)
                logger.info("已在配置中保存支付密码")
                break
        else:
            break
    return pay_pwd


def check_cookies_availability() -> bool:
    "检查Alipay是否能通过Cookie正常登录"
    try:
        with open("Cookies/AilpayCookies.json", 'r') as file:
            alipay_cookies = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return False
    # 将JSON格式的Cookie列表转换为请求头部格式
    cookie_header = '; '.join([f'{cookie["name"]}={cookie["value"]}' for cookie in alipay_cookies])
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Cookie": cookie_header
    }

    response = requests.get("https://www.alipay.com/", headers=headers)

    if response.status_code == 200:
        element = response.text.find("我已有支付宝账户")
        if element != -1:
            logger.warning("登录支付宝失败,请更新Cookie")
            return False
        else:
            new_cookies = requests.utils.dict_from_cookiejar(response.cookies)
            cfg = configparser.ConfigParser()
            cfg.read("cfg.ini", encoding="utf-8")
            try:
                if cfg["Alipay"].getboolean("save_cookies"):
                    with open("Cookies\AilpayCookies.json", 'w') as file:
                        json.dump(new_cookies, file)
            except:
                pass
            return True
    else:
        logger.error(f"LoginAlipayFailed: {response.status_code} Request failed")
        return False


def get_alipay_cookies():
    "获取支付宝Cookies"
    if not (os.path.exists("Cookies/AilpayCookies.json") and os.path.getsize("Cookies/AilpayCookies.json") == 0 and check_cookies_availability()):
        driver = edge(False)
        driver.implicitly_wait(10.0)
        driver.get("https://auth.alipay.com/login/index.htm?goto=https%3A%2F%2Fwww.alipay.com%2F")
        logger.info("扫码以登录支付宝")
        # 判断是否已扫码
        while True:
            try:
                if driver.current_url.startswith("https://www.alipay.com/"):
                    break
                else:
                    time.sleep(0.5)
            except WebDriverException as e:
                #logger.critical(e)
                logger.critical("浏览器可能被异常关闭,将结束程序...")
                sys.exit()
        alipay_cookies = driver.get_cookies()
        logger.info("已获取支付宝Cookies")
        try:
            if cfg.getboolean("Alipay", "save_cookies"):
                with open("Cookies/AlipayCookies.json", "w+") as cookie_file:
                    cookie_file.write(json.dumps(alipay_cookies))
                logger.info("已保存支付宝Cookies")
        except:
            pass
        return alipay_cookies
    else:
        with open("Cookies/AlipayCookies.json", "r") as cookie_file:
             alipay_cookies = json.loads(cookie_file.read())
        return alipay_cookies


def getXGP(account:str):
    # 用于计算用时
    start_time = time.time()

    parts = account.split("----")
    ms_email = parts[0]
    ms_password = parts[1]

    session = requests.session()
    """
    for cookie in alipay_cookies:
        session.cookies.set(cookie["name"], cookie["value"], domain=cookie["domain"])
    """
    session.proxies = proxies
    
    # OAuth2.0
    url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize"
    client_id = "1f907974-e22b-4810-a9de-d9647380c97e"
    client_request_id = str(uuid.uuid1())
    code_verifier = get_random_str(43).encode()
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier).digest()).rstrip(b"=").decode()
    state_data = ('{"id":"%s","meta":{"interactionType":"redirect"}}' % uuid.uuid1()).encode()
    state = base64.b64encode(state_data).decode() + "|https%3A%2F%2Fwww.xbox.com%2Fzh-HK%2Fxbox-game-pass%2Fpc-game-pass"
    params = {
        "client_id": client_id,
        "scope": "xboxlive.signin openid profile offline_access",
        "redirect_uri": "https://www.xbox.com/auth/msa?action=loggedIn&locale_hint=zh-HK",
        "client-request-id": client_request_id,
        "response_mode": "fragment",
        "response_type": "code",
        "x-client-SKU": "msal.js.browser",
        "x-client-VER": "3.7.0",
        "client_info": "1",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "prompt": "select_account",
        "nonce": str(uuid.uuid1()),
        "state": state
    }
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "sec-fetch-site": "none",
        "sec-fetch-mode": "navigate",
        "sec-fetch-user": "?1",
        "sec-fetch-dest": "document",
        "sec-ch-ua": '"Not A(Brand";v="99", "Microsoft Edge";v="121", "Chromium";v="121"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "accept-encoding": "gzip",
        "accept-language": "zh-CN,zh;q=0.9",
    }
    oauth2 = session.get(url=url,params=params, headers=headers, verify=False)

    # 登录微软

    # 发送账户
    url = "https://login.live.com/GetCredentialType.srf?"
    uaid = oauth2.cookies["uaid"]
    flow_token = re.search(r'value="(.+?)"',oauth2.text).group(1)
    body = {
        "username": ms_email,
        "uaid": uaid,
        "isOtherIdpSupported": False,
        "checkPhones": False,
        "isRemoteNGCSupported": True,
        "isCookieBannerShown": False,
        "isFidoSupported": True,
        "forceotclogin": False,
        "otclogindisallowed": False,
        "isExternalFederationDisallowed": False,
        "isRemoteConnectSupported": False,
        "federationFlags": 3,
        "isSignup": False,
        "flowToken": flow_token
    }
    post_email = session.post(url=url, headers=headers, json=body, allow_redirects=False, verify=False)

    if post_email.json()["IfExistsResult"] == 1:
        logger.error(f"微软账户错误:{ms_email}")
        return

    # 发送密码
    url = f"https://login.live.com/ppsecure/post.srf?uaid={uaid}"
    body = {
        "i13": "0",
        "login": ms_email,
        "loginfmt": ms_email,
        "type": "11",
        "LoginOptions": "3",
        "lrt": "",
        "lrtPartition": "",
        "hisRegion": "",
        "hisScaleUnit": "",
        "passwd": ms_password,
        "ps": "2",
        "psRNGCDefaultType": "",
        "psRNGCEntropy": "",
        "psRNGCSLK": "",
        "canary": "",
        "ctx": "",
        "hpgrequestid": "",
        "PPFT": flow_token,
        "PPSX": "P",
        "NewUser": "1",
        "FoundMSAs": "",
        "fspost": "0",
        "i21": "0",
        "CookieDisclosure": "0",
        "IsFidoSupported": "1",
        "isSignupPost": "0",
        "isRecoveryAttemptPost": "0",
        "i19": "060601"
    }
    post_password = session.post(url=url, headers=headers, data=body, allow_redirects=False, verify=False)

    # 取消保持登录状态
    opid = re.search(r"opid=(.+?)&", oauth2.text).group(1)
    url = f"https://login.live.com/ppsecure/post.srf?nopa=2&uaid={uaid}&opid={opid}&route=C107_SN1"
    body = {
        "LoginOptions": "3",
        "type": "28",
        "ctx": "",
        "hpgrequestid": "",
        "PPFT": flow_token,
        "canary": ""
    }
    keep_login = session.post(url=url, data=body, headers=headers, allow_redirects=False, verify=False)
    login_action = keep_login

    # 跳过保护账户
    url_match = re.search(r'action="(.+?)"', keep_login.text)
    if url_match:
        url = url_match.group(1)
        if url.split("?")[0] == "https://account.live.com/proofs/Add":
            pprid = re.search(r'id="pprid" value="(.+?)"',keep_login.text).group(1)
            body = {
                "ipt": re.search(r'id="ipt" value="(.+?)"',keep_login.text).group(1),
                "pprid": pprid,
                "uaid": uaid
            }
            add_proofs = session.post(url=url, headers=headers, data=body, allow_redirects=False, verify=False)

            canary = re.search(r'name="canary" value="(.+?)"',add_proofs.text).group(1)
            body = {
                "iProofOptions": "Email",
                "DisplayPhoneCountryISO": "CN",
                "DisplayPhoneNumber": "",
                "EmailAddress": "",
                "canary": canary,
                "action": "Skip",
                "PhoneNumber": "",
                "PhoneCountryISO": ""
            }
            skip = session.post(url=url, data=body, headers=headers, allow_redirects=False, verify=False)

            # 跳过摆脱密码束缚
            url = skip.headers["Location"]
            authenticator_cancel = session.post(url=url, headers=headers, allow_redirects=False, verify=False)
            login_action = authenticator_cancel

    # 登录Xbox

    url = "https://www.xbox.com/zh-HK/auth/msa?action=loggedIn&locale_hint=zh-HK"
    login_in = session.get(url=url, headers=headers, allow_redirects=False, verify=False)

    url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
    headers["origin"] = "https://www.xbox.com"
    code = re.search(r'code=(.+?)&',login_action.headers["Location"]).group(1)
    body = {
    "client_id": client_id,
    "redirect_uri": "https://www.xbox.com/auth/msa?action=loggedIn&locale_hint=zh-HK",
    "scope": "xboxlive.signin openid profile offline_access",
    "code": code,
    "x-client-SKU": "msal.js.browser",
    "x-client-VER": "3.7.0",
    "x-ms-lib-capability": "retry-after, h429",
    "x-client-current-telemetry": "",
    "x-client-last-telemetry": "",
    "code_verifier": code_verifier,
    "grant_type": "authorization_code",
    "client_info": "1",
    "client-request-id": client_request_id,
    "X-AnchorMailbox": ""
    }
    oauth2_token = session.post(url=url, data=body, headers=headers, allow_redirects=False, verify=False)

    # 登录Xbox
    url = "https://sisu.xboxlive.com/connect/XboxLive"
    # token_decode = jwt.decode(oauth2_token.json["id_token"],algorithms=["RS256"],verify=False)
    tokrn_data = fix_base64_str(str(oauth2_token.json()["id_token"]).split(".")[1])
    tokrn_data_decode = json.loads(base64.b64decode(tokrn_data))
    login_hint = tokrn_data_decode["login_hint"]
    msa_id = tokrn_data_decode["oid"] + "." + tokrn_data_decode["tid"]
    params = {
        "ru": "https://www.xbox.com/auth/msa?action=loggedIn",
        "login_hint": login_hint,
        "userPrompts": "XboxOptionalDataCollection",
        "consent": "required",
        "cv": "",
        "state": '{"ru":"https://www.xbox.com/zh-HK/xbox-game-pass/pc-game-pass","msaId":%s,"sid":"RETAIL"}' % msa_id
    }
    login_in = session.get(url=url,params=params, headers=headers, verify=False)

    # 创建Xbox档案

    session_id_match = re.search(r'sid=(.+?)&',login_in.history[2].headers["Location"])
    if session_id_match:
        session_id = session_id_match.group(1)
        url = f"https://sisu.xboxlive.com/proxy?sessionid={session_id}"
        headers["authorization"] = re.search(r'spt=(.+?)&',login_in.history[2].headers["Location"]).group(1)
        xbox_prefix = cfg.get("Prefix", "xbox_prefix")
        reservation_id = 1234567890
        body = {
            "GamertagReserve": {
                "Gamertag": "",
                "ReservationId": reservation_id,
                "Duration": "1:00:00"
            }
        }
        # 测试代号是否可用
        while True:
            xbox_gamertag = xbox_prefix + get_random_str(15 - len(xbox_prefix))
            body["GamertagReserve"]["Gamertag"] = xbox_gamertag
            gamertag_test = session.post(url=url, json=body, headers=headers, allow_redirects=False, verify=False)
            if gamertag_test.ok:
                break

        # 设置代号
        body = {
            "CreateAccountWithGamertag": {
                "Gamertag": xbox_gamertag,
                "ReservationId": reservation_id
            }
        }
        set_gamertag = session.post(url=url, json=body, headers=headers, allow_redirects=False, verify=False)
        # current_gametag = set_gamertag.json["gamerTag"]
        logger.info(f"已设置Xbox玩家代号为:{xbox_gamertag}")

        # 设置头像
        body = {
            "SetGamerpic": {
                "GamerPic": "https://dlassets-ssl.xboxlive.com/public/content/ppl/gamerpics/00052-00000-md.png?w=320&h=320"
            }
        }
        set_gamerpic = session.post(url=url, json=body, headers=headers, allow_redirects=False, verify=False)

        # 可选诊断数据
        """
        url = "https://sisu.xboxlive.com/client/v32/default/view/consent.html?action=signup&flowType=new_user"
        consent = session.get(url=url, json=body, headers=headers, allow_redirects=False, verify=False)

        body = {
            "CheckConsents": {}
        }
        check_consents = session.post(url=url, json=body, headers=headers, allow_redirects=False, verify=False)

        body = {
            "SetConsents": {
                "Consents": [
                    {
                        "id": check_consents.json()["consents"][0]["id"],
                        "values": [
                            {
                                "categoryName": "XboxDiagnosticsOptionalData",
                                "value": "false",
                                "valueDataType": "Boolean"
                            }
                        ]
                    }
                ]
            }
        }
        set_consents = session.post(url=url, json=body, headers=headers, allow_redirects=False, verify=False)
        """

    # Xbox验证

    url = "https://user.auth.xboxlive.com/user/authenticate"
    rps_ticket = "d=" + oauth2_token.json()["access_token"]
    body = {
        "Properties": {
            "AuthMethod": "RPS",
            "RpsTicket": rps_ticket,
            "SiteName": "user.auth.xboxlive.com",
        },
        "RelyingParty": "http://auth.xboxlive.com",
        "TokenType": "JWT"
    }
    xbox_auth_1 = session.post(url=url, json=body, headers=headers, allow_redirects=False, verify=False)

    url = "https://xsts.auth.xboxlive.com/xsts/authorize"
    user_token = xbox_auth_1.json()["Token"]
    body = {
        "Properties": {
            "SandboxId": "RETAIL",
            "UserTokens": [user_token]
        },
        "RelyingParty": "http://mp.microsoft.com/",
        "TokenType": "JWT"
    }
    xbox_auth_2 = session.post(url=url, json=body, headers=headers, allow_redirects=False, verify=False)

    # 订阅XGP

    url = f"https://www.microsoft.com/store/buynow?noCanonical=true&market=HK&locale=zh-HK&clientName=XboxCom"
    uhs = xbox_auth_2.json()["DisplayClaims"]["xui"][0]["uhs"]
    microsoft_token = xbox_auth_2.json()["Token"]
    XToken = f"XBL3.0 x={uhs};{microsoft_token}"
    body = {
        "data": '{"products":[{"productId":"CFQ7TTC0KGQ8","skuId":"0002","availabilityId":"CFQ7TTC0KF41"}],"campaignId":"xboxcomct","callerApplicationId":"XboxCom","expId":["EX:sc_xboxgamepad","EX:sc_xboxspinner","EX:sc_xboxclosebutton","EX:sc_xboxuiexp","EX:sc_disabledefaultstyles","EX:sc_gamertaggifting"],"flights":["sc_xboxgamepad","sc_xboxspinner","sc_xboxclosebutton","sc_xboxuiexp","sc_disabledefaultstyles","sc_gamertaggifting"],"clientType":"XboxCom","data":{"usePurchaseSdk":true},"layout":"Modal","cssOverride":"XboxCom2NewUI","theme":"light","scenario":"","suppressGiftThankYouPage":false}',
        "auth": '{"XToken":"%s"}' % XToken
    }
    buy_xgp = session.post(url=url, data=body, headers=headers, allow_redirects=False, verify=False)

    # 选择支付方式
    cart_id = re.search(r'"cartId":"(.*?)"', buy_xgp.text).group(1)
    if cart_id == "":
        logger.error("出现异常 请使用网络代理")
        return

    params = {
        "type": "alipay_billing_agreement",
        "partner": "webblends",
        "orderId": cart_id,
        "operation": "Add",
        "country": "HK",
        "language": "zh-HK",
        "family": "ewallet",
        "completePrerequisites": "true"
    }
    url = "https://paymentinstruments.mp.microsoft.com/v6.0/users/me/paymentMethodDescriptions"
    headers["origin"] = "https://www.microsoft.com"
    headers["referer"] = "https://www.microsoft.com/"
    headers["authorization"] = XToken
    payment_method_descriptions = session.get(url=url, params=params, headers=headers, allow_redirects=False, verify=False)

    # 确认支付
    url = "https://paymentinstruments.mp.microsoft.com/v6.0/users/me/paymentInstrumentsEx?country=hk&language=zh-CHT&partner=webblends&completePrerequisites=True"
    risk_id = re.search(r'"riskId":"(.+?)"', buy_xgp.text).group(1)
    session_id = str(uuid.uuid1())
    body = {
        "paymentMethodCountry": "hk",
        "paymentMethodFamily": "ewallet",
        "paymentMethodOperation": "add",
        "paymentMethodResource_id": "ewallet.alipayQrCode",
        "paymentMethodType": "alipay_billing_agreement",
        "riskData": {
            "dataCountry": "hk",
            "dataOperation": "add",
            "dataType": "payment_method_riskData",
            "greenId": risk_id,
        },
        "sessionId": session_id
    }
    payment_instruments_ex = session.post(url=url, json=body, headers=headers, allow_redirects=False, verify=False)

    # 发送支付宝支付密码签约

    """
    redirectUrl = str(payment_instruments_ex.json()["details"]["redirectUrl"])
    appSignUrl = str(payment_instruments_ex.json()["details"]["appSignUrl"]) # 此链接用于跳转到应用
    url = (
        parse.unquote(re.search(r"&url=(.+)", appSignUrl).group(1))
        + "&return_url="
        + parse.quote(redirectUrl)
    )
    # Worong sign
    """

    url = payment_instruments_ex.json()["clientAction"]["context"][0]["displayDescription"][0]["members"][3]["members"][0]["pidlAction"]["context"]["baseUrl"]
    payment_instrument_id = payment_instruments_ex.json()["id"]
    params = {
        "ru": f"https://www.microsoft.com/zh-HK/store/rds/v2/GeneralAddPISuccess?picvRequired=False&pendingOn=Notification&type=alipay_billing_agreement&family=ewallet&id={payment_instrument_id}",
        "rx": "https://www.microsoft.com/zh-HK/store/rds/v2/GeneralAddPIFailure"
    }
    payment_instruments_ex = session.get(url=url, params=params, headers=headers, allow_redirects=False, verify=False)

    url = payment_instruments_ex.headers["location"]
    lock.acquire()
    driver.get(url)
    input_pay_password = driver.find_element(By.ID, "payPassword_rsainput").send_keys(pay_pwd)
    agree = driver.find_element(By.ID, "J_submit").click()
    # 代扣开通成功
    driver.find_element(By.XPATH, '//*[@id="container"]/div/div[1]/p[1]')
    lock.release()

    # TODO Alipay pay password encrypt
    """ 
    direct_alipay = session.get(
        url=url, headers=headers, allow_redirects=False, verify=False
    )

    url = direct_alipay.headers["Location"]
    alipay_html = session.get(url=url, headers=headers, allow_redirects=False, verify=False)

    url = "https://securitycore.alipay.com/securityAjaxValidate.json"
    alieditUid = re.search(r'name="alieditUid" value="(.+?)"',alipay_html.text).group(1)
    securityId = re.search(r'name="securityId" value="(.+?)"',alipay_html.text).group(1)
    payPassword = ""
    key_seq = ""
    params = {
        "sendCount": "3",
        "dataId": int(time.time() * 1000),
        "dataSize": "1",
        "dataIndex": "0",
        "dataContent": {
            "payment_password": {
                "J_aliedit_key_hidn": "payPassword",
                "J_aliedit_uid_hidn": "alieditUid",
                "J_aliedit_using": "true",
                "payPassword": payPassword,
                "alieditUid": alieditUid,
                "ks": key_seq,
                "security_activeX_enabled": "false",
            }
        },
        "_callback": "light.packetRequest._packetCallbacks.callback0",
        "securityId": securityId,
        "orderId": "null"
    }
    post_pay_password = session.get(url=url, params=params, headers=headers, allow_redirects=False, verify=False)

    url = "https://mdeduct.alipay.com/customer/customerAgreementSignConfirm.htm"
    headers["origin"] = "https://mdeduct.alipay.com"
    headers["referer"] = direct_alipay.headers["Location"]
    _form_token = re.search(r'name="_form_token" value=""(.+?)"',alipay_html.text).group(1)
    cacheContextId = re.search(r'name="cacheContextId" value=""(.+?)"',alipay_html.text).group(1)
    e_i_i_d = re.search(r'name="e_i_i_d" value=""(.+?)"',alipay_html.text).group(1)
    userLogonId = re.search(r'name="userLogonId" value=""(.+?)"',alipay_html.text).group(1)
    body = {
        "_form_token" : _form_token,
        "signFlag" : "signConfirmFromPC",
        "cacheContextId" : cacheContextId,
        "notNeedMobileCodeCheck" : "false",
        "e_i_i_d":e_i_i_d,
        "i_c_i_d":"",
        "userLogonId" : userLogonId,
        "securityId" : securityId,
        "payPassword_input": "",
        "payPassword_rsainput":"",
        "J_aliedit_using": "true",
        "payPassword": "",
        "J_aliedit_key_hidn": "payPassword",
        "J_aliedit_uid_hidn": "alieditUid",
        "alieditUid": alieditUid,
        "REMOTE_PCID_NAME": "_seaside_gogo_pcid",
        "_seaside_gogo_pcid": "",
        "_seaside_gogo_": "",
        "_seaside_gogo_p": "",
        "J_aliedit_prod_type": "payment_password",
        "security_activeX_enabled": "false",
        "J_aliedit_net_info": ""
    }
    sign_confirm = session.post(url=url, data=body, headers=headers, allow_redirects=False, verify=False)
    """

    """
    url = sign_confirm.headers["Location"]
    agreement_operation_result = session.get(url=url, headers=headers, allow_redirects=False, verify=False)
    """

    # 确认使用支付宝订阅
    url = f"https://paymentinstruments.mp.microsoft.com/v6.0/users/me/paymentInstrumentsEx/{payment_instrument_id}?language=zh-CHT&partner=webblends&country=hk&completePrerequisites=True"
    add_alipay = session.get(url=url, headers=headers, allow_redirects=False, verify=False)

    # 添加地址信息
    # url = "https://jcmsfd.account.microsoft.com/JarvisCM/me/addresses"
    url = "https://paymentinstruments.mp.microsoft.com/v6.0/users/me/addresses"
    body = {
        "addressCountry": "hk",
        "addressType": "billing",
        "address_line1": "b",
        "address_line2": "",
        "city": "a",
        "country": "hk"
    }
    addresses = session.post(url=url, json=body, headers=headers, allow_redirects=False, verify=False)

    # 订阅
    url = "https://cart.production.store-web.dynamics.com/v1.0/Cart/PrepareCheckout?appId=BuyNow&perf=true&context=UpdateBillingInformation"
    ms_cv = get_random_str(22)
    headers["ms-cv"] = ms_cv + ".5"
    headers["x-authorization-muid"] = re.search(r'"alternativeMuid":"(.+?)"',buy_xgp.text).group(1)
    headers["x-ms-correlation-id"] = re.search(r'"correlationId":"(.+?)"',buy_xgp.text).group(1)
    headers["x-ms-vector-id"] = re.search(r'"vectorId":"(.+?)"',buy_xgp.text).group(1)
    risk_id = re.search(r'"riskId":"(.+?)"',buy_xgp.text).group(1)
    body = {
        "buyNowScenario": "",
        "callerApplicationId": "_CONVERGED_XboxCom",
        "cartId": cart_id,
        "catalogClientType": "",
        "clientContext": {
            "client": "XboxCom",
            "deviceFamily": "Web"
        },
        "flights": [],
        "friendlyName": None,
        "isBuyNow": True,
        "isGift": False,
        "locale": "zh-HK",
        "market": "HK",
        "primaryPaymentInstrumentId": payment_instrument_id,
        "refreshPrimaryPaymentOption": False,
        "riskSessionId": risk_id,
        "testScenarios": "None"
    }
    prepare_checkout = session.post(url=url, json=body, headers=headers, allow_redirects=False, verify=False)

    url = "https://paymentinstruments.mp.microsoft.com/v6.0/users/me/PaymentSessionDescriptions"
    piid = payment_instrument_id
    piCid = add_alipay.json()["accountId"]
    purchaseOrderId = cart_id
    params = {
        "paymentSessionData" : '{"piid":"%s","language":"zh-HK","partner":"webblends","piCid":"%s","amount":29,"currency":"HKD","country":"HK","hasPreOrder":"false","challengeScenario":"RecurringTransaction","challengeWindowSize":"03","purchaseOrderId":"%s"}' % (piid,piCid,purchaseOrderId),
        "operation": "Add"
    }
    payment_session_descriptions = session.get(url=url, params=params, headers=headers, allow_redirects=False, verify=False)

    url = f"https://cart.production.store-web.dynamics.com/v1.0/Cart/purchase?appId=BuyNow"
    headers["ms-cv"] = ms_cv + ".6"
    match_AddrId = re.search(r'<Id>(.+?)</Id>',addresses.text)
    if match_AddrId:
        addressId = match_AddrId.group(1)
    else:
        addressId = addresses.json()["id"]
    # addressId = re.search(r'"soldToAddressId":"(.+?)"',buy_xgp.text).group(1)
    # flights = re.search(r'"flights":\[(.+?)\]', buy_xgp.text).group(1)
    # flights = flights.replace('"',"").split(",")
    body = {
        "cartId": cart_id,
        "market": "HK",
        "locale": "zh-HK",
        "catalogClientType": "",
        "callerApplicationId": "_CONVERGED_XboxCom",
        "clientContext": {
            "client": "XboxCom",
            "deviceFamily": "Web"
        },
        "paymentSessionId": session_id,
        "riskChallengeData": None,
        "rdsAsyncPaymentStatusCheck": False,
        "paymentInstrumentId": payment_instrument_id,
        "paymentInstrumentType": "alipay_billing_agreement",
        "email": ms_email,
        "csvTopOffPaymentInstrumentId": None,
        "billingAddressId": {
            "accountId": piCid,
            "id": addressId
        },
        "currentOrderState": "CheckingOut",
        "flights": [],
        "itemsToAdd": {}
    }
    buy_now = session.post(url=url, json=body, headers=headers, allow_redirects=False, verify=False)

    logger.info("已订阅Xbox Game Pass")

    # 设置Minecraft档案

    # 登录微软账户
    """
    url = "https://www.minecraft.net/msaprofilejs/6eff6391c7c99228bb68_03012024_0244/11.chunk.c68d8eb533ea60bdfbc5.js"
    get_login_params = session.get(url=url, headers=headers, allow_redirects=False, verify=False)
    """
    # cobrandId = re.search(r'sisuCobrandId:"(.+?)"', get_login_params.text).group(1)
    # tid = re.search(r'titleId:"(.+?)"', get_login_params.text).group(1)
    ru = "https%3A%2F%2Fwww.minecraft.net%2Fzh-hans%2Flogin%3Freturn_url%3Dhttps%253A%252F%252Fwww.minecraft.net%252Fzh-hans%252Fmsaprofile%252Fmygames%252Feditprofile"
    # aid = re.search(r'sisuAppId:"(.+?)"', get_login_params.text).group(1)
    url = f"https://sisu.xboxlive.com/connect/XboxLive/?state=login&ru={ru}"
    headers.pop("authorization")
    headers.pop("ms-cv")
    headers.pop("x-authorization-muid")
    headers.pop("x-ms-correlation-id")
    headers.pop("x-ms-vector-id")
    headers["referer"] = "https://www.minecraft.net/"
    headers["origin"] = "https://www.minecraft.net"
    login_minecraft = session.get(url=url, headers=headers, verify=False)

    url = "https://api.minecraftservices.com/authentication/login_with_xbox"
    access_token_base64 = login_minecraft.history[2].headers["location"].split("#")[1].strip("state=login&accessToken=")
    access_token = json.loads(base64.b64decode(fix_base64_str(access_token_base64)))
    identityToken = "XBL3.0 x=" + access_token[1]["Item2"]["DisplayClaims"]["xui"][0]["uhs"] + ";" + access_token[1]["Item2"]["Token"]
    body = {
        "ensureLegacyEnabled": True,
        "identityToken": identityToken
    }
    login_with_xbox = session.post(url=url, json=body, headers=headers, allow_redirects=False, verify=False)

    request_id = str(uuid.uuid1())
    url = f"https://api.minecraftservices.com/entitlements/license?requestId={request_id}"
    authorization = "Bearer " + login_with_xbox.json()["access_token"]
    headers["authorization"] = authorization
    redeem = session.get(url=url,headers=headers,allow_redirects=False,verify=False)

    minecraft_prefix = cfg.get("Prefix", "minecraft_prefix")

    # 测试ID是否可用
    while True:
        profile_name = minecraft_prefix + get_random_str(16 - len(minecraft_prefix))
        url = f"https://api.minecraftservices.com/minecraft/profile/name/{profile_name}/available"
        name_available = session.get(url=url, headers=headers, allow_redirects=False, verify=False)
        status = name_available.json()["status"]
        if status == "AVAILABLE":
            break
    
    # 设置MinecraftID
    url = "https://api.minecraftservices.com/minecraft/profile"
    body = {"profileName": profile_name}
    set_profile_name = session.post(url=url, json=body, headers=headers, allow_redirects=False, verify=False)
    if set_profile_name.ok:
        logger.info(f"已设置MinecraftID为:{profile_name}")
    elif set_profile_name.json()["details"]["status"] == "NOT_ENTITLED":
        logger.error(f"无法修改MinecraftID!")
    
    # 设置Minecraft皮肤
    if cfg.getboolean("Skin","customSkin"): 
        url = "https://api.minecraftservices.com/minecraft/profile/skins"
        model = cfg.getint("Skin","model")
        model_list = ["classic","slim"]
        body = {"variant": model_list[model]}
        skin_path = cfg["Skin"]["skin"]
        skin_file = open(skin_path,"rb")
        skin = {"file":skin_file}
        customSkin = session.post(url=url,headers=headers,data=body,files=skin,verify=False)
        if customSkin.ok:
            logger.info("已设置Minecraft皮肤")

    # 取消订阅

    url = "https://account.microsoft.com/services/pcgamepass/cancel?fref=billing-cancel"
    headers.pop("authorization")
    billing_cancel = session.get(url=url, headers=headers, verify=False)

    # 登录微软账户
    url = "https://account.microsoft.com/auth/complete-signin?ru=https%3A%2F%2Faccount.microsoft.com%2Fservices%2Fpcgamepass%2Fcancel%3Ffref%3Dbilling-cancel&wa=wsignin1.0"
    body = {
        "pprid": re.search(r'id="pprid" value="(.+?)">', billing_cancel.text).group(1),
        "NAP": re.search(r'id="NAP" value="(.+?)">', billing_cancel.text).group(1),
        "ANON": re.search(r'id="ANON" value="(.+?)">', billing_cancel.text).group(1),
        "t": re.search(r'id="t" value="(.+?)">', billing_cancel.text).group(1)
    }
    login_ms = session.post(url=url, data=body, headers=headers, verify=False)

    url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize"
    client_id = "81feaced-5ddd-41e7-8bef-3e20a2689bb7"
    client_request_id = str(uuid.uuid1())
    code_verifier = get_random_str(43).encode()
    code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier).digest()).rstrip(b"=").decode()
    state_data = ('{"id":"%s","meta":{"interactionType":"silent"}}' % uuid.uuid1()).encode()
    state = base64.b64encode(state_data).decode()
    params = {
        "client_id": client_id,
        "scope": "openid profile offline_access",
        "redirect_uri": "https://account.microsoft.com/auth/complete-client-signin-oauth",
        "client-request-id": client_request_id,
        "response_mode": "fragment",
        "response_type": "code",
        "x-client-SKU": "msal.js.browser",
        "x-client-VER": "2.37.0",
        "client_info": "1",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "prompt": "none",
        "login_hint": ms_email,
        "X-AnchorMailbox": "UPN:" + ms_email,
        "nonce": str(uuid.uuid1()),
        "state": state
    }
    headers["referer"] = "https://account.microsoft.com/"
    oauth2 = session.get(url=url, params=params, headers=headers, verify=False)

    url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
    headers["origin"] = "https://account.microsoft.com"
    headers["referer"] = "https://account.microsoft.com/"
    url_and_params = oauth2.history[1].headers["Location"]
    code = re.search(r"code=(.+?)&", url_and_params).group(1)
    body = {
        "client_id": client_id,
        "redirect_uri": "https://account.microsoft.com/auth/complete-client-signin-oauth",
        "scope": "openid profile offline_access",
        "code": code,
        "x-client-SKU": "msal.js.browser",
        "x-client-VER": "2.37.0",
        "x-ms-lib-capability": "retry-after, h429",
        "x-client-current-telemetry": "",
        "x-client-last-telemetry": "",
        "code_verifier": code_verifier,
        "grant_type": "authorization_code",
        "client_info": "1",
        "client-request-id": client_request_id,
        "X-AnchorMailbox": ""
    }
    oauth2_token = session.post(url=url, data=body, headers=headers, allow_redirects=False, verify=False)

    # 取消订阅
    url = "https://account.microsoft.com/services/pcgamepass/cancel?fref=billing-cancel&refd=account.microsoft.com"
    cancel_service_page = session.get(url=url, headers=headers, allow_redirects=False, verify=False)

    url = "https://account.microsoft.com/services/api/cancelservice"
    verification_token = re.search(r'name="__RequestVerificationToken" type="hidden" value="(.+?)"',cancel_service_page.text).group(1)
    headers["__requestverificationtoken"] = verification_token
    headers["ms-cv"] = session.cookies["AMC-MS-CV"]
    headers["referer"] = "https://account.microsoft.com/services/pcgamepass/cancel?fref=billing-cancel&refd=account.microsoft.com"
    headers["x-edge-shopping-flag"]= "0"
    headers["x-requested-with"]= "XMLHttpRequest"
    headers["x-tzoffset"]= "480"
    match_serviceId = re.search(r'"active":\[{"id":"(.+?)"',cancel_service_page.text)
    if not match_serviceId:
        url = "https://account.microsoft.com/services/api/subscriptions-and-alerts?excludeWindowsStoreInstallOptions=false&excludeLegacySubscriptions=false"
        subscriptions_and_alerts = session.get(url=url, headers=headers, allow_redirects=False, verify=False)
        serviceId = re.search(r'"id":"(.+?)"',subscriptions_and_alerts.text).group(1)
    else:
        serviceId = match_serviceId.group(1)
    body = {
        "serviceId":serviceId,
        "serviceType":"recurrence",
        "refundAmount":29,
        "riskToken":"",
        "isDunning":False,
        "locale":"zh-CN",
        "market":"HK"
    }
    cancel_service = session.put(url=url, json=body, headers=headers, allow_redirects=False, verify=False)

    logger.info("已取消订阅并退款")

    lock.acquire()
    global XGP_file
    XGP_file.write(account + "\n")
    lock.release()

    logger.info("用时：%.2f秒" % (time.time() - start_time))


def assign_account(accounts:list[str]):
    "为每个线程分配账号"
    while True:
        lock.acquire()
        if not accounts:
            lock.release()
            break
        acc = accounts.pop()
        lock.release()
        if acc[0] != "#":
            acc = acc.strip("\n")
            getXGP(acc)


if __name__ == "__main__":
    os.system('cls')
    init()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    cfg = configparser.ConfigParser()
    cfg.read("cfg.ini")
    logger = init_logger(timestamp)
    urllib3.disable_warnings()

    pay_pwd = get_pay_pwd()
    proxies = get_proxies()
    alipay_cookies = get_alipay_cookies()
    driver = edge()

    with open("Accounts/Accounts.txt", "r+") as f:
        accounts = f.readlines()

    try:
        thread_num = cfg.getint("Thread","thread")
    except:
        thread_num = 1
    threads:list[threading.Thread] = []
    lock = threading.Lock()
    for _ in range(thread_num):
        thread = threading.Thread(target=assign_account, args=(accounts,) ,name = f"Tread-{str(_)}")
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
