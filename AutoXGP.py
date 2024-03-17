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

 
def output(message: str):
    """
    输出信息和时间
    """
    localTime = time.localtime()
    print(f"[{localTime.tm_hour}:{localTime.tm_min}:{localTime.tm_sec}] {message}")

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

def getXGP(account:str):
    # 用于计算用时
    start_time = time.time()

    parts = account.split("----")
    ms_email = parts[0]
    ms_password = parts[1]

    client = httpx.Client(http2=True, proxy=proxy, verify=False, timeout=None)
    """
    for cookie in alipay_cookies:
        client.cookies.set(cookie["name"], cookie["value"], domain=cookie["domain"])
    """
    
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
        output(f"微软账户错误:{ms_email}")
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

    # 取消保持登录状态
    
    url = f"https://login.live.com/ppsecure/post.srf?nopa=2&uaid={uaid}&opid={opid}&route=C107_SN1"
    body = {
        "LoginOptions": "3",
        "type": "28",
        "ctx": "",
        "hpgrequestid": "",
        "PPFT": flow_token,
        "canary": ""
    }
    keep_login = client.post(url=url, data=body, headers=headers)
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
            add_proofs = client.post(url=url, headers=headers, data=body)

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
            skip = client.post(url=url, data=body, headers=headers)

            # 跳过摆脱密码束缚
            url = skip.headers["Location"]
            authenticator_cancel = client.post(url=url, headers=headers)
            login_action = authenticator_cancel

    # 登录Xbox
    
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
    login_in = client.get(url=url, params=params, headers=headers, follow_redirects=True)

    # 创建Xbox档案

    session_id_match = re.search(r'sid=(.+?)&',login_in.history[2].headers["Location"])
    if session_id_match:
        session_id = session_id_match.group(1)
        url = f"https://sisu.xboxlive.com/proxy?sessionid={session_id}"
        headers["authorization"] = re.search(r'spt=(.+?)&',login_in.history[2].headers["Location"]).group(1)
        xbox_prefix = config.get("Prefix", "xbox_prefix")
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
        # current_gametag = set_gamertag.json["gamerTag"]
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

    url = f"https://www.microsoft.com/store/buynow?noCanonical=true&market=HK&locale=zh-HK&clientName=XboxCom"
    uhs = xbox_auth_2.json()["DisplayClaims"]["xui"][0]["uhs"]
    microsoft_token = xbox_auth_2.json()["Token"]
    XToken = f"XBL3.0 x={uhs};{microsoft_token}"
    body = {
        "data": '{"products":[{"productId":"CFQ7TTC0KGQ8","skuId":"0002","availabilityId":"CFQ7TTC0KF41"}],"campaignId":"xboxcomct","callerApplicationId":"XboxCom","expId":["EX:sc_xboxgamepad","EX:sc_xboxspinner","EX:sc_xboxclosebutton","EX:sc_xboxuiexp","EX:sc_disabledefaultstyles","EX:sc_gamertaggifting"],"flights":["sc_xboxgamepad","sc_xboxspinner","sc_xboxclosebutton","sc_xboxuiexp","sc_disabledefaultstyles","sc_gamertaggifting"],"clientType":"XboxCom","data":{"usePurchaseSdk":true},"layout":"Modal","cssOverride":"XboxCom2NewUI","theme":"light","scenario":"","suppressGiftThankYouPage":false}',
        "auth": '{"XToken":"%s"}' % XToken
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
    payment_instruments_ex = client.get(url=url, params=params, headers=headers)

    url = payment_instruments_ex.headers["location"]
    lock.acquire()
    driver.get(url)
    input_pay_password = driver.find_element(By.ID, "payPassword_rsainput").send_keys(alipay_pay_password)
    agree = driver.find_element(By.ID, "J_submit").click()
    # 代扣开通成功
    driver.find_element(By.XPATH, '//*[@id="container"]/div/div[1]/p[1]')
    lock.release()

    # TODO Alipay pay password encrypt
    """ 
    direct_alipay = client.get(url=url, headers=headers)

    url = direct_alipay.headers["Location"]
    alipay_html = client.get(url=url, headers=headers)

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
    post_pay_password = client.get(url=url, params=params, headers=headers)

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
    sign_confirm = client.post(url=url, data=body, headers=headers)
    """

    """
    url = sign_confirm.headers["Location"]
    agreement_operation_result = client.get(url=url, headers=headers)
    """

    # 确认使用支付宝订阅
    url = f"https://paymentinstruments.mp.microsoft.com/v6.0/users/me/paymentInstrumentsEx/{payment_instrument_id}?language=zh-CHT&partner=webblends&country=hk&completePrerequisites=True"
    add_alipay = client.get(url=url, headers=headers)

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
    url = "https://cart.production.store-web.dynamics.com/v1.0/Cart/PrepareCheckout?appId=BuyNow&perf=true&context=UpdateBillingInformation"
    ms_cv = random_str(22)
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
    prepare_checkout = client.post(url=url, json=body, headers=headers)

    url = "https://paymentinstruments.mp.microsoft.com/v6.0/users/me/PaymentSessionDescriptions"
    piid = payment_instrument_id
    piCid = add_alipay.json()["accountId"]
    purchaseOrderId = cart_id
    params = {
        "paymentSessionData" : '{"piid":"%s","language":"zh-HK","partner":"webblends","piCid":"%s","amount":29,"currency":"HKD","country":"HK","hasPreOrder":"false","challengeScenario":"RecurringTransaction","challengeWindowSize":"03","purchaseOrderId":"%s"}' % (piid,piCid,purchaseOrderId),
        "operation": "Add"
    }
    payment_session_descriptions = client.get(url=url, params=params, headers=headers)

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
    headers.pop("x-ms-correlation-id")
    headers.pop("x-ms-vector-id")
    headers["referer"] = "https://www.minecraft.net/"
    headers["origin"] = "https://www.minecraft.net"
    login_minecraft = client.get(url=url, headers=headers, follow_redirects=True)

    url = "https://api.minecraftservices.com/authentication/login_with_xbox"
    access_token_base64 = login_minecraft.history[2].headers["location"].split("#")[1].strip("state=login&accessToken=")
    access_token = json.loads(base64.b64decode(fix_base64_str(access_token_base64)))
    identityToken = "XBL3.0 x=" + access_token[1]["Item2"]["DisplayClaims"]["xui"][0]["uhs"] + ";" + access_token[1]["Item2"]["Token"]
    body = {
        "ensureLegacyEnabled": True,
        "identityToken": identityToken
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
        customSkin = client.post(url=url, headers=headers, data=body, files=skin)
        if customSkin.is_success:
            output("已设置Minecraft皮肤")

    # 取消订阅

    url = "https://account.microsoft.com/services/pcgamepass/cancel?fref=billing-cancel"
    headers.pop("authorization")
    billing_cancel = client.get(url=url, headers=headers, follow_redirects=True)

    # 登录微软账户
    url = "https://account.microsoft.com/auth/complete-signin?ru=https%3A%2F%2Faccount.microsoft.com%2Fservices%2Fpcgamepass%2Fcancel%3Ffref%3Dbilling-cancel&wa=wsignin1.0"
    body = {
        "pprid": re.search(r'id="pprid" value="(.+?)">', billing_cancel.text).group(1),
        "NAP": re.search(r'id="NAP" value="(.+?)">', billing_cancel.text).group(1),
        "ANON": re.search(r'id="ANON" value="(.+?)">', billing_cancel.text).group(1),
        "t": re.search(r'id="t" value="(.+?)">', billing_cancel.text).group(1)
    }
    login_ms = client.post(url=url, data=body, headers=headers, follow_redirects=True)

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
    headers["referer"] = "https://account.microsoft.com/"
    oauth2 = client.get(url=url, params=params, headers=headers, follow_redirects=True)

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
    headers["x-edge-shopping-flag"]= "0"
    headers["x-requested-with"]= "XMLHttpRequest"
    headers["x-tzoffset"]= "480"
    match_serviceId = re.search(r'"active":\[{"id":"(.+?)"',cancel_service_page.text)
    if not match_serviceId:
        url = "https://account.microsoft.com/services/api/subscriptions-and-alerts?excludeWindowsStoreInstallOptions=false&excludeLegacySubscriptions=false"
        subscriptions_and_alerts = client.get(url=url, headers=headers)
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
    cancel_service = client.put(url=url, json=body, headers=headers)

    output("已取消订阅并退款")

    lock.acquire()
    global XGP_file
    XGP_file.write(account + "\n")
    lock.release()

    output("用时：%.2f秒" % (time.time() - start_time))

def assign_account(accounts:list[str]):
    while True:
        lock.acquire()
        if not accounts:
            lock.release()
            break
        account = accounts.pop()
        lock.release()
        if account[0] != "#":
            account = account.strip("\n")
            getXGP(account)


if __name__ == "__main__":
    # 设置控制台标题
    ctypes.windll.kernel32.SetConsoleTitleW("Auto Xbox Game Pass")

    config = configparser.ConfigParser()
    config.read("config.ini")

    # 获取支付宝登录Cookie
    cookie_file = open("alipayCookies.json", "r+")
    alipay_cookies = cookie_file.read()
    driver = edge(False)
    driver.implicitly_wait(5.0)
    if alipay_cookies == "":
        driver.get("https://auth.alipay.com/login/index.htm?goto=https%3A%2F%2Fwww.alipay.com%2F")
        output("扫码以登录支付宝")
        # 判断是否已扫码
        while True:
            if driver.current_url.startswith("https://www.alipay.com/"):
                break
            else:
                time.sleep(0.2)
        driver.minimize_window()
        alipay_cookies = driver.get_cookies()

        save_cookie = config.getboolean("Alipay", "saveCookie")
        if save_cookie:
            cookie_file.write(json.dumps(alipay_cookies))
            output("已保存支付宝Cookies")
    else:
        driver.get("https://www.alipay.com/")
        alipay_cookies = json.loads(alipay_cookies)
        for cookie in alipay_cookies:
            driver.add_cookie(cookie)
    cookie_file.close()

    # 获取支付宝支付密码
    alipay_pay_password = config.getint("Alipay", "payPassword")
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

    XGP_file = open("XGP.txt","a")

    enable_proxy = config.getboolean("Proxy","enableProxy")
    if enable_proxy:
        host = config["Proxy"]["host"]
        port = config["Proxy"]["port"]
        proxy = "http://" + host + ":" + port
    else:
        proxy = None

    urllib3.disable_warnings()

    thread_num = config.getint("Thread","thread")
    threads:list[threading.Thread] = []
    lock = threading.Lock()
    for _ in range(thread_num):
        thread = threading.Thread(target=assign_account,args=(accounts,))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()
    
    XGP_file.close()
    driver.quit()
