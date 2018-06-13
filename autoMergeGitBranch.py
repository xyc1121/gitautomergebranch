'''
自动合并发布分支
创建TAG
'''
#! /usr/bin/python
# coding = utf-8
import os
import urllib
import time
import json
import subprocess
import sys
from urllib import request
from urllib import parse
from http import cookiejar

loginuser = "****"
password = "****"
branchurl = "http://stash.igrow.cn/rest/api/latest/projects/{projectkey}/repos/{repos}/branches"
dicts = {
			'school.igrow.cn': ('WSCH','school'),
			'm.igrow.cn': ('WMOB','m'), 
			'boss.igrow.cn': ('WBOS','boss'), 
			'baby.igrow.cn': ('WBOOK','book'), 
			'yzone.igrow.cn': ('WYZO','yzone'), 
			'assets.haoyuyuan.com': ('WASS','assets'), 
			'auth.haoyuyuan.com': ('WAUT','wauth'), 
			'api-yo.igrow.cn': ('WSCH','api-yo'), 
			'api.igrow.cn': ('WAPI','api'), 
			'api-crm.igrow.cn': ('APICRM','api-crm'),
			'api': ('WAPI','api'), 
			'yzone': ('WYZO','yzone'), 
			'm': ('WMOB','m'),
			'school': ('WSCH','school'),
			'auth': ('WAUT','wauth'), 
			'boss': ('WBOS','boss'), 
			'baby': ('WBOOK','book'), 
			'api-crm': ('APICRM','api-crm'),
			'api-yo': ('WSCH','api-yo'), 
		}

def main():
	isexit = "t"
	while isexit == "t":
		# 选择哪种操作
		process = input("请选择哪种处理（1--合并发布分支，2--创建tag）：")

		if process != "1" and process != "2":
			process = input("请选择（1--合并发布分支，2--创建tag）：")

		if process != "1" and process != "2":
			print("抱歉您的选择不在选项中，无法处理，谢谢。")
			return

		# 判断能否启动git
		cnt = call("git --version")
		if cnt.returncode != 0:
			print("此电脑不能运行git，请安装git，并加入坏境变量path中。")
			return

		# 项目路径
		projectpath = input("请输入项目路径（例：F:/git-source/team/api）:")

		if os.path.exists(projectpath):
			# 跳转到目录下
			os.chdir(projectpath)
			path = os.getcwd()
			print("已经跳转到目录:%s" % (path))

		# 项目名
		projectname = input("请输入项目名（例：school.igrow.cn）:")

		# 发布分支
		releasebranch = input("请输入发布分支:")

		if process == "1":
			mergebranch(projectname, releasebranch)
			print(">>>>>项目（%s）合并分支处理完毕。" % (projectname))
		elif process == "2":
			version = input("请输入项目版本:")
			createtag(projectname, releasebranch, version)
			print(">>>>>项目（%s）创建tag处理完毕。" % (projectname))

		isexit = input("您要继续处理其他项目吗？（t--继续，q--退出）:")

'''
从stash中获取需要处理的分支
''' 
def getbranches(projectkey, repos):
	print("getbranches(%s, %s)" % (projectkey, repos))

	# 登录stash获取cookie
	url = "http://stash.igrow.cn/j_stash_security_check"

	postdata=urllib.parse.urlencode({
		"j_username":loginuser,
		"j_password":password,
		"submit":"Log in"
	}).encode('utf-8')

	header={
		"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
		"Accept-Encoding": "utf-8",
		"Accept-Language": "zh-CN,zh;q=0.9",
		"Cache-Control": "no-cache",
		"Connection": "keep-alive",
		"Content-Length": "49",
		"Content-Type": "application/x-www-form-urlencoded",
		"Host": "stash.igrow.cn",
		"Origin": "http://stash.igrow.cn",
		"Pragma": "no-cache",
		"Referer": "http://stash.igrow.cn/login",
		"Upgrade-Insecure-Requests": "1",
		"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36"
	}
	
	#声明一个CookieJar对象实例来保存cookie
	cookie = cookiejar.CookieJar()
	#利用urllib.request库的HTTPCookieProcessor对象来创建cookie处理器,也就CookieHandler
	handler = urllib.request.HTTPCookieProcessor(cookie)
	#通过CookieHandler创建opener
	opener = urllib.request.build_opener(handler)

	request = urllib.request.Request(url = url, data = postdata, headers = header,method="POST")
	response = opener.open(request)
	
	# 获取cookie:JSESSIONID
	jsessionid = ""
	for item in cookie:
		if item.name == "JSESSIONID":
			jsessionid = "JSESSIONID=" + item.value

	time.sleep(1)
	branch = []
	if (jsessionid != ""):
		# 获取访问url
		url = branchurl.format(projectkey = projectkey, repos = repos)
		headers={
			"Accept":"application/json, text/javascript, */*; q=0.01",
			"Accept-Encoding":"utf-8",
			"Cache-Control":"no-cache",
			"User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36",
			"Host":"stash.igrow.cn",
			"Content-Type":"application/json",
			"Referer":"http://stash.igrow.cn/projects/WMOB/repos/m/branches",
			"Cookie":jsessionid,
			"Connection":"keep-alive"
		}
		data=urllib.parse.urlencode({
			"start":"0",
			"limit":"20",
			"orderBy":"MODIFICATION"
		}).encode('utf-8')
		
		request = urllib.request.Request(url = url,data = data,headers = headers,method="GET")
		response = opener.open(request)
		html = response.read().decode()
		# 获取需要处理的分支
		if html != "":
			jsonstr = json.loads(html)
			for value in jsonstr['values']:
				branch.append(value['displayId'])
	return branch

'''
合并发布分支
''' 
def mergebranch(projectname, releasebranch):
	print("mergebranch(%s, %s)" % (projectname, releasebranch))

	# 获取项目对应的项目key和仓库名
	if projectname in dicts.keys():
		dictrepos = dicts[projectname]
		projectkey = dictrepos[0]
		repos = dictrepos[1]
	else:
		print("抱歉您输入的项目不在范围内：" + dicts.keys())
		return

	# 获取需要合并的分支
	branches = getbranches(projectkey,repos)
	if len(branches) == 0:
		print("抱歉没有您需要合并的分支。")
		return

	# 排除release分支，不需要合并
	for i in branches:
		if i[0:8] == "release_":
			branches.remove(i)
	print(branches)

	# 合并分支
	for branch in branches:
		print(">>>>>开始合并发布分支[" + releasebranch + "]到分支[" + branch + "].")

		# 切换到需合并的分支
		call('git checkout %s' % (branch))
		time.sleep(1)

		# 查看当前分支
		call('git branch')
		time.sleep(1)

		# 拉取最新代码
		call('git fetch origin')
		call('git merge origin/%s' % (branch))

		cnt = call("git merge origin/%s --no-ff -m \"git merge origin/%s to %s.\"" % (releasebranch,releasebranch,branch))
		# 判断是否有合并冲突，若有冲突，则退出
		if cnt.returncode == 0 and "conflict" in repr(cnt.stdout):
			print("自动合并存在冲突，请解决冲突后再提交代码！！")
			return
		time.sleep(1)

		cnt = call("git merge origin/%s --no-ff -m \"git merge origin/%s to %s.\"" % (releasebranch,releasebranch,branch))
		# 判断是否合并成功，合并成功则推送到远程分支
		if cnt.returncode == 0 and "Already up-to-date" in repr(cnt.stdout):
			time.sleep(1)
			call('git push origin %s' % (branch))

		print(">>>>>结束合并发布分支[" + releasebranch + "]到分支[" + branch + "].")

def createtag(projectname, releasebranch, version):
	print("createtag(%s, %s, %s)" % (projectname, releasebranch, version))

	# 创建发布分支的tag，推送到远程
	print(">>>>>开始创建tag")

	call('git checkout %s' % (releasebranch))
	time.sleep(1)

	call('git branch')
	time.sleep(1)

	call('git fetch origin')
	call('git merge origin/%s' % (releasebranch))
	time.sleep(1)

	cnt = call("git merge origin/%s" % (releasebranch))
	# 发布分支已经是最新代码时，打上标记创建tag，合并到远程分支
	if cnt.returncode == 0 and "Already up-to-date" in repr(cnt.stdout):
		time.sleep(1)
		tagname = "v" + releasebranch[8:len(releasebranch)]
		
		call("git tag -a %s -m \"%s\"" % (tagname, version))
		time.sleep(1)

		call('git push origin %s' % (tagname))

	print(">>>>>结束创建tag")

def call(command):
	try:
		arrreturn = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE)
		print("======>%s" % (repr(arrreturn)))
	except Exception:
		print("\"%s\"处理发生错误，请查看问题（比如合并冲突）。" % command)
		sys.exit()
	return arrreturn

if __name__=='__main__':
	main()