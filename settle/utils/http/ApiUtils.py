import hashlib
import hmac
import time

from settle.utils.http.HttpUtils import HttpUtils


class ApiUtils:

    @staticmethod
    def get(url, access_key, secret_key, params={}, headers={}):
        headers.update({
            'X-HK-APIKEY': access_key,
            'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
        })
        ApiUtils.sign(secret_key, params)
        return HttpUtils.get(url, params, headers)

    @staticmethod
    def post(url, access_key, secret_key, params={}, headers={}, body: str = None):
        headers.update({
            'X-HK-APIKEY': access_key,
            'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
        })
        ApiUtils.sign(secret_key, params)
        return HttpUtils.post(url, params, body, headers)

    @staticmethod
    def delete(url, access_key, secret_key, params={}, headers={}):
        headers.update({
            'X-HK-APIKEY': access_key,
            'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
        })
        ApiUtils.sign(secret_key, params)
        return HttpUtils.delete(url, params, headers)

    @staticmethod
    def sign(secret_key, params={}):
        params['timestamp'] = str(ApiUtils.get_now_timestamp())
        content_for_sign = '&'.join([f"{k}={v}" for k, v in params.items()])
        signature = ApiUtils.create_signature(content_for_sign, secret_key)
        params['signature'] = signature

    @staticmethod
    def get_now_timestamp() -> int:
        timestamp = int(round(time.time() * 1000))
        return timestamp

    @staticmethod
    def create_signature(content: str, secret: str):
        sign_content = bytes(content, encoding='utf-8')
        h = hmac.new(secret.encode('utf-8'), sign_content, hashlib.sha256)
        signature = h.hexdigest()
        return signature
