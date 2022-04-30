import bs4
import datetime
import time
import re
import requests
import requests.cookies
from browser import Browser

class Processor:
    def __init__(self, cookies: list[dict]) -> None:
        self.ptaskc = re.compile("全(\d*?)件") # 中\d*?〜\d*?件
        self.cookies = cookies
        self.session = requests.session()
        for cookie in self.cookies:
            #print(cookie)
            #for item in cookie:
            #    #print(item)
            #    if type(cookie[item]) != str:
            #        s = str(cookie[item]).lower() if type(cookie[item]) == bool else str(cookie[item])
            #        cookie[item] = "".join(s[1:]) if s.startswith(".") else s
            #    self.session.cookies.update(requests.cookies.cookiejar_from_dict(cookie))  #shit
            self.session.cookies.set(cookie["name"], cookie["value"]) #god
        print(self.session.cookies.get_dict())

    def do_all(self):
        challenge_deliveries = self.get_challenge_deliveries()
        learning_map_homeworks = self.get_learning_map_homeworks()
        webtests = self.get_webtests()
        json = __import__("json")
        def json_serial(obj):
            if isinstance(obj, (datetime.datetime, datetime.date)):
                return obj.isoformat()
            raise TypeError ("Type %s not serializable" % type(obj))
        print(json.dumps(challenge_deliveries, indent="  ", default=json_serial))
        print(json.dumps(learning_map_homeworks, indent="  ", default=json_serial))
        print(json.dumps(webtests, indent="  ", default=json_serial))

    def parse_date(self, datestr: str) -> datetime.datetime:
        datestr = " ".join(datestr.split(" ")[-2:])
        return datetime.datetime.strptime(datestr, "%Y/%m/%d %H:%M")

    def get_challenge_deliveries(self) -> dict:
        res = self.session.get("https://video.classi.jp/student/challenge_delivery_history/challenge_delivery_history_school_in_studying")
        soup = bs4.BeautifulSoup(res.text, "lxml")
        open("cd.html", "w", encoding="utf-8").write(res.text)
        etaskc = soup.select_one("#container > div > div.list-pageinfo")
        etasks = soup.select_one("#container > div > div.task-list")
        return {
            "count": int(self.ptaskc.match(etaskc.text).group(1)),
            "tasks": self.parse_challenge_delivery(etasks, "https://video.classi.jp")
        }

    def parse_challenge_delivery(self, etasks: bs4.Tag, domain: str = "") -> list:
        result = []
        for etask in etasks.children:
            result.append({
                "title": etask.select_one("dl > dd > p.subject").text,
                "description": etask.select_one("dl > dt").text,
                "expires_at": self.parse_date(etask.select_one("dl > dd > p:nth-child(2) > span").text),
                "progress": int(etask.select_one("div.right-block > div").get("data-percent")),
                "url": domain + etask.get("href") if etask.get("href").startswith("/") else etask.get("href")
            })
        return result

    def get_learning_map_homeworks(self) -> list:
        #res = self.session.get("https://video.classi.jp/v/student/learning_map_homework?filter=incomplete")
        #soup = bs4.BeautifulSoup(res.text, "lxml")
        #open("lmh.html", "w", encoding="utf-8").write(res.text)
        #etaskc = soup.select_one("body > video-root > spen-single-column > div > main > video-learning-map-homework-list > div.meta-info-area > div")
        #etasks = soup.select_one("body > video-root > spen-single-column > div > main > video-learning-map-homework-list > nav")
        #return {
        #    "count": int(self.ptaskc.match(etaskc.text).group(1)),
        #    "tasks": self.parse_learning_map_homework(etasks)
        #}
        res = self.session.get("https://video.classi.jp/api/video/student/learning_map_homeworks") #i love you api
        print(res.text)
        j = res.json()
        return {
            "count": len(j),
            "tasks": [{
                "title": task["title"],
                "description": task["teacherName"],
                "expires_at": datetime.datetime.strptime(task["deadline"], "%Y-%m-%dT%H:%M:%SZ"),
                "url": "https://video.classi.jp/v/student/learning_map_homework/" + str(task["videoHomeworkId"]),
            } for task in j]
        }
    
    #def parse_learning_map_homework(self, etasks: bs4.Tag, domain: str = ""):
    #    result = []
    #    for etask in etasks.children:
    #        result.append({
    #            "title": etask.select_one("video-homework-list-item > div.info > div.title").text,
    #            "description": etask.select_one("video-homework-list-item > div.info > div.teacher-name").text,
    #            "expires_at": self.parse_date(etask.select_one("video-homework-list-item > div.info > div.date-time").text),
    #            "url": domain + etask.get("href") if etask.get("href").startswith("/") else etask.get("href")
    #        })
    #    return result

    def get_webtests(self) -> list: #todo get all tests
        res = self.session.get("https://platform.classi.jp/api/v2/webtest/examinations?page=1")
        print(res.text)
        j = res.json()
        return {
            "count": j["total"],
            "page": j["page"],
            "tasks": [{
                "title": task["webtest"]["name"],
                "description": task["group"]["name"] + " - " + task["distributor"]["name"],
                "expires_at": datetime.datetime.strptime(task["deadline_at"], "%Y-%m-%d %H:%M:%S"),
                "started_at": datetime.datetime.strptime(task["distribution_at"], "%Y-%m-%d %H:%M:%S"),
                "url": "https://platform.classi.jp/webtest/#/exam/detail/" + str(task["id"])
            } for task in j["distributions"]]
        }

if __name__ == "__main__":
    browser = Browser(input("email: "), input("password: "))
    browser.main()
    time.sleep(5)
    #browser.walk()
    #browser.driver.minimize_window()
    cookies = browser.driver.get_cookies()
    #browser.driver.close()
    print(len(cookies), cookies)
    processor = Processor(cookies)
    #print(processor.get_challenge_deliveries())
    processor.do_all()
    input("?")