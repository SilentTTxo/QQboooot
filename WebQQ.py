# -*- coding: utf-8 -*-
import requests
import sys
from HttpClient import HttpClient
import re, random, md5, json, os, time, thread, subprocess, logging
import rsa, Tea, base64


#请在此处设置你的QQ号和密码
QQ = 
PASS = "here"


"""
  下面的配置信息,请不要修改,除非你知道它的作用是什么
"""

ClientID = 8534174
APPID = 1003903
PSessionID = ''

#RSA 公钥
pubkey = "F20CE00BAE5361F8FA3AE9CEFA495362FF7DA1BA628F64A347F0A8C012BF0B254A30CD92ABFFE7A6EE0DC424CB6166F8819EFA5BCCB20EDFB4AD02E412CCF579B1CA711D55B8B0B3AEB60153D5E0693A2A86F3167D7847A0CB8B00004716A9095D9BADC977CBB804DBDCBA6029A9710869A453F27DFDDF83C016D928B3CBF4C7"
rsaPublickey = int(pubkey, 16)
key = rsa.PublicKey(rsaPublickey, 3)

reload(sys)   
sys.setdefaultencoding('utf8')
def getTEAPass(q, p, v):
  #MD5 密码
  p = md5.new(p).digest()

  #TEA 的KEY
  m = md5.new(p + ("%0.16X" % q).decode('hex')).digest()

  #RSA的加密结果
  n = rsa.encrypt(p, key)

  #RSA 结果的长度
  d = ("%0.4X" % len(n)).decode('hex')

  #RSA 加密结果
  d += n

  #salt
  d += ("%0.16X" % q).decode('hex')

  #验证码长度
  d += ("%0.4X" % len(v)).decode('hex')

  #验证码
  d += v.upper()

  #TEA 加密并Base64编码
  r = base64.b64encode(Tea.encrypt(d, m))

  #对特殊字符进行替换
  return r.replace('/', '-').replace('+', '*').replace('=', '_')

#旧版的, 已经弃用了
def getEncPass(q, p, v):
  m = md5.new(p).digest() + ("%0.16X" % q).decode('hex')
  return md5.new(md5.new(m).hexdigest().upper() + v.upper()).hexdigest().upper()

def runCommand(cmd, uin):
  ret = 'Run Command: [{0}]\n'.format(cmd)

  try:
    popen_obj = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0, env=os.environ.copy())
    (stdout, stderr) = popen_obj.communicate()

    ret += stdout.strip()
    ret += '\n' + stderr.strip()
  except Exception, e:
    ret += e

  SendQQMsg(uin, ret)


def SendMsg(url, id, msg, msgType):
  global ClientID, PSessionID, http, Referer, MsgID
  MsgID = MsgID + 1

  msg = msg.replace('\\', '\\\\\\\\').replace('\t', '\\\\t').replace('\r', '\\\\r').replace('\n', '\\\\n')
  msg = msg.replace('"', '\\\\\\"')

  http.Post("http://d.web2.qq.com/channel/{0}".format(url), (
    ('r', '{{"{5}":{0},"face":600,"content":"[\\"{4}\\",[\\"font\\",{{\\"name\\":\\"Arial\\",\\"size\\":\\"10\\",\\"style\\":[0,0,0],\\"color\\":\\"000000\\"}}]]","msg_id":{1},"clientid":"{2}","psessionid":"{3}"}}'.format(id, MsgID, ClientID, PSessionID, msg, msgType)),
    ('clientid', ClientID),
    ('psessionid', PSessionID)
  ), Referer)
  logging.debug("send ok")


def SendQQMsg(uin, msg):
  SendMsg('send_buddy_msg2', uin, msg, 'to')

def SendGroupMsg(qid, msg):
  SendMsg('send_qun_msg2', qid, msg, 'group_uin')

def Answer(content):
  ans = requests.get(u"http://www.tuling123.com/openapi/api?key=1a37e6f408e5b6dcb7b6601bd7ad746a&info={0}".format(content))
  return ans.json()['text']

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s  %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',filename='QQlog.log', datefmt='[%Y-%m-%d %H:%M:%S]')


http = HttpClient()


initUrl = "https://ui.ptlogin2.qq.com/cgi-bin/login?daid=164&target=self&style=5&mibao_css=m_webqq&appid={0}&enable_qlogin=0&no_verifyimg=1&s_url=http%3A%2F%2Fweb2.qq.com%2Floginproxy.html&f_url=loginerroralert&strong_login=1&login_state=10&t=".format(APPID)

html = http.Get(initUrl, 'http://web2.qq.com/webqq.html')

sign = re.search(r'var g_login_sig=encodeURIComponent\("(.+?)"\);', html)

if sign is None:
  logging.error('get login sign error')
else:
  sign = sign.group(1)

logging.info('get sign : %s', sign)



html = http.Get("https://ssl.ptlogin2.qq.com/check?pt_tea=1&uin={0}&appid={1}&js_ver=10116&js_type=0&login_sig={2}&u1=http%3A%2F%2Fweb2.qq.com%2Floginproxy.html&r=0.5331138293443659".format(QQ, APPID, sign), initUrl)

logging.debug(html)

html = html.split("'")

if len(html) == 0:
  exit()

vc = None

if html[1] == '1':
  logging.info('need validate code')
  http.Download("https://ssl.captcha.qq.com/getimage?aid={0}&r={1}&uin={2}".format(APPID, random.random(), QQ), "v.jpg")
  verifysession = http.getCookie('verifysession')
  print("need Validate Code,Please input it")
  vc = raw_input()
else:
  vc = html[3]
  verifysession = html[7]

if vc is None:
  logging.error('get validate code error')
  quit()

vc = vc.strip()

logging.info(vc)

logging.info('verifysession: {0}'.format(verifysession))

html = http.Get("https://ssl.ptlogin2.qq.com/login?u={0}&p={1}&verifycode={2}&webqq_type=10&remember_uin=1&login2qq=1&aid={3}&u1={4}&h=1&ptredirect=0&ptlang=2052&daid=164&from_ui=1&pttype=1&dumy=&fp=loginerroralert&action=1-41-15424&mibao_css=m_webqq&t=1&g=1&js_type=0&js_ver=10116&login_sig={5}&pt_uistyle=5&pt_randsalt=0&pt_vcode_v1=0&pt_verifysession_v1={6}".format(QQ, getTEAPass(QQ, PASS, vc), vc, APPID, "http%3A%2F%2Fweb.qq.com%2Floginproxy.html%3Flogin2qq%3D1%26webqq_type%3D10", sign, verifysession), initUrl)

html = html.split("'")

if html[1] != '0':
  logging.error("'".join(html))
  quit()

PTWebQQ = http.getCookie('ptwebqq')

logging.info('PTWebQQ: {0}'.format(PTWebQQ))

html = http.Get(html[5])

while 1:
  html = http.Post('http://d.web2.qq.com/channel/login2', (
    ('r', '{{"status":"online","ptwebqq":"{0}","passwd_sig":"","clientid":"{1}","psessionid":"{2}"}}'.format(PTWebQQ, ClientID, PSessionID)),
    ('clientid', ClientID),
    ('psessionid', 'null')
  ), 'http://s.web2.qq.com/proxy.html?v=20110412001&callback=1&id=3')

  logging.debug(html)

  ret = json.loads(html)

  if ret['retcode'] != 0:
    quit()

  VFWebQQ = ret['result']['vfwebqq']
  PSessionID = ret['result']['psessionid']

  logging.info('Login success')
  print("Login success")

  Referer = 'http://d.web2.qq.com/proxy.html?v=20110331002&callback=1&id=2'
  MsgID = 38200000

  E = 0
  while 1:
    html = http.Post('http://d.web2.qq.com/channel/poll2', (
      ('r', '{{"clientid":"{0}","psessionid":"{1}","key":0,"ids":[]}}'.format(ClientID, PSessionID)),
      ('clientid', ClientID),
      ('psessionid', PSessionID)
    ), Referer)

    if html == '':
      continue

    try:
      ret = json.loads(html)
      E = 0
      #jsonStr = json.dumps(ret)
      #print jsonStr
    except Exception, e:
      logging.debug(e)
      E += 1
      if E > 5:
        break
      time.sleep(2)
      continue

    if ret['retcode'] == 102:#无消息
      continue
    if ret['retcode'] == 116:#更新PTWebQQ值
      PTWebQQ = ret['p']
      continue
    if ret['retcode'] == 0:
      for msg in ret['result']:
        msgType = msg['poll_type']
        if msgType == 'message':#QQ消息
          txt = msg['value']['content'][1]
          logging.debug("QQ Message:" + txt)
          SendQQMsg(msg['value']['from_uin'],"ok")
          if txt[0] == '#':
              thread.start_new_thread(runCommand, (txt[1:].strip(), msg['value']['from_uin']))
          if txt[0:4] == 'exit':
              http.Get('http://d.web2.qq.com/channel/logout2?ids=&clientid={0}&psessionid={1}'.format(ClientID, PSessionID), Referer)
              exit()
        elif msgType == 'sess_message':#QQ临时会话的消息
          logging.debug(msg['value']['content'][1])
        elif msgType == 'group_message':#群消息
          try:
          	txt = msg['value']['content'][1]
          	#print("群({0})---{1}:".format(msg['value']['info_seq'],msg['value']['content'][0][1].name)
          	#print(u"Group({0}):".format(msg['value']['info_seq']) + txt)
          	if txt[0:3] == '@JG':
          	  SendGroupMsg(msg['value']['from_uin'],Answer(txt[4:]))
          except Exception, e:
          	print(e)
        elif msgType == 'discu_message':#讨论组的消息
          txt = msg['value']['content'][1]
          logging.debug("Discu Message:" + txt)
        elif msgType == 'kick_message':
          logging.error(msg['value']['reason'])
          exit()
        elif msgType != 'input_notify':
          logging.debug(msg)
    else:
      logging.debug(ret)

# vim: tabstop=2 softtabstop=2 shiftwidth=2 expandtab
