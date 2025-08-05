import atexit
import subprocess
import sys
import os, uuid
import time
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.core.http import HttpClient
import requests
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class CustomHttpClient(HttpClient):
    def get(self, url, params=None, **kwargs) -> requests.Response:
        return requests.get(
            url,
            params,
            proxies={
                "http": "http://12.26.204.100:8080",
                "https": "http://12.26.204.100:8080",
            },
            verify=False,
            **kwargs
        )

class EdgeDriver:
    URL = "http://edm2.sec.samsung.net/cc/link/verLink/174462396652404089/4"
    CSS_SELECTOR = "div.btns span.r a:nth-child(2)"
    
    def __init__(self, proxy_url="http://12.26.204.100:8080"):
        self.proxy_url = proxy_url
        # os.makedirs('d:/servers/', exist_ok=True)

        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(__file__)
        
        self.webdriver_path = resource_path('msedgedriver.exe')


        # self.webdriver_path = './drivers/msedgedriver.exe'
        


    def _setup_env(self):
        os.environ['NO_PROXY']="127.0.0.1,localhost,samsung.net,pfs.nprotect.com,dsvdi.net,samsungds.net,stsds.secsso.net"
        os.environ['PROXY']=self.proxy_url


    def run(self):
        self._setup_env()
        
        atexit.register(self.cleanup)
        #self.download_manager = WDMDownloadManager(CustomHttpCliendt())
        self.options = EdgeOptions()
        profile_path = os.path.join(os.environ['LOCALAPPDATA'], 'selenium_profiles', str(uuid.uuid4()))
        os.makedirs(profile_path, exist_ok=True)
        self.options.add_argument(f"--user-data-dir={profile_path}")
        # self.options.add_argument("--headless")
        self.service = EdgeService(executable_path=self.webdriver_path, verbose=True)
        self.driver = webdriver.Edge(service=self.service)
        self.driver_pid = self.service.process.pid
        try:
            self.driver.get(self.URL)
            element = WebDriverWait(self.driver, timeout=5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.CSS_SELECTOR))
            )
            
            assert "편집" == element.text
            element.click()
            print('EDM open success')
            time.sleep(8)

        finally:
            self.driver.quit()
            atexit.register(self.cleanup)

        

    def cleanup(self):
        try:
            subprocess.call(['taskkill', '/F', '/PID', str(self.driver_pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(e)
        

        

# 사용 예시
if __name__ == "__main__":
    
    edge_driver = EdgeDriver()
    edge_driver.run()
