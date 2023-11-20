'''
自动合并发布分支
创建TAG
转成exe文件 "pyinstaller -F auto_merge_git_branch.py"
'''
# coding = utf-8
import os
import time
import json
import subprocess
import sys
from urllib import request
from urllib import parse
from http import cookiejar
from common import logger
import configparser

BRANCH_URL = ("http://stash.igrow.cn/rest/api/latest/projects/{projectkey}/"
              "repos/{repos}/branches")

def main():
    """自动合并发布分支，创建分支标记。"""
    global log
    log = logger.Logger().getlog()
    # 获取stash配置
    stash_config = get_stash_config()
    isexit = "t"
    while isexit == "t":
        # 选择哪种操作
        process = input("请选择哪种处理（1--合并发布分支，2--创建tag）：")

        if process not in ("1", "2"):
            process = input("请选择（1--合并发布分支，2--创建tag）：")

        if process not in ("1", "2"):
            log.error("抱歉您的选择不在选项中，无法处理，谢谢。")
            return

        # 判断能否启动git
        cnt = call("git --version")
        if cnt.returncode != 0:
            log.error("此电脑不能运行git，请安装git，并加入坏境变量path中。")
            return

        # 项目路径
        projectpath = input("请输入项目路径（例：F:/git-source/team/api）:")

        if os.path.exists(projectpath):
            # 跳转到目录下
            os.chdir(projectpath)
            path = os.getcwd()
            loginfo = "已经跳转到目录: %s" % (path)
            log.info(loginfo)

        # 项目名
        projectname = input("请输入项目名（例：school.igrow.cn）:")

        # 发布分支
        releasebranch = input("请输入发布分支:")        

        if process == "1":
            merge_branch(projectname, releasebranch, stash_config)
            loginfo = ">>>>>项目（%s）合并分支处理完毕。" % (projectname)
            log.info(loginfo)
        elif process == "2":
            version = input("请输入项目版本:")
            create_tag(projectname, releasebranch, version)
            loginfo = ">>>>>项目（%s）创建tag处理完毕。" % (projectname)
            log.info(loginfo)

        isexit = input("您要继续处理其他项目吗？（t--继续，q--退出）:")

def get_stash_config():
    """
    从ini文件获取stash配置
    """
    config = configparser.ConfigParser()
    ini_path = os.path.dirname(os.getcwd()) + '\\config\\jira_stash_config.ini'
    if not os.path.exists(ini_path):
        log.error("获取stash配置失败，ini文件路径：%s" % ini_path)
        return

    try:
        config.read(ini_path, encoding='utf-8')
        log.info("ini配置：%s" % config.sections())
        return config
    except IOError as ex:
        log.error("获取stash配置失败")
        return

def get_branches(projectkey, repos, stash_config):
    """
    从stash中获取需要处理的分支
    """
    loginfo = "get_branches(%s, %s)" % (projectkey, repos)
    log.info(loginfo)

    stash_login_user = stash_config.get('stash_account', 'stash_login_user')
    stash_pass_word = stash_config.get('stash_account', 'stash_pass_word')

    # 登录stash获取cookie
    url = "http://stash.igrow.cn/j_stash_security_check"

    postdata = parse.urlencode({
        "j_username": stash_login_user,
        "j_password": stash_pass_word,
        "submit": "Log in"
        }).encode('utf-8')

    header = {
        "Accept": ("text/html,application/xhtml+xml,application/xml;"
                   "q=0.9,image/webp,image/apng,*/*;q=0.8"),
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
        "User-Agent": ("Mozilla/5.0 (Windows NT 6.1; WOW64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/66.0.3359.139 Safari/537.36")
        }

    # 声明一个CookieJar对象实例来保存cookie
    cookie = cookiejar.CookieJar()
    # 利用urllib.request库的HTTPCookieProcessor对象来创建cookie处理器,也就CookieHandler
    handler = request.HTTPCookieProcessor(cookie)
    # 通过CookieHandler创建opener
    opener = request.build_opener(handler)

    htmlrequest = request.Request(url=url,
                                  data=postdata,
                                  headers=header,
                                  method="POST")
    response = opener.open(htmlrequest)

    # 获取cookie:JSESSIONID
    jsessionid = ""
    for item in cookie:
        if item.name == "JSESSIONID":
            jsessionid = "JSESSIONID=" + item.value

    time.sleep(1)
    branch = []
    if jsessionid != "":
        # 获取访问url
        url = BRANCH_URL.format(projectkey=projectkey, repos=repos)
        headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Accept-Encoding": "utf-8",
            "Cache-Control": "no-cache",
            "User-Agent": ("Mozilla/5.0 (Windows NT 6.1; WOW64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/66.0.3359.139 Safari/537.36"),
            "Host": "stash.igrow.cn",
            "Content-Type": "application/json",
            "Referer": "http://stash.igrow.cn/projects/WMOB/repos/m/branches",
            "Cookie": jsessionid,
            "Connection": "keep-alive"
            }
        data = parse.urlencode({
            "start": "0",
            "limit": "20",
            "orderBy": "MODIFICATION"
        }).encode('utf-8')

        htmlrequest = request.Request(
            url=url,
            data=data,
            headers=headers,
            method="GET")
        response = opener.open(htmlrequest)
        html = response.read().decode()
        # 获取需要处理的分支
        if html != "":
            jsonstr = json.loads(html)
            for value in jsonstr['values']:
                branch.append(value['displayId'])
    return branch

def merge_branch(projectname, releasebranch, stash_config):
    """
    合并发布分支
    """
    loginfo = "merge_branch(%s, %s)" % (projectname, releasebranch)
    log.info(loginfo)

    dictProjectKey = json.loads(stash_config.get('stash_project', 'project_key'))
    dictRepos = json.loads(stash_config.get('stash_project', 'repos'))

    # 获取项目对应的项目key和仓库名
    if projectname in dictProjectKey.keys():
        projectkey = dictProjectKey[projectname]
        repos = dictRepos[projectname]
    else:
        loginfo = "抱歉您输入的项目不在范围内：" + repr(dictProjectKey.keys())
        log.error(loginfo)
        return

    # 获取需要合并的分支
    branches = get_branches(projectkey, repos, stash_config)
    if not branches:
        log.error("抱歉没有您需要合并的分支。")
        return

    # 排除release分支，不需要合并
    for i in branches:
        if i[0:8] == "release_":
            branches.remove(i)
    log.info(branches)

    # 合并分支
    for branch in branches:
        loginfo = ">>>>>开始合并发布分支[" + releasebranch + "]到分支[" + branch + "]."
        log.info(loginfo)

        # 切换到需合并的分支
        call('git checkout %s' % (branch))
        time.sleep(1)

        # 查看当前分支
        call('git branch')
        time.sleep(1)

        # 拉取最新代码
        call('git fetch origin')
        call('git merge origin/%s' % (branch))

        execute = ("git merge origin/%s --no-ff -m "
                   "\"git merge origin/%s to %s.\"") % (
                       releasebranch, releasebranch, branch)
        cnt = call(execute)
        # 判断是否有合并冲突，若有冲突，则退出
        if cnt.returncode == 0 and "conflict" in repr(cnt.stdout):
            log.error("自动合并存在冲突，请解决冲突后再提交代码！！")
            return
        time.sleep(1)

        execute = ("git merge origin/%s --no-ff -m "
                   "\"git merge origin/%s to %s.\"") % (
                       releasebranch, releasebranch, branch)
        cnt = call(execute)
        # 判断是否合并成功，合并成功则推送到远程分支
        if cnt.returncode == 0 and "Already up to date" in repr(cnt.stdout):
            time.sleep(1)
            call('git push origin %s' % (branch))

        loginfo = ">>>>>结束合并发布分支[" + releasebranch + "]到分支[" + branch + "]."
        log.info(loginfo)


def create_tag(projectname, releasebranch, version):
    """
    创建版本标记
    """
    loginfo = "create_tag(%s, %s, %s)" % (projectname, releasebranch, version)
    log.info(loginfo)

    # 创建发布分支的tag，推送到远程
    log.info(">>>>>开始创建tag")

    call('git checkout %s' % (releasebranch))
    time.sleep(1)

    call('git branch')
    time.sleep(1)

    call('git fetch origin')
    call('git merge origin/%s' % (releasebranch))
    time.sleep(1)

    cnt = call("git merge origin/%s" % (releasebranch))
    # 发布分支已经是最新代码时，打上标记创建tag，合并到远程分支
    if cnt.returncode == 0 and "Already up to date" in repr(cnt.stdout):
        time.sleep(1)
        tagname = "v" + releasebranch[8:len(releasebranch)]

        call("git tag -a %s -m \"%s\"" % (tagname, version))
        time.sleep(1)

        call('git push origin %s' % (tagname))

    log.info(">>>>>结束创建tag")


def call(command):
    """
    执行shell命令
    """
    try:
        arrreturn = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE)
        loginfo = "======>%s" % (repr(arrreturn))
        log.info(loginfo)
    except OSError:
        loginfo = "\"%s\"处理发生错误，请查看问题（比如合并冲突）。" % command
        log.error(loginfo)
        sys.exit()
    return arrreturn


if __name__ == '__main__':
    main()
