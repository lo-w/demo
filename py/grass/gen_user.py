
import random
import requests
import unicodedata
from lxml import html 


RLIST            = [",", "-"]
USER_PASS        = ""

def get_xpath_ele(ele):
    if ele:
        val = ele[0]
        if "(" in val:
            val = val.split("(")[0]
        for c in RLIST:
            val = val.replace(c, "")
        return unicodedata.normalize('NFKD', val).strip()
    return ""

def get_user():
    user = {}
    user_urls = [
        {"url_uuid":"96da9428960dfa2613826167c913a530","url":"https://www.shenfendaquan.com/"},
        {"url_uuid":"5122167f66a858e9872434bafaadd7f5","url":"https://www.fakepersongenerator.com/"}
    ]

    url = random.choice(user_urls)
    user_url = url.get("url")
    url_uuid = url.get("url_uuid")
    # user_url = "https://www.fakepersongenerator.com/"
    # url_uuid = "5122167f66a858e9872434bafaadd7f5"
    # user_url = "https://www.shenfendaquan.com/"
    # url_uuid = "96da9428960dfa2613826167c913a530"


    res=requests.get(user_url)

    user_xpath = html.etree.HTML(res.text)
    task_count = sql_info(task_count_sql, (url_uuid,))[0].get('c')

    for i in range(1, task_count + 1):
        task_step_list = sql_info(task_select_sql, (url_uuid, i))
        for task in task_step_list:
            findvalue = task.get('findvalue')
            mapto = task.get('mapto')
            k = mapto.split(".")[-1]
            if findvalue:
                v = get_xpath_ele(user_xpath.xpath(findvalue))
            else:
                if "mail" in mapto:
                    mlist = ["@gmail.com", "@outlook.com", "@hotmail.com", "@foxmail.com"]
                    v = user.get("name").replace(" ", ".").lower() + random.choice(mlist)
                else:
                    continue
            user[k] = v
    user['pass'] = USER_PASS
    return user


def main():
    print(get_user())


if __name__ == '__main__':
    main()