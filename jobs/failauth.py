from driver.base import WX_API
from core.config import cfg
from jobs.notice import sys_notice
from driver.success import Success
from tools.base64_tools import image_to_base64_data
from core.notice.wechat import send_wechat_image_message
from core.log import logger
import hashlib
import time

def send_wx_code(title:str="",url:str=""):
    if cfg.get("server.send_code",False):
        WX_API.GetCode(Notice=CallBackNotice,CallBack=Success)
    pass
def CallBackNotice(data=None,ext_data=None):
    if data is not None:
        logger.warning(data)
        return

    text = f"- 服务名：{cfg.get('server.name','')}\n"
    text += f"- 发送时间： {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))}\n"

    # 生成并加载二维码图片
    WX_API.QRcode()
    image_path = "./static/wx_qrcode.png"

    try:
        base64_data = image_to_base64_data(image_path)
        with open(image_path, "rb") as f:
            md5 = hashlib.md5(f.read()).hexdigest()
        logger.warning(f'微信公众号二维码base64编码：{base64_data}')
        logger.warning(f'微信公众号base64编码前的md5值：{md5}')
    except Exception as e:
        logger.error(f"生成二维码图片失败: {e}")
        sys_notice(text, "微信公众号授权过期扫码")
        return

    notice_cfg = cfg.get("notice", {}) or {}
    wechat_webhook = str(notice_cfg.get("wechat", "")).strip()

    if WX_API.GetHasCode() and wechat_webhook:
        # 通过企业微信机器人发送图片消息
        send_wechat_image_message(wechat_webhook, base64_data, md5)
        text += "\n- 已通过企业微信发送二维码图片，请扫码完成授权"
    else:
        text += "\n- 未获取到企业微信配置或二维码，请登录系统查看授权二维码"

    sys_notice(text, "微信公众号授权过期扫码")