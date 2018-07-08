import requests
from bs4 import BeautifulSoup
from collections import defaultdict

session = requests.Session()
jiaowu_url = 'http://10.200.21.61:7001/ieas2.1/'
# use '/login' instead of '/login/' to avoid redirects
login_url = 'https://sso.buaa.edu.cn/login'

def get_login_token() -> str:
    r = session.get(login_url)
    assert(r.status_code == 200)
    soup = BeautifulSoup(r.content, 'html.parser')
    lt = soup.find('input', {'name': 'lt'})['value']
    return lt

def login(username: str, password: str) -> bool:
    formdata = {
        'username': username,
        'password': password,
        'code': '',
        'lt': get_login_token(),
        'execution': 'e1s1',
        '_eventId': 'submit',
        'submit': '登陆'
    }
    r2 = session.post(login_url, data=formdata, allow_redirects=False)
    assert(r2.status_code == 200)
    return 'Set-Cookie' in r2.headers

def assess_item(teacher: "beautifulSoup object"):
    print('judging teacher %s...' % teacher.string)
    course_id = list(teacher.parents)[2]['rwh_id']
    teacher_info = teacher['onclick'].split("'")   
    teacher_id = teacher_info[1]
    pjcs = teacher_info[3]
    form_data = {
        'rwh': course_id,
        'zgh': teacher_id,
        'pjcs': pjcs,
        'kcdm': '',
        'pageXnxq': ''
    }
    r = session.post("http://10.200.21.61:7001/ieas2.1/xspj/toAddPjjs", 
                     data=form_data)
    if r.status_code != 200:
        print('failed! Details:', r.status_code, teacher_id, course_id, pjcs)
        return
    s = BeautifulSoup(r.content, "html.parser")
    form = s.find('form', id='queryform')
    entries = form.find_all('input', type='hidden')
    form_data2 = defaultdict(list)
    for entry in entries:
        if not entry.has_attr('name'):
            continue
        form_data2[entry['name']].append(entry['value'])
    entries = form.find_all('input', id='zbdm')
    for i, entry in enumerate(entries):
        # option = entry.td.input
        option = entry.find_next_sibling('td').input
        if i == 0:
            option = option.find_next_sibling('input')
        form_data2[option['name']].append(option['value'])
    r2 = session.post('http://10.200.21.61:7001/ieas2.1/xspj/saveXspj',
                      data=form_data2)
    if r2.status_code != 200:
        print('failed! Details:', r2.status_code, form_data2)
        return
    print('success!')

def auto_evaluation():
    res = session.get("http://10.200.21.61:7001/ieas2.1/xspj/Fxpj_fy", 
                       allow_redirects=False)
    if res.status_code != 200:
        print("can't load page")
        exit()
    soup = BeautifulSoup(res.content, 'html.parser')
    yellow_spans = soup.find_all('span', class_='yellow')
    teachers = []
    for span in yellow_spans:
        teachers += span.find_all('a')   
    for teacher in teachers:
        assess_item(teacher)

def auto_judge():
	username = input('请输入统一认证登陆账号：')
	password = input('请输入统一认证登陆密码：')
	if login(username, password) == True:
		auto_evaluation()
	else:
		print("账号或者密码错误(请确保连入校园网)")
	
auto_judge()
