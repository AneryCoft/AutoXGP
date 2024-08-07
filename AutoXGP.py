"""
Develped by AneryCoft
Github:https://github.com/AneryCoft
2024.1.25
"""

import time
import random
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
import ctypes
import configparser
import httpx
import urllib3
import re
from urllib import parse
import base64
import hashlib
import uuid
import json
import threading
from typing import List
import traceback
import datetime
import execjs

 
def output(message: str):
    "输出时间 线程名 信息"
    current_time = datetime.datetime.now().strftime("%H-%M-%S")
    current_thread_name = threading.current_thread().name
    print(f"[{current_time}] {current_thread_name} {message}")

def random_str(length: int) -> str:
    "生成随机字符串"
    characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890"
    return ''.join(random.choices(characters, k=length))

def edge(headless:bool) -> webdriver.Edge:
    """
    使用webdriver创建Edge浏览器
    """
    options = Options()
    options.binary_location = (
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    )
    if headless:
        options.add_argument("--headless")
    options.add_argument("--inprivate")
    options.add_experimental_option("useAutomationExtension", False)
    # 禁用调试信息
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    return webdriver.Edge(options=options)

def fix_base64_str(string:str) -> str:
    """
    修复Base64编码的字符串
    避免 binascii.Error: Incorrect padding
    """
    length = len(string)
    if length % 4:
        string += "=" * (4 - length % 4)
    return string

def do_submit(code:str, client:httpx.Client, headers:dict, redirects:bool=False) -> httpx.Response|None:
    "发送JavaScript中的请求"
    url_match = re.search(r'action="(.+?)"', code)
    if url_match:
        url = url_match.group(1)
        method = re.search(r'method="(.+?)"', code).group(1)
        items = re.findall(r'<input (.+?)>', code)
        body = {}
        for item in items:
            name = re.search(r'name="(.+?)"', item).group(1)
            value = re.search(r'value="(.+?)"', item).group(1)
            body[name] = value
        return client.request(method=method, url=url, data=body, headers=headers ,follow_redirects=redirects)
    return None

def getXGP(account:str):
    # 用于计算用时
    start_time = time.time()

    parts = account.split(split_symbol)
    ms_email = parts[0]
    ms_password = parts[1]

    client = httpx.Client(http2=True, proxy=proxy, verify=False, timeout=None)

    for cookie in alipay_cookies:
        client.cookies.set(cookie["name"], cookie["value"], domain=cookie["domain"])

    output(account)

    # OAuth2.0
    url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize"
    client_id = "1f907974-e22b-4810-a9de-d9647380c97e"
    client_request_id = str(uuid.uuid1())
    code_verifier = random_str(43).encode()
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
        "accept-language": "zh-CN,zh;q=0.9"
    }
    oauth2 = client.get(url=url, params=params, headers=headers, follow_redirects=True)

    # 登录微软

    # 发送账户
    url = "https://login.live.com/GetCredentialType.srf"
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
    post_email = client.post(url=url, headers=headers, json=body)

    if post_email.json()["IfExistsResult"] == 1:
        output(f"微软账户错误")
        return

    # 发送密码
    opid = re.search(r"opid=(.+?)&", oauth2.text).group(1)
    url = f"https://login.live.com/ppsecure/post.srf?opid={opid}&uaid={uaid}"
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
    post_password = client.post(url=url, headers=headers, data=body)

    # 隐私声明
    """
    url_match = re.search(r'action="(.+?)"',post_password.text)
    if url_match:
        url = url_match.group(1)
        if url.split("?")[0] == "https://privacynotice.account.microsoft.com/notice":
            body = {
                "correlation_id": re.search(r'id="correlation_id" value="(.+?)">',post_password.text).group(1),
                "code": re.search(r'id="code" value="(.+?)">',post_password.text).group(1)
            }
            privacy_notice = client.post(url=url, data=body, headers=headers)
    """

    # 跳过登录保护
    # 这个界面的出现不固定
    add_proofs = do_submit(post_password.text,client,headers)

    skip_prove_body = {
        "iProofOptions": "Email",
        "DisplayPhoneCountryISO": "CN",
        "DisplayPhoneNumber": "",
        "EmailAddress": "",
        "canary": "",
        "action": "Skip",
        "PhoneNumber": "",
        "PhoneCountryISO": ""
    }

    if add_proofs:
        canary = re.search(r'name="canary" value="(.+?)"',add_proofs.text).group(1)
        skip_prove_body["canary"] = canary
        skip_add_proof = client.post(url=url, data=skip_prove_body, headers=headers,follow_redirects=True)
    
    # 取消保持登录状态
    url = f"https://login.live.com/ppsecure/post.srf?nopa=2&uaid={uaid}&opid={opid}"
    body = {
        "LoginOptions": "3",
        "type": "28",
        "ctx": "",
        "hpgrequestid": "",
        "PPFT": flow_token,
        "canary": ""
    }
    keep_login = client.post(url=url, data=body, headers=headers)
    params_respond = keep_login

    add_proofs = do_submit(keep_login.text,client,headers)
    if add_proofs:
        canary = re.search(r'name="canary" value="(.+?)"',add_proofs.text).group(1)
        skip_prove_body["canary"] = canary
        skip_add_proof = client.post(url=url, data=skip_prove_body, headers=headers,follow_redirects=True)
        params_respond = skip_add_proof

    # 登录Xbox
    
    url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
    headers["origin"] = "https://www.xbox.com"
    code = re.search(r'code=(.+?)&',params_respond.headers["Location"]).group(1)
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
    "code_verifier": code_verifier.decode(),
    "grant_type": "authorization_code",
    "client_info": "1",
    "client-request-id": client_request_id,
    "X-AnchorMailbox": ""
    }
    oauth2_token = client.post(url=url, data=body, headers=headers)

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
    logged_in = client.get(url=url, params=params, headers=headers, follow_redirects=True)

    # 创建Xbox档案

    logged_in_redirects = logged_in.history
    session_id_match = re.search(r'sid=(.+?)&',logged_in_redirects[2].headers["Location"])
    if len(logged_in_redirects) > 2 and session_id_match:
        session_id = session_id_match.group(1)
        url = f"https://sisu.xboxlive.com/proxy?sessionid={session_id}"
        headers["authorization"] = re.search(r'spt=(.+?)&',logged_in_redirects[2].headers["Location"]).group(1)
        reservation_id = 1234567890
        body = {
            "GamertagReserve": {
                "Gamertag": "",
                "ReservationId": reservation_id,
                "Duration": "1:00:00"
            }
        }
        # 测试代号是否可用
        xbox_prefix = config.get("Prefix", "xbox_prefix")
        while True:
            xbox_gamertag = xbox_prefix + random_str(15 - len(xbox_prefix))
            body["GamertagReserve"]["Gamertag"] = xbox_gamertag
            gamertag_test = client.post(url=url, json=body, headers=headers)
            if gamertag_test.is_success:
                break

        # 设置代号
        body = {
            "CreateAccountWithGamertag": {
                "Gamertag": xbox_gamertag,
                "ReservationId": reservation_id
            }
        }
        set_gamertag = client.post(url=url, json=body, headers=headers)
        current_gamertag = set_gamertag.json()["gamerTag"]
        if current_gamertag == xbox_gamertag:
            output(f"已设置Xbox玩家代号为:{xbox_gamertag}")

        # 设置头像
        body = {
            "SetGamerpic": {
                "GamerPic": "https://dlassets-ssl.xboxlive.com/public/content/ppl/gamerpics/00052-00000-md.png?w=320&h=320"
            }
        }
        set_gamerpic = client.post(url=url, json=body, headers=headers)

        # 可选诊断数据
        """
        url = "https://sisu.xboxlive.com/client/v32/default/view/consent.html?action=signup&flowType=new_user"
        consent = client.get(url=url, json=body, headers=headers)

        body = {
            "CheckConsents": {}
        }
        check_consents = client.post(url=url, json=body, headers=headers)

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
        set_consents = client.post(url=url, json=body, headers=headers)
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
    xbox_auth_1 = client.post(url=url, json=body, headers=headers)

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
    xbox_auth_2 = client.post(url=url, json=body, headers=headers)

    # 订阅XGP

    url = "https://www.microsoft.com/store/buynow?noCanonical=true&market=HK&locale=zh-HK&clientName=XboxCom"
    uhs = xbox_auth_2.json()["DisplayClaims"]["xui"][0]["uhs"]
    microsoft_token = xbox_auth_2.json()["Token"]
    XToken = f"XBL3.0 x={uhs};{microsoft_token}"
    body = {
        "data": '{"usePurchaseSdk":true}',
        "market": "HK",
        "cV": "",
        "locale": "zh-HK",
        "xToken": XToken,
        "pageFormat": "full",
        "products": '[{"productId":"CFQ7TTC0KGQ8","skuId":"0002","availabilityId":"CFQ7TTC0L6B2"}]',
        "campaignId": "xboxcomct",
        "callerApplicationId": "XboxCom",
        "expId": "EX:sc_xboxspinner,EX:sc_xboxclosebutton,EX:sc_xboxgamepad,EX:sc_xboxuiexp,EX:sc_disabledefaultstyles,EX:sc_gamertaggifting",
        "flights[0]": "sc_xboxspinner",
        "flights[1]": "sc_xboxclosebutton",
        "flights[2]": "sc_xboxgamepad",
        "flights[3]": "sc_xboxuiexp",
        "flights[4]": "sc_disabledefaultstyles",
        "flights[5]": "sc_gamertaggifting",
        "urlRef": "https://www.xbox.com/zh-HK/auth/msa?action=loggedIn&locale_hint=zh-HK",
        "clientType": "XboxCom",
        "layout": "Modal",
        "cssOverride": "XboxCom2NewUI",
        "theme": "light",
        "timeToInvokeIframe": "83329.29999999981",
        "sdkVersion": "VERSION_PLACEHOLDER"
    }
    buy_xgp = client.post(url=url, data=body, headers=headers)

    # 选择支付方式
    cart_id = re.search(r'"cartId":"(.*?)"', buy_xgp.text).group(1)
    if cart_id == "":
        output("出现异常 请使用网络代理")
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
    payment_method_descriptions = client.get(url=url, params=params, headers=headers)

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
    payment_instruments_ex = client.post(url=url, json=body, headers=headers)

    # 支付宝签约页面
    url = payment_instruments_ex.json()["clientAction"]["context"][0]["displayDescription"][0]["members"][3]["members"][0]["pidlAction"]["context"]["baseUrl"]
    payment_instrument_id = payment_instruments_ex.json()["id"]
    params = {
        "ru": f"https://www.microsoft.com/zh-HK/store/rds/v2/GeneralAddPISuccess?picvRequired=False&pendingOn=Notification&type=alipay_billing_agreement&family=ewallet&id={payment_instrument_id}",
        "rx": "https://www.microsoft.com/zh-HK/store/rds/v2/GeneralAddPIFailure"
    }
    headers.pop("origin")
    headers.pop("authorization")
    alipay_deduct = client.get(url=url, params=params, headers=headers, follow_redirects=True)
    
    # 发送支付宝支付密码签约
    url = "https://securitycore.alipay.com/securityAjaxValidate.json"
    aliedit_uid = re.search(r'name="alieditUid" value="(.+?)"',alipay_deduct.text).group(1)
    security_id = re.search(r'name="securityId" value="(.+?)"',alipay_deduct.text).group(1)

    PK = re.search(r'PK: "(.+?)"',alipay_deduct.text).group(1)
    TS = re.search(r'TS: "(.+?)"',alipay_deduct.text).group(1)
    ksk = re.search(r"ksk: '(.+?)'",alipay_deduct.text).group(1)
    pay_password:str = alipay_encrypt_js.call("securityPassword",alipay_pay_password,PK,TS)
    key_seq:str = alipay_encrypt_js.call("getKeySeq",ksk)

    params = {
        "sendCount": "3",
        "dataId": int(time.time() * 1000),
        "dataSize": "1",
        "dataIndex": "0",
        "dataContent": '{"payment_password":{"J_aliedit_key_hidn":"payPassword","J_aliedit_uid_hidn":"alieditUid","J_aliedit_using":true,"payPassword":"%s","alieditUid":"%s","ks":"%s","security_activeX_enabled":false}}'
        % (pay_password, aliedit_uid, key_seq),
        "_callback": "light.packetRequest._packetCallbacks.callback0",
        "securityId": security_id,
        "orderId": "null"
    }
    headers["referer"] = "https://mdeduct.alipay.com/"
    post_pay_password = client.get(url=url, params=params, headers=headers)

    url = "https://mdeduct.alipay.com/customer/customerAgreementSignConfirm.htm"
    headers["origin"] = "https://mdeduct.alipay.com"
    headers["referer"] = str(alipay_deduct.url)
    _form_token = re.search(r'name="_form_token" value="(.+?)"',alipay_deduct.text).group(1)
    cache_context_id = re.search(r'name="cacheContextId" value="(.+?)"',alipay_deduct.text).group(1)
    e_i_i_d = re.search(r'name="e_i_i_d" value="(.+?)"',alipay_deduct.text).group(1)
    user_logon_id = re.search(r'name="userLogonId" value="(.+?)"',alipay_deduct.text).group(1)
    body = {
        "_form_token" : _form_token,
        "signFlag" : "signConfirmFromPC",
        "cacheContextId" : cache_context_id,
        "notNeedMobileCodeCheck" : "false",
        "e_i_i_d":e_i_i_d,
        "i_c_i_d":"",
        "userLogonId" : user_logon_id,
        "securityId" : security_id,
        "payPassword_input": "",
        "payPassword_rsainput":"",
        "J_aliedit_using": "true",
        "payPassword": "",
        "J_aliedit_key_hidn": "payPassword",
        "J_aliedit_uid_hidn": "alieditUid",
        "alieditUid": aliedit_uid,
        "REMOTE_PCID_NAME": "_seaside_gogo_pcid",
        "_seaside_gogo_pcid": "",
        "_seaside_gogo_": "",
        "_seaside_gogo_p": "",
        "J_aliedit_prod_type": "payment_password",
        "security_activeX_enabled": "false",
        "J_aliedit_net_info": ""
    }
    sign_confirm = client.post(url=url, data=body, headers=headers)

    headers["origin"] = "https://www.microsoft.com"
    headers["referer"] = "https://www.microsoft.com/"
    headers["authorization"] = XToken

    # 确认使用支付宝订阅
    url = f"https://paymentinstruments.mp.microsoft.com/v6.0/users/me/paymentInstrumentsEx/{payment_instrument_id}?language=zh-CHT&partner=webblends&country=hk&completePrerequisites=True"
    while True:
        add_alipay = client.get(url=url, headers=headers)
        status = add_alipay.json()["status"]
        if status != "Pending": # Active
            break

    # 设置姓名
    url = "https://paymentinstruments.mp.microsoft.com/v6.0/users/me/profiles"
    body = {
        "profileType": "consumerprerequisites",
        "profileCountry": "hk",
        "profileOperation": "add",
        "type": "consumer",
        "first_name": "Coft",
        "last_name": "Anery",
        "email_address": ms_email,
        "culture": "EN"
    }
    set_name = client.post(url=url, json=body, headers=headers)

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
    addresses = client.post(url=url, json=body, headers=headers)

    # 订阅
    url = "https://cart.production.store-web.dynamics.com/v1.0/Cart/PrepareCheckout?appId=BuyNow&context=UpdateBillingInformation"
    headers["ms-cv"] = re.search(r'"cvServerStart":"(.+?)"',buy_xgp.text).group(1)
    headers["x-authorization-muid"] = re.search(r'"alternativeMuid":"(.+?)"',buy_xgp.text).group(1)
    headers["x-ms-client-type"] = "XboxCom"
    headers["x-ms-market"] = "HK"
    headers["x-ms-vector-id"] = re.search(r'"vectorId":"(.+?)"',buy_xgp.text).group(1)
    risk_id = re.search(r'"riskId":"(.+?)"',buy_xgp.text).group(1)
    # flights = re.search(r'"flights":\[(.+?)\]', buy_xgp.text).group(1)
    # flights = flights.replace('"',"").split(",")
    body = {
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
    prepare_checkout = client.post(url=url, json=body, headers=headers)

    url = "https://paymentinstruments.mp.microsoft.com/v6.0/users/me/PaymentSessionDescriptions"
    piid = payment_instrument_id
    pi_cid = add_alipay.json()["accountId"]
    purchase_order_id = cart_id
    params = {
        "paymentSessionData" : '{"piid":"%s","language":"zh-HK","partner":"webblends","piCid":"%s","amount":29,"currency":"HKD","country":"HK","hasPreOrder":"false","challengeScenario":"RecurringTransaction","challengeWindowSize":"03","purchaseOrderId":"%s"}' % (piid,pi_cid,purchase_order_id),
        "operation": "Add"
    }
    payment_session_descriptions = client.get(url=url, params=params, headers=headers)

    url = f"https://cart.production.store-web.dynamics.com/v1.0/Cart/purchase?appId=BuyNow"
    match_addr_id = re.search(r'<Id>(.+?)</Id>',addresses.text)
    address_id:str
    if match_addr_id:
        address_id = match_addr_id.group(1)
    else:
        address_id = addresses.json()["id"]
    # address_id = re.search(r'"soldToAddressId":"(.+?)"',buy_xgp.text).group(1)

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
            "accountId": pi_cid,
            "id": address_id
        },
        "currentOrderState": "CheckingOut",
        "flights": [],
        "itemsToAdd": {}
    }
    buy_now = client.post(url=url, json=body, headers=headers)

    output("已订阅Xbox Game Pass")

    # 设置Minecraft档案

    # 登录微软账户
    """
    url = "https://www.minecraft.net/msaprofilejs/6eff6391c7c99228bb68_03012024_0244/11.chunk.c68d8eb533ea60bdfbc5.js"
    get_login_params = session.get(url=url, headers=headers, allow_redirects=False)
    """
    # cobrandId = re.search(r'sisuCobrandId:"(.+?)"', get_login_params.text).group(1)
    # tid = re.search(r'titleId:"(.+?)"', get_login_params.text).group(1)
    ru = "https%3A%2F%2Fwww.minecraft.net%2Fzh-hans%2Flogin%3Freturn_url%3Dhttps%253A%252F%252Fwww.minecraft.net%252Fzh-hans%252Fmsaprofile%252Fmygames%252Feditprofile"
    # aid = re.search(r'sisuAppId:"(.+?)"', get_login_params.text).group(1)
    url = f"https://sisu.xboxlive.com/connect/XboxLive/?state=login&ru={ru}"
    headers.pop("authorization")
    headers.pop("ms-cv")
    headers.pop("x-authorization-muid")
    headers.pop("x-ms-client-type")
    headers.pop("x-ms-market")
    headers.pop("x-ms-vector-id")
    headers["referer"] = "https://www.minecraft.net/"
    headers["origin"] = "https://www.minecraft.net"
    login_minecraft = client.get(url=url, headers=headers, follow_redirects=True)

    url = "https://api.minecraftservices.com/authentication/login_with_xbox"
    access_token_base64 = login_minecraft.history[2].headers["location"].split("#")[1].strip("state=login&accessToken=")
    access_token = json.loads(base64.b64decode(fix_base64_str(access_token_base64)))
    uhs,token = "",""
    for item in access_token:
        if item["Item1"] == "rp://api.minecraftservices.com/":
            uhs = item["Item2"]["DisplayClaims"]["xui"][0]["uhs"]
            token = item["Item2"]["Token"]
    identity_token = "XBL3.0 x=" + uhs + ";" + token
    body = {
        "ensureLegacyEnabled": True,
        "identityToken": identity_token
    }
    login_with_xbox = client.post(url=url, json=body, headers=headers)

    request_id = str(uuid.uuid1())
    url = f"https://api.minecraftservices.com/entitlements/license?requestId={request_id}"
    authorization = "Bearer " + login_with_xbox.json()["access_token"]
    headers["authorization"] = authorization
    redeem = client.get(url=url, headers=headers)

    minecraft_prefix = config.get("Prefix", "minecraft_prefix")

    # 测试ID是否可用
    while True:
        profile_name = minecraft_prefix + random_str(16 - len(minecraft_prefix))
        url = f"https://api.minecraftservices.com/minecraft/profile/name/{profile_name}/available"
        name_available = client.get(url=url, headers=headers)
        status = name_available.json()["status"]
        if status == "AVAILABLE":
            break
    
    # 设置MinecraftID
    url = "https://api.minecraftservices.com/minecraft/profile"
    body = {"profileName": profile_name}
    set_profile_name = client.post(url=url, json=body, headers=headers)
    if set_profile_name.is_success:
        output(f"已设置MinecraftID为:{profile_name}")
    elif set_profile_name.json()["details"]["status"] == "NOT_ENTITLED":
        output(f"无法修改MinecraftID!")
    
    # 设置Minecraft皮肤
    if config.getboolean("Skin","customSkin"): 
        url = "https://api.minecraftservices.com/minecraft/profile/skins"
        model = config.getint("Skin","model")
        model_list = ["classic","slim"]
        body = {"variant": model_list[model]}
        skin_path = config["Skin"]["skin"]
        skin_file = open(skin_path,"rb")
        skin = {"file":skin_file}
        custom_skin = client.post(url=url, headers=headers, data=body, files=skin)
        if custom_skin.is_success:
            output("已设置Minecraft皮肤")

    # 取消订阅

    # 登录微软账户
    url = "https://account.microsoft.com/services/pcgamepass/cancel?fref=billing-cancel"
    headers.pop("authorization")
    headers["referer"] = "https://account.microsoft.com/"
    headers["origin"] = "https://account.microsoft.com"
    login = client.get(url=url, headers=headers,follow_redirects=True)

    login_ms = do_submit(login.text,client,headers,True)

    url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize"
    client_id = "81feaced-5ddd-41e7-8bef-3e20a2689bb7"
    client_request_id = str(uuid.uuid1())
    code_verifier = random_str(43).encode()
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
    oauth2 = client.get(url=url, params=params, headers=headers, follow_redirects=True)

    url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
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
        "code_verifier": code_verifier.decode(),
        "grant_type": "authorization_code",
        "client_info": "1",
        "client-request-id": client_request_id,
        "X-AnchorMailbox": ""
    }
    oauth2_token = client.post(url=url, data=body, headers=headers)

    # 取消订阅
    url = "https://account.microsoft.com/services/pcgamepass/cancel?fref=billing-cancel&refd=account.microsoft.com"
    cancel_service_page = client.get(url=url, headers=headers)

    url = "https://account.microsoft.com/services/api/cancelservice"
    verification_token = re.search(r'name="__RequestVerificationToken" type="hidden" value="(.+?)"',cancel_service_page.text).group(1)
    headers["__requestverificationtoken"] = verification_token
    headers["ms-cv"] = client.cookies["AMC-MS-CV"]
    headers["referer"] = "https://account.microsoft.com/services/pcgamepass/cancel?fref=billing-cancel&refd=account.microsoft.com"
    headers["x-requested-with"]= "XMLHttpRequest"
    headers["x-tzoffset"]= "480"
    match_service_id = re.search(r'"active":\[{"id":"(.+?)"',cancel_service_page.text)
    if match_service_id:
        service_id = match_service_id.group(1)
    else:
        url = "https://account.microsoft.com/services/api/subscriptions-and-alerts?excludeWindowsStoreInstallOptions=false&excludeLegacySubscriptions=false"
        subscriptions_and_alerts = client.get(url=url, headers=headers)
        service_id = subscriptions_and_alerts.json()["active"][0]["id"]
    body = {
        "serviceId":service_id,
        "serviceType":"recurrence",
        "refundAmount":29,
        "riskToken":"",
        "isDunning":False,
        "locale":"zh-CN",
        "market":"HK"
    }
    cancel_service = client.put(url=url, json=body, headers=headers)

    output("已取消订阅并退款")

    # 删除付款工具
    url = "https://account.microsoft.com/auth/acquire-onbehalf-of-token?scopes=pidl"
    acquire_token = client.get(url=url, headers=headers)

    url = f"https://paymentinstruments.mp.microsoft.com/v6.0/users/me/paymentInstrumentsEx/{payment_instrument_id}?partner=northstarweb&language=zh-CN"
    headers.pop("__requestverificationtoken")
    headers["authorization"] = "MSADELEGATE1.0=" + acquire_token.json()[0]["token"]
    delete_payment_instruments = client.delete(url=url, headers=headers)

    output("已删除付款工具")

    lock.acquire()
    global XGP_file
    XGP_file.write(account + "\n")
    lock.release()

    output("用时：%.2f秒" % (time.time() - start_time))

def assign_account(accounts:List[str]):
    while True:
        lock.acquire()
        if not accounts:
            lock.release()
            break
        account = accounts.pop()
        lock.release()
        account = account.strip("\n")
        try:
            getXGP(account)
        except Exception as e:
            traceback.print_exception(e)

def set_title():
    "设置控制台标题"
    while True:
        time_now = datetime.datetime.now().replace(microsecond=0)
        elapsed = time_now - start_time
        ctypes.windll.kernel32.SetConsoleTitleW(f"AutoXGP V{VERSION} | 用时:{elapsed}")
        time.sleep(1.0)

if __name__ == "__main__":
    VERSION = "1.0"
    start_time = datetime.datetime.now().replace(microsecond=0)
    set_title_thread = threading.Thread(target=set_title,daemon=True)
    set_title_thread.start()

    config = configparser.ConfigParser()
    config.read("config.ini")

    # 获取支付宝登录Cookie

    cookie_file = open("alipayCookies.json", "r+")
    alipay_cookies = cookie_file.read()
    if alipay_cookies == "":
        driver = edge(False)
        driver.get("https://auth.alipay.com/login/index.htm?goto=https%3A%2F%2Fwww.alipay.com%2F")
        output("扫码以登录支付宝")
        # 判断是否已扫码
        while True:
            if driver.current_url.startswith("https://www.alipay.com/"):
                break
            else:
                time.sleep(0.2)
        
        alipay_cookies = driver.get_cookies()
        save_cookie = config.getboolean("Alipay", "saveCookie")
        if save_cookie:
            cookie_file.write(json.dumps(alipay_cookies))
            cookie_file.close()
            output("已保存支付宝Cookies")
        driver.quit()
    else:
        alipay_cookies = json.loads(alipay_cookies)

    # 编译JavaScript
    js_file = open("alipayEncrypt.js","r")
    alipay_encrypt_js = execjs.compile(js_file.read())
    js_file.close()

    # 获取支付宝支付密码
    alipay_pay_password:str = config.get("Alipay", "payPassword")
    if alipay_pay_password == "":
        alipay_pay_password = input("输入你的支付宝支付密码:")
        config.set("Alipay", "payPassword", alipay_pay_password)
        config_file = open("config.ini", "w")
        config.write(config_file)
        config_file.close()
        output("已在配置中保存支付宝支付密码")

    account_file = open("accounts.txt","r+")
    accounts = account_file.readlines()
    account_file.close()

    split_symbol = config.get("Account","splitSymbol")

    XGP_file = open("XGP.txt","a")

    enable_proxy = config.getboolean("Proxy","enableProxy")
    if enable_proxy:
        host = config["Proxy"]["host"]
        port = config["Proxy"]["port"]
        proxy = "http://" + host + ":" + port
    else:
        proxy = None

    thread_num = config.getint("Thread","thread")
    threads:List[threading.Thread] = []
    lock = threading.Lock()
    for _ in range(thread_num):
        thread = threading.Thread(target=assign_account,args=(accounts,))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    
    XGP_file.close()
