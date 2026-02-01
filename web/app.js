(function () {
  "use strict";

  const API = "/api";

  function showPanel(id) {
    document.querySelectorAll(".panel").forEach(function (el) {
      el.classList.add("hidden");
    });
    document.querySelectorAll("nav a").forEach(function (el) {
      el.classList.remove("active");
      if (el.getAttribute("href") === "#" + id) el.classList.add("active");
    });
    var panel = document.getElementById(id);
    if (panel) panel.classList.remove("hidden");
  }

  document.querySelectorAll("nav a").forEach(function (a) {
    a.addEventListener("click", function (e) {
      e.preventDefault();
      var href = a.getAttribute("href");
      if (href && href.startsWith("#")) showPanel(href.slice(1));
    });
  });

  function setStatus(elId, text, isError) {
    var el = document.getElementById(elId);
    if (!el) return;
    el.textContent = text;
    el.style.color = isError ? "#f87171" : "";
  }

  // --- Config ---
  var configForm = document.getElementById("config-form");
  var historySizeEl = document.getElementById("history_size");
  var aiOptimizeEl = document.getElementById("ai_optimize_enabled");
  var aiApiKeyEl = document.getElementById("ai_api_key");
  var aiBaseUrlEl = document.getElementById("ai_base_url");
  var defaultModeEl = document.getElementById("default_mode");

  function loadConfig() {
    fetch(API + "/config")
      .then(function (r) {
        if (!r.ok) throw new Error(r.statusText);
        return r.json();
      })
      .then(function (data) {
        historySizeEl.value = data.history_size || 10;
        aiOptimizeEl.checked = !!data.ai_optimize_enabled;
        if (aiApiKeyEl) aiApiKeyEl.value = data.ai_api_key || "";
        if (aiBaseUrlEl) aiBaseUrlEl.value = data.ai_base_url || "";
        defaultModeEl.value = data.default_mode || "restore";
      })
      .catch(function (err) {
        setStatus("config-status", "加载配置失败: " + err.message, true);
      });
  }

  configForm.addEventListener("submit", function (e) {
    e.preventDefault();
    var body = {
      history_size: parseInt(historySizeEl.value, 10) || 10,
      ai_optimize_enabled: aiOptimizeEl.checked,
      ai_api_key: (aiApiKeyEl && aiApiKeyEl.value) ? aiApiKeyEl.value : "",
      ai_base_url: (aiBaseUrlEl && aiBaseUrlEl.value) ? aiBaseUrlEl.value : "",
      default_mode: defaultModeEl.value || "restore",
    };
    fetch(API + "/config", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
      .then(function (r) {
        if (!r.ok) throw new Error(r.statusText);
        return r.json();
      })
      .then(function () {
        setStatus("config-status", "已保存。修改历史条数后需重启中继生效。");
      })
      .catch(function (err) {
        setStatus("config-status", "保存失败: " + err.message, true);
      });
  });

  // --- History ---
  var historyList = document.getElementById("history-list");
  var historyRefresh = document.getElementById("history-refresh");

  function loadHistory() {
    fetch(API + "/history")
      .then(function (r) {
        if (!r.ok) throw new Error(r.statusText);
        return r.json();
      })
      .then(function (list) {
        historyList.innerHTML = "";
        if (!list.length) {
          historyList.innerHTML = "<li>暂无记录</li>";
          return;
        }
        list.forEach(function (item) {
          var li = document.createElement("li");
          var meta = document.createElement("div");
          meta.className = "meta";
          meta.textContent =
            (item.timestamp ? new Date(item.timestamp).toLocaleString() : "") +
            " · " +
            (item.mode || "restore");
          var content = document.createElement("div");
          content.className = "content";
          content.textContent = item.content || "";
          li.appendChild(meta);
          li.appendChild(content);
          historyList.appendChild(li);
        });
      })
      .catch(function (err) {
        historyList.innerHTML = "<li>加载失败: " + err.message + "</li>";
      });
  }

  historyRefresh.addEventListener("click", loadHistory);

  // --- Prompts ---
  var promptsEditor = document.getElementById("prompts-editor");
  var promptsAdd = document.getElementById("prompts-add");
  var promptsSave = document.getElementById("prompts-save");

  function renderPrompts(data) {
    promptsEditor.innerHTML = "";
    var keys = Object.keys(data || {});
    if (keys.length === 0) {
      addPromptRow("", "");
      return;
    }
    keys.forEach(function (k) {
      addPromptRow(k, data[k]);
    });
  }

  function addPromptRow(key, value) {
    var row = document.createElement("div");
    row.className = "prompt-row";
    var keyInput = document.createElement("input");
    keyInput.type = "text";
    keyInput.className = "key";
    keyInput.placeholder = "键名";
    keyInput.value = key;
    var valueInput = document.createElement("textarea");
    valueInput.placeholder = "提示词内容";
    valueInput.value = value;
    var removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "remove";
    removeBtn.textContent = "删除";
    removeBtn.addEventListener("click", function () {
      row.remove();
    });
    row.appendChild(keyInput);
    row.appendChild(valueInput);
    row.appendChild(removeBtn);
    promptsEditor.appendChild(row);
  }

  function collectPrompts() {
    var out = {};
    promptsEditor.querySelectorAll(".prompt-row").forEach(function (row) {
      var keyEl = row.querySelector("input.key");
      var valueEl = row.querySelector("textarea");
      var k = (keyEl && keyEl.value && keyEl.value.trim()) || "";
      if (k) out[k] = (valueEl && valueEl.value) || "";
    });
    return out;
  }

  function loadPrompts() {
    fetch(API + "/prompts")
      .then(function (r) {
        if (!r.ok) throw new Error(r.statusText);
        return r.json();
      })
      .then(renderPrompts)
      .catch(function (err) {
        setStatus("prompts-status", "加载提示词失败: " + err.message, true);
      });
  }

  promptsAdd.addEventListener("click", function () {
    addPromptRow("", "");
  });

  promptsSave.addEventListener("click", function () {
    var body = collectPrompts();
    fetch(API + "/prompts", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
      .then(function (r) {
        if (!r.ok) throw new Error(r.statusText);
        return r.json();
      })
      .then(function () {
        setStatus("prompts-status", "已保存。");
      })
      .catch(function (err) {
        setStatus("prompts-status", "保存失败: " + err.message, true);
      });
  });

  // --- Init ---
  loadConfig();
  loadHistory();
  loadPrompts();

  var hash = (window.location.hash || "#settings").slice(1);
  if (hash && document.getElementById(hash)) showPanel(hash);
  else showPanel("settings");
})();
