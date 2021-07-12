from __future__ import print_function
try:
    from builtins import bytes
except ImportError as e:
    print(e)
    print("Hata: Scripti çalıştırmak için gereken 'future' librarysi mevcut değil, yüklemek için: 'pip install future' komutunu tuşlayın.")
    exit()

import time
import sys

try:
    import requests
    from requests.packages.urllib3.exceptions import InsecureRequestWarning
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
except ImportError as e:
    print(e)
    print("Hata: Request yollamak için gereken 'request' librarysi mevcut değil, yüklemek için: 'pip install requests' komutunu tuşlayın.")
    exit(1)

if sys.version_info >= (3, 0):
    if sys.getdefaultencoding().lower() != 'utf-8' or sys.stdout.encoding.lower() != 'utf-8':
        print("UTF-8 sürümünde hata mevcut, script durduruluyor.")
        print("sys.getdefaultencoding(): "+sys.getdefaultencoding())
        print("sys.stdout.encoding: "+sys.stdout.encoding)
        print("export LC_CTYPE=utf-8")
        print("export PYTHONIOENCODING=utf-8")
        exit()

START = """GET / HTTP/1.1
Host: www.example.org
User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:63.0) Gecko/20100101 Firefox/63."""
END = """
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: de,en-US;q=0.7,en;q=0.3
Accept-Encoding: gzip, deflate
Connection: close
Upgrade-Insecure-Requests: 1
"""

TLS = False
DEBUG = True
TIMEOUT = 2
SEND_THROUGH_PROXY = False

def main():
    corpus = range(0, 2)
    send_with_requests(corpus)

def send_with_requests(corpus):
    for i in corpus:
        req = RawHttpRequest(START + str(i) + END, TLS)
        info(i, "Request gönderiliyor.")
        result(repr(send_requests(req)[:60])+ "...")
        result(repr(send_requests(req)))
        r = send_requests(req, entire_response=True)
        debug(r.request.headers)
        debug_sleep(15)

def send_requests(req, entire_response=False, allow_redirects=True):    
    proxy_dict = None
    if SEND_THROUGH_PROXY:
        http_proxy  = "http://127.0.0.1:8080"
        https_proxy = "https://127.0.0.1:8080"

        proxy_dict = { 
                      "http"  : http_proxy, 
                      "https" : https_proxy, 
                    }
    headers = dict(req.header_tuples)
    r = requests.request(req.method, req.url, data=req.body, headers=headers, proxies=proxy_dict, verify=False, timeout=TIMEOUT, allow_redirects=allow_redirects)
    if entire_response:
        return r
    else:
        return r.text

class RawRequest(object):
    def __init__(self, raw, tls, host=None, port=None, newline="\n"):
        self.raw = raw
        self.tls = tls
        self.host = host
        self.port = port
        self.newline = newline
        

class RawHttpRequest(RawRequest):
    REMOVE_HEADERS=[
        'content-length', 
        'accept-encoding',
        'accept-charset', 
        'accept-language', 
        'accept', 
        'keep-alive', 
        'connection', 
        'pragma', 
        'cache-control'
    ]
    
    def __init__(self, raw, tls, host=None, port=None, remove_headers=None, newline="\n"):
        super(RawHttpRequest, self).__init__(raw, tls, host, port, newline)
        self.method = "GET"
        self.url = "/"
        self.header_tuples = ""
        self.body = ""
        
        self.parse(remove_headers)
        debug(str(self))
    
    def __str__(self):
        r = """Host: {}
Port: {}
TLS: {}
Newline: {}
Method: {}
URL: {}
Headers: {}
Body: {}
Raw:
{}
""".format(self.host, self.port, self.tls, repr(self.newline), self.method, self.url, dict(self.header_tuples), repr(self.body), self.raw)
        return r
    
    def parse(self, remove_headers):
        if remove_headers is None:
            remove_headers = RawHttpRequest.REMOVE_HEADERS
        remove_headers = [x.lower() for x in remove_headers]
        
        double_newline = self.newline * 2
        if double_newline in self.raw:
            headers, self.body = self.raw.split(double_newline, 1)
            if not self.body:
                self.body = None
        else:
            debug("Uyarı: Request 'body' içermiyor.")
            headers = self.raw
            self.body = None
        headers = headers.split(self.newline)
        request_line = headers[0]
        headers = headers[1:]
        
        method, rest = request_line.split(" ", 1)
        self.method = method.upper()
        url, self.protocol = rest.rsplit(" ", 1)
    
        if not url.startswith("/"):
            raise Exception("URL must start with /")
        
        if self.tls is None:
            debug("Uyarı: Normal ayar Non-TLS HTTP requeste ayarlandı.")
            self.tls = False
        
        extract_from_host_header = not self.host and not self.port
        
        header_tuples = []
        for header in headers:
            name, value = header.split(": ", 1)
            if extract_from_host_header and name.lower() == 'host':
                if ":" in value:
                    host, port = value.split(":", 1)
                    self.host = host
                    self.port = int(port)
                else:
                    self.host = value
                    if self.tls:
                        self.port = 443
                    else:
                        self.port = 80
                                
            if not name.lower() in remove_headers:
                header_tuples.append((name, value))
                debug("Added header:", name)
        self.header_tuples = header_tuples
        self.create_url(url)
    
    def create_url(self, path):
        prot = "https://" if self.tls else "http://"
        if self.port == 443 and self.tls:
            self.url = prot + self.host + path
        elif self.port == 80 and not self.tls: 
            self.url = prot + self.host + path
        else:
            self.url = prot + self.host + ":" + str(self.port) + path

def warning(*text):
    print("[Uyarı] "+str(" ".join(str(i) for i in text)))

def error(*text):
    print("[Hata] "+str(" ".join(str(i) for i in text)))

def fatalError(*text):
    print("[Büyük Hata] "+str(" ".join(str(i) for i in text)))
    exit()

def result(*text):
    print("[Sonuç] "+str(" ".join(str(i) for i in text)))

def info(*text):
    print("[Bilgi] "+str(" ".join(str(i) for i in text)))

def debug(*text):
    if DEBUG:
        print("[Debug] "+str(" ".join(str(i) for i in text)))

def debug_sleep(time):
    if DEBUG:
        time.sleep(time)

if __name__ == "__main__":
    main()