from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

class Browser:
    def __init__(self, email: str, password: str) -> None:
        options = Options()
        #options.add_argument("--headless")
        #options.add_argument("--proxy-server=127.0.0.1:8888")
        self.driver = webdriver.Chrome(chrome_options=options, service=Service(ChromeDriverManager().install()))
        self.wait = WebDriverWait(driver=self.driver, timeout=30)
        #self.driver.implicitly_wait(10) #time.sleep is god
        self.email = email
        self.password = password

    def main(self):
        self.open()
        self.login()
    
    def open(self):
        self.driver.get("https://id.classi.jp/login/identifier")
        self.wait.until(EC.presence_of_all_elements_located)
        time.sleep(1)

    def login(self):
        #e = self.driver.find_element_by_xpath("//span[text()='Googleのアカウント']")
        e = self.driver.find_element_by_xpath("/html/body/app-root/app-login-identifier/main/section/div[3]/app-login-sso/button[1]")
        e.click()
        self.wait.until(EC.presence_of_all_elements_located)
        time.sleep(3)
        #e = self.driver.find_element_by_xpath("//div[matches(text(), \"^s\\d{5}@setouchi-h\\.ed\\.jp\")]")
        #e.click()
        e = self.driver.find_element_by_xpath("/html/body/div[1]/div[1]/div[2]/div/div[2]/div/div/div[2]/div/div[1]/div/form/span/section/div/div/div[1]/div/div[1]/div/div[1]/input")
        e.send_keys(self.email)
        e = self.driver.find_element_by_xpath("/html/body/div[1]/div[1]/div[2]/div/div[2]/div/div/div[2]/div/div[2]/div/div[1]/div/div/button/span")
        e.click()
        time.sleep(2)
        e = self.driver.find_element_by_xpath("/html/body/div[1]/div[1]/div[2]/div/div[2]/div/div/div[2]/div/div[1]/div/form/span/section/div/div/div[1]/div[1]/div/div/div/div/div[1]/div/div[1]/input")
        e.send_keys(self.password)
        e = self.driver.find_element_by_xpath("/html/body/div[1]/div[1]/div[2]/div/div[2]/div/div/div[2]/div/div[2]/div/div[1]/div/div/button/span")
        e.click()
        self.wait.until(EC.url_to_be("https://platform.classi.jp/"))
        print("Logged in.")

    def walk(self):
        time.sleep(2)
        urls = []
        i = 0
        while True:
            try:
                a = self.driver.find_element_by_xpath(f"/html/body/div[1]/div/article/div/section[2]/ul/li[{i+1}]/a")
                urls.append(a.get_attribute("href"))
                print(type(a.get_attribute("href")), a.get_attribute("href"))
                i+=1
            except Exception as e:
                print(e)
                break
        for url in urls:
            self.driver.get(url)
            self.wait.until(EC.visibility_of_all_elements_located)
            time.sleep(3)