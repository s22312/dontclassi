import bs4
import datetime
import time
import json
import re
import requests
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
        def json_serial(obj):
            if isinstance(obj, (datetime.datetime, datetime.date)):
                return obj.isoformat()
            raise TypeError ("Type %s not serializable" % type(obj))
        print(json.dumps(challenge_deliveries, indent="  ", default=json_serial))
        print(json.dumps(learning_map_homeworks, indent="  ", default=json_serial))
        print(json.dumps(webtests, indent="  ", default=json_serial))

        for challenge_delivery in challenge_deliveries["tasks"]:
            for video_lecture in self.get_video_lectures(challenge_delivery)["tasks"]:
                for video_content in self.get_video_contents(video_lecture)["tasks"]:
                    if video_content["type"] == "video":
                        info = self.get_video_content_video_info(video_content)
                        self.do_video_content_video(info)
                        print("solved:", video_content["title"])
                    else: #type should be "program"
                        print("couldn't solve the problem:", video_content["title"])
                        #self.do_video_content_program(video_content)

    def parse_date(self, datestr: str) -> datetime.datetime:
        datestr = " ".join(datestr.split(" ")[-2:])
        return datetime.datetime.strptime(datestr, "%Y/%m/%d %H:%M")

    def get_challenge_deliveries(self) -> dict: #challenge deliveries dont have api why
        res = self.session.get("https://video.classi.jp/student/challenge_delivery_history/challenge_delivery_history_school_in_studying")
        soup = bs4.BeautifulSoup(res.text, "lxml")
        open("cd.html", "w", encoding="utf-8").write(res.text)
        etaskc = soup.select_one("#container > div > div.list-pageinfo")
        etasks = soup.select_one("#container > div > div.task-list")
        return {
            "count": int(self.ptaskc.match(etaskc.text).group(1)),
            "tasks": [self.parse_challenge_delivery(etask, "https://video.classi.jp") for etask in etasks.children]
        }

    def parse_challenge_delivery(self, etask: bs4.Tag, domain: str = "") -> dict:
        return {
            "title": etask.select_one("dl > dd > p.subject").text,
            "description": etask.select_one("dl > dt").text,
            "expires_at": self.parse_date(etask.select_one("dl > dd > p:nth-child(2) > span").text),
            "progress": int(etask.select_one("div.right-block > div").get("data-percent")),
            "url": domain + etask.get("href") if etask.get("href").startswith("/") else etask.get("href")
        }

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
        print(res.status_code, res.text)
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
    
    #def parse_learning_map_homeworks(self, etasks: bs4.Tag, domain: str = ""):
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
        print(res.status_code, res.text)
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

    def get_video_lectures(self, task: dict) -> dict:
        #get video_cource
        url = task["url"].split("?")
        url[0]+="/start_challenge"
        res = self.session.get("?".join(url))
        soup = bs4.BeautifulSoup(res.text, "lxml")
        open("vl.html", "w", encoding="utf-8").write(res.text)
        etasks = soup.select_one("#container > div > section > div.lecture_list > div")
        return {
            "count": len(list(etasks.children)),
            "tasks": [self.parse_video_lecture(etask, "https://video.classi.jp") for etask in etasks.children]
        }

    def parse_video_lecture(self, etask: bs4.Tag, domain: str = "") -> dict:
        return {
            "title": etask.select_one("div > div.simple-task-name > p > span.lecture_name").text,
            "description": etask.select_one("div > div.simple-task-name > p > span.lecture_no").text,
            "url": domain + etask.get("href") if etask.get("href").startswith("/") else etask.get("href")
        }

    def get_video_contents(self, task: dict) -> dict:
        res = self.session.get(task["url"])
        soup = bs4.BeautifulSoup(res.text, "lxml")
        open("vc.html", "w", encoding="utf-8").write(res.text)
        etasks = soup.select_one("#container > div > section > ul.spen-mod-item-list.is-column-1.spen.spen-util-mb-24.lecture-flow")
        return {
            "count": len(list(etasks.children)),
            "tasks": [self.parse_video_content(etask, "https://video.classi.jp") for etask in etasks.children]
        }

    def parse_video_content(self, etask: bs4.Tag, domain: str = "") -> dict:
        return {
            "title": etask.select_one("a").text,
            #"description": etask.select_one("a").text,
            "type": "video" if etask.select_one("i").get("class", [None]) == ["fa", "fa", "fa-film"] else "program",
            "url": domain + etask.select_one("a").get("href") if etask.select_one("a").get("href").startswith("/") else etask.select_one("a").get("href")
        }

    def get_video_content_video_info(self, task: dict) -> dict:
        res = self.session.get(task["url"])
        soup = bs4.BeautifulSoup(res.text, "lxml")
        open("vci.html", "w", encoding="utf-8").write(res.text)
        keys = [
            "gon.study_status_id",
            "gon.content_id",
            "gon.lecture_id",
            "gon.cource_id",
            "gon.meta_id",
            "gon.media_id",
            "gon.logica_user_id",
            "gon.token"
        ]
        result = {
            "title": soup.select_one("#container > div > div > div > h1").text
        }
        for key in keys:
            _key = key.replace(".", "\.")
            value = re.search(f"{_key}=(.*?);", res.text)
            #print(key, value)
            result[key] = value.group(1) if value else ""
        return result

    def do_video_content_video(self, info: dict) -> bool:
        data = (
            "native_app_name="
            "&study_status_id="+info["gon.study_status_id"]+
            "&video_content_id="+info["gon.content_id"]+
            "&content_id="+info["gon.content_id"]+
            "&lecture_id="+info["gon.lecture_id"]+
            "&cource_id="+info["gon.cource_id"]+
            "&player_insert_flag=true"
            "&meta_id="+info["gon.meta_id"]+
            "&speed_list%5B1.0%5D="+info["gon.media_id"]+
            "&media_id="+info["gon.media_id"]+
            "&play_speed=1.0"
            "&logica_user_id="+info["gon.logica_user_id"]+
            "&token="+info["gon.token"]+
            "&current_time=0"
            "&is_from_top=false"
            "&ajax_flag=true"
            "&ajax_url=%2Fapi%2Fv1%2Fstudents%2Fvideo_complete"
            "&success=success"
            "&completed=false"
        )
        res = self.session.post(
            "https://video.classi.jp/api/v1/students/videos/start_study",
            headers={
                "content-type": "application/x-www-form-urlencoded;charset=UTF-8"
            },
            data=data
        )
        print(res.status_code, res.text)
        j = res.json()
        res = self.session.patch(
            "https://video.classi.jp/api/v1/students/video_complete",
            headers={
                "content-type": "application/x-www-form-urlencoded;charset=UTF-8"
            },
            data=data+(
                "&vssc_id="+str(j["vssc_id"])+
                "&study_type="+str(j["study_type"])
            )
        )
        print(res.status_code, res.text)
        return True

    def do_video_content_program(self, info: dict):
        res = self.session.get(info["url"])
        soup = bs4.BeautifulSoup(res.text, "lxml")
        open("vcp.html", "w", encoding="utf-8").write(res.text)
        if "type=\"checkbox\"" in res.text:
            raise NotImplementedError()
            choices = {}
            choicenames = {}
            for li in soup.select_one("#container > div > div > form > div.spen-ly-question > div > div > div.question-select > div > ul").children:
                i = li.select_one("#answer_data_sections__questions__user_answer_")
                c = li.select_one("div").text.strip()
                img = li.select_one("div > img")
                if len(img) > 0:
                    c = img.get("src")
                choices[i.get("value")] = c
                choices[i.get("value")] = i.get("name")
        elif "type=\"text\"" in res.text:
            raise NotImplementedError()
        elif "type=\"spen-mod-select\"" in res.text:
            raise NotImplementedError()
        elif "type=\"spen-mod-true-false-radio-box\"" in res.text:
            raise NotImplementedError()

if __name__ == "__main__":
    with open("config.json", "r", encoding="utf-8") as f:
        j = json.load(f)
    browser = Browser(j["email"], j["password"])
    browser.main()
    time.sleep(5)
    #browser.walk()
    #browser.driver.minimize_window()
    cookies = browser.driver.get_cookies()
    browser.driver.close()
    print(len(cookies), cookies)
    processor = Processor(cookies)
    #print(processor.get_challenge_deliveries())
    processor.do_all()
    input("?")