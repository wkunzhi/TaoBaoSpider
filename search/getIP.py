# -*- coding: utf-8 -*-
# __author__ = "zok" 
# Date: 2019/2/27  Python: 3.7

from selenium import webdriver
from config import proxyUser, proxyPass, proxyHost, proxyPort
import string
import zipfile


def create_proxy_auth_extension(proxy_host, proxy_port,
                                proxy_username, proxy_password,
                                scheme='http', plugin_path=None):
    if plugin_path is None:
        plugin_path = r'./{}_{}@http-cla.abuyun.com_9030.zip'.format(proxy_username, proxy_password)

    manifest_json = """
       {
           "version": "1.0.0",
           "manifest_version": 2,
           "name": "Abuyun Proxy",
           "permissions": [
               "proxy",
               "tabs",
               "unlimitedStorage",
               "storage",
               "<all_urls>",
               "webRequest",
               "webRequestBlocking"
           ],
           "background": {
               "scripts": ["background.js"]
           },
           "minimum_chrome_version":"22.0.0"
       }
       """

    background_js = string.Template(
        """
        var config = {
            mode: "fixed_servers",
            rules: {
                singleProxy: {
                    scheme: "${scheme}",
                    host: "${host}",
                    port: parseInt(${port})
                },
                bypassList: ["foobar.com"]
            }
          };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "${username}",
                    password: "${password}"
                }
            };
        }

        chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
        );
        """
    ).substitute(
        host=proxy_host,
        port=proxy_port,
        username=proxy_username,
        password=proxy_password,
        scheme=scheme,
    )

    with zipfile.ZipFile(plugin_path, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)

    return plugin_path


proxy_auth_plugin_path = create_proxy_auth_extension(
    proxy_host=proxyHost,
    proxy_port=proxyPort,
    proxy_username=proxyUser,
    proxy_password=proxyPass)

option = webdriver.ChromeOptions()

option.add_argument("--start-maximized")
option.add_extension(proxy_auth_plugin_path)

# browser = webdriver.Chrome(executable_path='./chromedriver', chrome_options=option, service_args=SERVICE_ARGS)
# browser.get("http://test.abuyun.com")
