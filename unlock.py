# -*- coding: utf-8 -*-
import sys
import time
import random
import httplib
import subprocess

# 产生用户名，用来向htcdev注册账号
def generate_user():
    key='u'
    charlist=['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 
              'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 
              'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    lenlist=len(charlist)
    for i in xrange(1, 18):
        key=key+charlist[random.randrange(0, lenlist, 1)]
    return key

# 生成账户注册数据，可以打开 https://www.htcdev.com/register/ 对照里面要填的内容
def generate_body(user, password, mailcatch):
    body='XID={XID_HASH}&ACT=7&RET=http://www.htcdev.com//register/success&FROM='
    id2='&m_field_id_2='
    id2=id2+user
    id3='&m_field_id_3='
    id3=id3+user
    email='&email='
    email=email+user
    email=email+mailcatch
    uname='&username='
    uname=uname+user
    pwd='&password='
    pwd=pwd+password
    pwdc='&password_confirm='
    pwdc=pwdc+password
    id1='&m_field_id_1='
    id1=id1+'China'
    body=body+id2
    body=body+id3
    body=body+email
    body=body+uname
    body=body+pwd
    body=body+pwdc
    body=body+id1
    return body
    
# 从cookie中解析出指定的字符串
def extract_cookie(cookie, key):
    index=cookie.find(key)
    if index==-1:
        print "no ", key
        return " "
    pair=cookie[index:]
    index=pair.find(";")
    if index==-1:
        print "no end for ", key
        return " "
    pair=pair[:index]
    return pair           

if __name__ == "__main__":
    #
    # 将手机设置到bootloader状态
    #
    cmd=r"c:/htcunlock/adb reboot-bootloader"
    subprocess.call(cmd)
    #
    # 向htcdev注册账户信息
    #    
    htcdev="www.htcdev.com"
    uri="/"
    header={"Content-type":"application/x-www-form-urlencoded", "Accept":"text/plain"}
    # 用户名随机生成
    user=generate_user()
    # 密码也可以随便填
    password='xthzfrsHuAMd'
    # 使用mailcatch提供的邮件，注册账户信息
    mailcatch='@mailcatch.com'    
    body=generate_body(user,password,mailcatch)   
    connhtc=httplib.HTTPConnection(htcdev)
    connhtc.request("POST", uri, body, header)
    rsphtc=connhtc.getresponse()
    print rsphtc.status, rsphtc.reason
    data=rsphtc.read()
    # 
    # htcdev将向账户关联的mailcatch邮箱发送邮件，其中包含确认签名
    # 从mailchat中取回该确认签名
    #
    sign=""
    found=0
    mailcatch="mailcatch.com"
    uri="/en/temporary-inbox?box="+user
    connmail=httplib.HTTPConnection(mailcatch)
    # 确认签名是映射中键first_mail_id对应的值，轮询mailcatch服务，直到找到签名为止
    for i in xrange(1,20):
        index=0
        found=0
        f=open(r"c:/htcunlock/mymailcatchtmp", "w+")
        connmail.request("GET", uri)
        rspmail=connmail.getresponse()    
        print rspmail.status, rspmail.reason
        data=rspmail.read()
        f.write(data)
        f.seek(0)
        while True:
            line=f.readline()
            index=index+1
            if len(line)==0:
	            print "reach EOF. mail index:%d, line counts:%d" %(i, index)
	            break
            if "first_mail_id" in line:
                v=line.find("value")
                if v==-1:
                    continue
                line=line[v:]
                low=line.find("'")
                high=line.rfind("'")
                if low==-1:
                    continue
                length=high-low
                low=low+1
                # length:36
                if length >= 30:
                    sign=line[low:high]
                    found=1
                    break
        if found==1:
            f.close()
            break;
        f.close()
        
    if found==0:
        print "not found register ack signature,exit."
        connhtc.close()
        connmail.close()
        sys.exit()
    #
    # htcdev会向mailcatch邮箱发送邮件，其中包含账户的激活链接，
    # 从mailcatch取回该激活链接的网址
    # 激活链接的网址的格式是：www.htcdev.com/?ACT=x&id=xxxxxxxxxx
    #       
    show="&show="+sign
    uri="/en/temporary-mail-content?box="+user
    uri=uri+show
    website=""
    found=0  
    for i in xrange(1,8):
        index=0
        found=0
        f=open(r"c:/htcunlock/mymailcatchtmp", "w+")      
        connmail.request("GET", uri)
        try:
            rspmail=connmail.getresponse()
        except:
            print "get mail content response exception, mail index:", i
            continue
        print rspmail.status, rspmail.reason
        data=rspmail.read()
        f.write(data)
        f.seek(0)
        while True:
            line=f.readline()
            index=index+1
            if len(line)==0:
                print "reach EOF, mail index:%d, line counts:%d" %(i, index)
                break;
            if "www.htcdev.com/?ACT" in line:
                website=line
                found=1
                break
        if found==1:
            f.close()
            break
        f.close()
    
    if found==0:
        print "not received activate notice, exit."
        connhtc.close()
        connmail.close()
        sys.exit()
    #
    # 有时候从mailcatch取回的激活链接网址中会包含非法字符串，这种情况下删除非法字符串
    #
    index=website.find("?")
    if index==-1:
        print "no ACT string, exit."
        connhtc.close()
        connmail.close()
        sys.exit()
    uri=website[index:]
    uri="/"+uri
    index=uri.find("&")
    if index==-1:
        print "no & char, exit."
        connhtc.close()
        connmail.close()
        sys.exit()
    id=uri[index:]
    partone=uri[:index]
    if id[1]!="i":
        print "abnormal activate uri, correct it."
        index=id.find("id")
        if index==-1:
            print "no id string, exit."
            connhtc.close()
            connmail.close()
            sys.exit()
        id=id[index:]
        id="&"+id
        uri=partone+id
    for i in xrange(1, 3):
        if uri[-1]=="\n":
            uri=uri[:-1]
        elif uri[-1]=="\r":
            uri=uri[:-1]
    #
    # 激活该注册账户,激活时使用的uri格式为：/?ACT=x&id=xxxxxxxxxx
    #
    connhtc.request("GET", uri)
    rsphtc=connhtc.getresponse()
    print rsphtc.status, rsphtc.reason
    data=rsphtc.read()
    #
    # 使用该账户登陆到htcdev
    #
    uri="/"
    body='ACT=9&RET=-2&site_id=1&username='+user
    body=body+'&password='
    body=body+password
    connhtc.request("POST", uri, body, header)
    rsphtc=connhtc.getresponse()
    print rsphtc.status, rsphtc.reason
    loginheader=rsphtc.getheaders()
    # 取回htcdev返回的登陆响应中的cookie
    cookie=rsphtc.getheader('set-cookie')
    # 从cookie中解析出如下四个字段，并重新构建新的cookie
    exp_last_visit=extract_cookie(cookie, "exp_last_visit")
    if exp_last_visit==" ":
        print "exp_last_visit not in cookie!"
        connhtc.close()
        connmail.close()
        sys.exit()
    exp_last_activity=extract_cookie(cookie, "exp_last_activity")
    if exp_last_activity==" ":
        print "exp_last_activity not in cookie!"
        connhtc.close()
        connmail.close()
        sys.exit()
    exp_expiration=extract_cookie(cookie, "exp_expiration")
    if exp_expiration==" ":
        print "exp_expiration not in cookie!"
        connhtc.close()
        connmail.close()
        sys.exit()
    exp_sessionid=extract_cookie(cookie, "exp_sessionid")
    if exp_sessionid==" ":
        print "exp_sessionid not in cookie!"
        connhtc.close()
        connmail.close()
        sys.exit()
    cookie=exp_last_visit+"; "
    cookie=cookie+exp_last_activity
    cookie=cookie+"; "
    cookie=cookie+exp_expiration
    cookie=cookie+"; "
    cookie=cookie+exp_sessionid
    data=rsphtc.read()

    #
    # 从手机中获取token字符串。因为无法将该命令的输出重定向，暂时注释掉该段代码
    #
    #cmd=r"c:/htcunlock/fastboot oem get_identifier_token"
    #p=subprocess.Popen(cmd, stdout=subprocess.PIPE)
    #token=p.communicate()[0]   
    #
    # 向htcdev上传token。token是由命令fastboot oem get_identifier_token从手机中取回的字符串，这里先将token字符串写死, 所以需要根据获取的token重新赋值。
    # hard coded for my test mobile， replace the token retrieved using above method for your HTC mobile.
    uri="/bootloader/process-unlock-key"
    body="bootloader_text=<<<< Identifier Token Start >>>>\r\n\
8631A3F8908386AAFB361EF47C119049\r\n\
5CB4DB276134E0F15CCBF95044525A56\r\n\
D0C897FDF05A1E8FDA88884CC56C2D0F\r\n\
7E0DF97A7EE3303CA64B8F2909986445\r\n\
C004478DAD9A7BE19339C719AC086D1C\r\n\
9C6A4C185BB5AC9849E1E1A004B86903\r\n\
4E44EC1A1B3B2417B7C3A2D2E2F94404\r\n\
53EE95D813875E182D28AAA91A346F70\r\n\
406D2E0A9F0354362D94360B7AD5DE61\r\n\
913F6E97D3A4C370B568ED00CFF3B251\r\n\
B29554EDE62D6390432282135941F7D7\r\n\
CEC534D88F6904B8929DD25449CEDE5B\r\n\
D84AD58AB3E2B9C7895EFA0B0F5D7D47\r\n\
4037D9E4513F8453D34C298F52CC0679\r\n\
CF7CE2DAF5F1487FF34E35CFCCDCF59D\r\n\
5AC15861FE919663CCA01C9FB289EC65\r\n\
<<<<< Identifier Token End >>>>>&Submit=Submit"
    header={"Content-type":"application/x-www-form-urlencoded", "Accept":"text/plain", 'Cookie':cookie}
    connhtc.request("POST", uri, body, header)
    try:
        rsphtc=connhtc.getresponse()
    except:
        print "post token error."
    print rsphtc.status, rsphtc.reason
    data=rsphtc.read()
    #
    # htcdev会向mailcatch发送邮件，其中包含token上传的确认签名。从mailcatch中取回该签名
    #
    show=""
    found=0
    mailcatch="mailcatch.com"
    uri="/en/temporary-inbox?box="+user
    # 确认签名是映射中键first_mail_id对应的值，轮询mailcatch服务，直到找到签名为止
    for i in xrange(1,20):
        show=""
        index=0
        found=0
        f=open(r"c:/htcunlock/mymailcatchtmp", "w+")
        connmail.request("GET", uri)
        rspmail=connmail.getresponse()
        print rspmail.status, rspmail.reason
        data=rspmail.read()
        f.write(data)
        f.seek(0)
        while True:
            line=f.readline()
            index=index+1
            if len(line)==0:
                print "reach EOF, mail index:%d, line counts:%d" %(i, index)
                break
            if "first_mail_id" in line:
                v=line.find("value")
                if v==-1:
                    continue
                line=line[v:]
                low=line.find("'")
                high=line.rfind("'")
                if low==-1:
                    continue
                length=high-low
                low=low+1
                # length:36
                if length >= 30:
                    show=line[low:high]
                    if show!=sign:
                        found=1
                        break
        if found==1:
            f.close()
            break
        f.close()
        # XXX: sleep 20s
        time.sleep(20)
    if found==0:
        print "not found post token ack signature,exit."
        connhtc.close()
        connmail.close()
        sys.exit()
    #
    # htcdev会向mailcatch发送邮件，附件中包含解锁用到的bin文件，从mailcatch取回该bin文件
    # 取回mailcatch附件文件内容时，使用的uri字段为show_source
    #
    show="&show_source="+show
    uri="/en/temporary-mail-content?box="+user
    uri=uri+show
    # 包含附件bin文件的邮件中包含特征字符串filename=Unlock_code.bin， 轮询mailcatch服务直到找到该邮件
    found=0  
    for i in xrange(1,4):
        found=1
        connmail.request("GET", uri)
        rspmail=connmail.getresponse()
        print rspmail.status, rspmail.reason
        data=rspmail.read()
        boundary="boundary="
        index=data.find(boundary)
        if index==-1:
            print "no boundary in mail index:", i
            continue
        boundary=data[index:]
        index=boundary.find("\"")
        if index==-1:
            print "boundary error format."
            continue
        index=index+1
        boundary=boundary[index:]
        index=boundary.find("\"")
        if index==-1:
            print "no end for boundary"
            continue
        boundary=boundary[:index]
        string="filename=Unlock_code.bin"
        index=data.find(string)
        if index==-1:
            continue
        # OK, 该邮件附件是bin文件，取得bin文件内容。
        # bin文件内容是位于字符串filename=Unlock_code.bin和变量boundary代表的字符串中间的一段被加密过的字符串
        # bin文件内容不包含空格和回车换行字符
        index=index+len(string)
        bin=data[index:]
        index=bin.find(boundary)
        if index==-1:
            print "no end for bin!"
            connhtc.close()
            connmail.close()
            sys.exit()
        #在boundary的结束字符串前面，还有两个‘-’字符，删除之
        if index<=2:
            print "invalid bin file."
            connhtc.close()
            connmail.close()
            sys.exit()
        index=index-2
        bin=bin[:index]
        bin.strip()
        while True:
            if bin[0]=="\r":
                bin=bin[1:]
            elif bin[0]=="\n":
                bin=bin[1:]
            else:
                break
        while True:
            if bin[-1]=="\r":
                bin=bin[:-1]
            elif bin[-1]=="\n":
                bin=bin[:-1]
            else:
                break
        found=1
        break
    if found==0:
        print "not found bin file!"
        connhtc.close()
        connmail.close()
        sys.exit()
    #
    # 将bin文件内容使用base64解码，并写到本地文件Unlock_code.bin中
    #
    f=open(r"c:/htcunlock/Unlock_code.bin", "w+")
    data = base64.b64decode(bin)
    f.write(data)
    f.close()    
    #
    # 关闭同htcdev和mailcatch服务器的连接
    #
    connhtc.close()
    connmail.close()
    #
    # 解锁htc手机，手机上会弹出英文对话框让用户确认，选择yes表示同意解锁手机，选择no表示不同意解锁手机
    #
    cmd=r"c:/htcunlock/fastboot flash unlocktoken Unlock_code.bin"
    subprocess.call(cmd)
    print "the end"
    
    
                    
    
