"""Central i18n helper — EN default, ZH toggle kept.

Design (no behavior change):
- Backend language is selected via ``MUSE2API_LANG`` env (``en`` default, ``zh`` opt-in).
  Frontend (admin.html / extension) has its own EN/ZH toggle persisted in
  localStorage, independent of the backend.
- Upstream prompts sent to muse.ai (build_image_prompt / build_video_prompt)
  stay bilingual on purpose — pure-EN prompts change model behavior.
- Error *codes/types* are stable; only human *messages* are translated.
  Any ``in str(exc)`` branch must match BOTH languages (see MEDIA_TEXT_HINTS).
"""
from __future__ import annotations

import os

SUPPORTED = ("en", "zh")
DEFAULT_LANG = "en"

# Substrings that mean "model returned text instead of media".
# app.py retry logic checks these — keep both languages forever.
# Must stay substrings of t("media_only_text") in both languages
# (plus legacy variants for errors raised before i18n).
MEDIA_TEXT_HINTS = (
    "returned only text and produced no media",  # en (t("media_only_text"))
    "模型未生成媒体，仅返回文本",  # zh (t("media_only_text"))
    "did not produce a media attachment, only returned a text reply",  # en (legacy)
    "未产出媒体附件，仅返回了文本回复",  # zh (legacy)
)

# Delivery-not-confirmed hints (engine.py raises EN, matches both).
DELIVERY_HINTS = (
    "prompt was not delivered to the backend",
    "Prompt was not delivered to the backend",
    "提示词未成功送达后端",
)

_STRINGS: dict[str, dict[str, str]] = {
    # ---- auth / accounts (app.py) ----
    "missing_auth": {
        "en": "Missing Authorization: Bearer <key>",
        "zh": "缺少 Authorization: Bearer <key>",
    },
    "invalid_key": {
        "en": "Invalid API key",
        "zh": "API key 无效",
    },
    "validation_failed": {
        "en": "Request validation failed: ",
        "zh": "请求参数校验失败：",
    },
    "account_busy_timeout": {
        "en": "Timed out waiting for a free account; all accounts are busy",
        "zh": "等待空闲账号超时，当前所有账号均处于繁忙中",
    },
    "account_missing": {
        "en": "No available account. Import cookies in the admin page first",
        "zh": "没有可用账号，请先在管理页面导入 cookie",
    },
    "account_disabled": {
        "en": "Specified account does not exist or is disabled",
        "zh": "指定账号不存在或已禁用",
    },
    "browser_queue_timeout": {
        "en": "Browser queue wait timed out, please retry later",
        "zh": "等待浏览器队列超时，请稍后重试",
    },
    "task_deadline": {
        "en": "Total task deadline reached, stop retrying",
        "zh": "任务总等待时限已到，停止重试",
    },
    "image_task_missing": {
        "en": "image task not found",
        "zh": "image task 不存在",
    },
    # ---- engine.py (most user-visible) ----
    "chromium_failed": {
        "en": "Failed to start Chromium: ",
        "zh": "Chromium 启动失败: ",
    },
    "session_network_failed": {
        "en": "Request failed; check server network/proxy and retry",
        "zh": "网络请求失败；请检查服务器网络/代理后重试",
    },
    "session_401": {
        "en": "Session auth failed (HTTP 401). Confirm login on the official site, then re-import cookies",
        "zh": "会话认证失败 (HTTP 401)，请在官网确认登录后重新导入 cookie",
    },
    "quota_exhausted": {
        "en": "Account quota exhausted",
        "zh": "账号额度不足",
    },
    "gateway_timeout": {
        "en": "Page gateway connection timed out, switching account automatically",
        "zh": "页面网关连接超时，正在自动切换账号",
    },
    "logged_out": {
        "en": "Session was logged out by muse.ai (kicked by another login or risk control). Please re-import cookies",
        "zh": "会话已被 muse.ai 登出（可能被其它登录挤掉或触发风控），请重新导入 cookie",
    },
    "page_load_timeout": {
        "en": "muse.ai page load timed out (chat input not found). Check server network and retry; session NOT marked invalid",
        "zh": "muse.ai 页面加载超时（未出现聊天输入框），请检查服务器网络后重试；未确认会话失效",
    },
    "media_only_text": {
        "en": "Model returned only text and produced no media: ",
        "zh": "模型未生成媒体，仅返回文本: ",
    },
    "reference_read_failed": {
        "en": "Failed to read reference image, generation aborted",
        "zh": "参考图读取失败，已停止生成",
    },
    "reference_attach_failed": {
        "en": "Failed to attach reference image, generation aborted",
        "zh": "附加参考图失败，已停止生成",
    },
    "reference_upload_unconfirmed": {
        "en": "Reference image upload unconfirmed, generation aborted",
        "zh": "参考图上传未确认，已停止生成",
    },
    "session_http_forbidden": {
        "en": "Access denied, check server egress/region/access limits; cookies NOT proven invalid",
        "zh": "访问被拒绝，请检查服务器出口/地区/访问限制；不能据此判定 Cookie 失效",
    },
    "session_http_other": {
        "en": "Upstream request failed, retry later and check server network",
        "zh": "上游请求未成功，请稍后重试并检查服务器网络",
    },
    "session_not_json": {
        "en": "/api/session HTTP 200 returned non-JSON; session state unconfirmed",
        "zh": "/api/session HTTP 200 返回非 JSON；会话状态未确认",
    },
    "session_not_assigned": {
        "en": "/api/session HTTP 200 returned no assigned session; check account/workspace status on the official site",
        "zh": "/api/session HTTP 200 未返回 assigned 会话；请在官网检查账号/工作区状态",
    },
    "settings_button_missing": {
        "en": "Settings button not found",
        "zh": "找不到 Settings 按钮",
    },
    "settings_menu_missing": {
        "en": "Settings menu did not pop up",
        "zh": "Settings 菜单未弹出",
    },
    "chat_input_missing": {
        "en": "Chat input box not found",
        "zh": "找不到聊天输入框",
    },
    "client_disconnected": {
        "en": "Client disconnected, generation task aborted",
        "zh": "客户端已断开连接，终止生成任务",
    },
    "prompt_undelivered": {
        "en": "Prompt was not delivered to the backend (Still sending / Delivery not confirmed), aborting wait to retry",
        "zh": "提示词未成功送达后端（Still sending / Delivery not confirmed），终止等待并重试",
    },
    "vm_connect_timeout": {
        "en": "Cloud VM connection timed out (Still sending)",
        "zh": "云端 VM 连接超时 (Still sending)",
    },
    "first_token_timeout": {
        "en": "Timed out waiting for the assistant's first token",
        "zh": "等待助手首字响应超时",
    },
    "chat_reply_timeout": {
        "en": "Timed out waiting for the assistant's reply",
        "zh": "等待助手回复超时",
    },
    "extract_failed": {
        "en": "Failed to retrieve the generation result: ",
        "zh": "未能取回生成结果: ",
    },
    "prepare_timeout": {
        "en": "Task preparation timed out, send aborted",
        "zh": "任务准备超时，已停止发送",
    },
    "send_unconfirmed": {
        "en": "Prompt send unconfirmed, generation aborted",
        "zh": "提示词发送未确认，已停止生成",
    },
    "generation_timeout": {
        "en": "Timed out waiting for generation, no new result appeared",
        "zh": "等待生成超时，未出现新的生成结果",
    },
    "video_got_image_extract": {
        "en": "Expected a video but the extracted result is an image (",
        "zh": "期望生成视频，但提取成品类型为图片 (",
    },
    "video_got_image_download": {
        "en": "Expected a video but the downloaded result is an image (",
        "zh": "期望生成视频，但下载成品类型为图片 (",
    },
    "video_got_image_suffix": {
        "en": "), refusing to deliver an image as a video",
        "zh": ")，拒绝以图片冒充视频交付",
    },
    "fetch_failed": {
        "en": "Generated but failed to retrieve the file",
        "zh": "已生成但未能取回文件",
    },
    "image_task_missing": {
        "en": "image task not found",
        "zh": "image task 不存在",
    },
    "video_task_missing": {
        "en": "task not found",
        "zh": "task 不存在",
    },
    "messages_empty": {
        "en": "messages is empty",
        "zh": "messages 为空",
    },
    "input_empty": {
        "en": "input is empty",
        "zh": "input 为空",
    },
    "no_account_short": {
        "en": "No available account",
        "zh": "没有可用账号",
    },
    "bad_filename": {
        "en": "Invalid filename",
        "zh": "非法文件名",
    },
    "file_missing": {
        "en": "File not found",
        "zh": "文件不存在",
    },
    "no_cookies_parsed": {
        "en": "No cookies parsed, please check the format",
        "zh": "未解析到任何 cookie，请检查格式",
    },
    "cookies_not_parsed": {
        "en": "No cookies parsed",
        "zh": "未解析到 cookie",
    },
    "account_not_found": {
        "en": "Account not found",
        "zh": "账号不存在",
    },
    "account_no_cookies": {
        "en": "This account has no cookies",
        "zh": "该账号没有 cookie",
    },
    "quota_panel_empty": {
        "en": "Quota panel returned no valid data; old cache kept",
        "zh": "额度面板未读到有效数据；旧缓存未覆盖",
    },
    "quota_query_failed": {
        "en": "Quota query failed: ",
        "zh": "额度查询失败: ",
    },
    "helper_missing": {
        "en": "Helper script missing",
        "zh": "助手脚本缺失",
    },
    "ext_dir_missing": {
        "en": "Extension directory missing",
        "zh": "扩展目录缺失",
    },
    "names_must_be_array": {
        "en": "names must be an array of filenames",
        "zh": "names 必须是文件名数组",
    },
    "delete_failed": {
        "en": "Delete failed: ",
        "zh": "删除失败: ",
    },
    "update_dl_failed": {
        "en": "Failed to download GitHub update package (HTTP ",
        "zh": "下载 GitHub 更新包失败 (HTTP ",
    },
}


def get_lang() -> str:
    """Backend language: MUSE2API_LANG env, default 'en'."""
    v = (os.environ.get("MUSE2API_LANG") or DEFAULT_LANG).strip().lower()
    if v in ("zh", "zh-cn", "zh_cn", "chinese"):
        return "zh"
    return "en"


def t(key: str, lang: str | None = None) -> str:
    """Translate *key* to *lang* (defaults to get_lang()). Falls back to EN."""
    entry = _STRINGS.get(key)
    if not entry:
        return key
    lang = (lang or get_lang()).lower()
    if lang not in SUPPORTED:
        lang = DEFAULT_LANG
    return entry.get(lang) or entry["en"]


def is_media_only_text_error(exc: BaseException | str) -> bool:
    """True if *exc* is the 'text instead of media' error in either language."""
    s = str(exc) if not isinstance(exc, str) else exc
    return any(h in s for h in MEDIA_TEXT_HINTS)
