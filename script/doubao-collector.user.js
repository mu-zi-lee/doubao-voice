// ==UserScript==
// @name         豆包内容自动采集器
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  抓取豆包接收消息中的代码块内容并发送至本地中继
// @author       木子不是木子狸
// @match        https://www.doubao.com/*
// @connect      127.0.0.1
// @grant        GM_xmlhttpRequest
// ==/UserScript==

(function () {
  "use strict";

  const RELAY_URL = "http://127.0.0.1:8000/api/push";
  const DEFAULT_MODE = "restore";
  let lastSentContent = "";

  function getLatestCodeBlockText() {
    const selector =
      '[data-testid="message_text_content"] pre code';
    const nodes = document.querySelectorAll(selector);
    if (nodes.length === 0) {
      const fallback = document.querySelectorAll("pre code");
      if (fallback.length === 0) return null;
      return fallback[fallback.length - 1].innerText.trim();
    }
    return nodes[nodes.length - 1].innerText.trim();
  }

  function sendToRelay(content, mode) {
    GM_xmlhttpRequest({
      method: "POST",
      url: RELAY_URL,
      data: JSON.stringify({
        content,
        timestamp: Date.now(),
        mode: mode || DEFAULT_MODE,
      }),
      headers: { "Content-Type": "application/json" },
      onload: (res) => {
        if (res.status >= 200 && res.status < 300) {
          console.log("[doubao-collector] 发送成功:", content.substring(0, 20) + "...");
        } else {
          console.warn("[doubao-collector] 中继返回:", res.status);
        }
      },
      onerror: () => console.error("[doubao-collector] 中继未启动或连接失败"),
    });
  }

  const observer = new MutationObserver(() => {
    const text = getLatestCodeBlockText();
    if (text && text !== lastSentContent) {
      lastSentContent = text;
      sendToRelay(text, DEFAULT_MODE);
    }
  });

  observer.observe(document.body, { childList: true, subtree: true });
})();
