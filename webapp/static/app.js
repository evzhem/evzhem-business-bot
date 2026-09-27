const DEMO_USER_ID = 777888999;
let activeAnimations = [];
let currentFilter = 'all';

const ALL_FUNCTIONS_CATALOG = [
  // 1. Голос & Мультимедиа
  {
    category: "🎙️ Голос и Мультимедиа",
    cmd: ".гс [текст]",
    title: "Озвучка в Голосовое Сообщение (TTS)",
    desc: "Превращает текст в настоящее голосовое сообщение от вашего имени с реалистичным голосом.",
    example: ".гс Привет! Сейчас занят, перезвоню через 10 минут."
  },
  {
    category: "🎙️ Голос и Мультимедиа",
    cmd: ".qr [ссылка/текст]",
    title: "Мгновенный генератор QR-кодов",
    desc: "Создает аккуратное изображение QR-кода и отправляет прямо в чат.",
    example: ".qr https://t.me/evzhem_business_bot"
  },

  // 2. CRM & Досье
  {
    category: "💼 Личный CRM & Бизнес",
    cmd: ".досье",
    title: "Полная карточка собеседника",
    desc: "Показывает сохраненные теги, заметки, баланс переписки и дату первой активности.",
    example: ".досье"
  },
  {
    category: "💼 Личный CRM & Бизнес",
    cmd: ".тег [название]",
    title: "Присвоить тег контакту",
    desc: "Добавляет метку к человеку (#VIP, #Клиент, #Партнер, #Семья).",
    example: ".тег VIP_Клиент"
  },
  {
    category: "💼 Личный CRM & Бизнес",
    cmd: ".заметка [текст]",
    title: "Личная заметка о друге / клиенте",
    desc: "Сохраняет важные детали (день рождения, договоренности, предпочтения).",
    example: ".заметка Дедлайн 15 октября, кофе без сахара"
  },
  {
    category: "💼 Личный CRM & Бизнес",
    cmd: ".чек [сумма] [услуга]",
    title: "Электронный чек / Счёт",
    desc: "Генерирует стильный чек с номером транзакции, штрихкодом и суммой.",
    example: ".чек 15000 Разработка бота"
  },

  // 3. AI & Работа с текстом
  {
    category: "🧠 AI-Интеллект и Текст",
    cmd: ".суммари [N]",
    title: "AI-Выжимка переписки",
    desc: "Нейросеть делает краткую структурированную сводку последних сообщений в диалоге.",
    example: ".суммари 20"
  },
  {
    category: "🧠 AI-Интеллект и Текст",
    cmd: ".исправь [текст]",
    title: "Умный AI-Корректор",
    desc: "Мгновенно исправляет ошибки, опечатки и знаки препинания.",
    example: ".исправь превет как дила я тут бота пишу"
  },
  {
    category: "🧠 AI-Интеллект и Текст",
    cmd: ".стиль [деловой] [текст]",
    title: "Изменение стиля текста",
    desc: "Переписывает ваше сообщение в вежливый деловой или дружеский стиль.",
    example: ".стиль деловой мне нужен отчет сейчас"
  },
  {
    category: "🧠 AI-Интеллект и Текст",
    cmd: ".перевод [язык] [текст]",
    title: "Синхронный переводчик",
    desc: "Переводит текст на любой язык мира (en, de, es, zh, tr, etc.).",
    example: ".перевод en Привет, как твои дела?"
  },
  {
    category: "🧠 AI-Интеллект и Текст",
    cmd: ".ai [вопрос]",
    title: "Быстрый ответ ChatGPT в чат",
    desc: "Задает вопрос нейросети и вставляет емкий ответ прямо в сообщение.",
    example: ".ai Что такое блокчейн простыми словами?"
  },

  // 4. Анимации & Трансформеры
  {
    category: "💫 Живые Анимации & Смайлы",
    cmd: ".люблю",
    title: "Признание в любви с замочком",
    desc: "Покадровая сборка романтической открытки с сохранением на замок.",
    example: ".люблю"
  },
  {
    category: "💫 Живые Анимации & Смайлы",
    cmd: ".печать [текст]",
    title: "Эффект пишущей машинки",
    desc: "Текст печатается по буквам в реальном времени с мигающим курсором.",
    example: ".печать Привет! Это живой набор текста."
  },
  {
    category: "💫 Живые Анимации & Смайлы",
    cmd: ".сердце",
    title: "Пульсирующее сердце",
    desc: "Красивая пульсация разноцветных сердец.",
    example: ".сердце"
  },
  {
    category: "💫 Живые Анимации & Смайлы",
    cmd: ".корона",
    title: "Коронация короля/королевы",
    desc: "Трансформация в сияющую золотую корону.",
    example: ".корона"
  },
  {
    category: "💫 Живые Анимации & Смайлы",
    cmd: ".дождь",
    title: "Гроза и радуга",
    desc: "Покадровый дождь, переходящий в сияющую радугу.",
    example: ".дождь"
  },
  {
    category: "💫 Живые Анимации & Смайлы",
    cmd: ".иди нахуй",
    title: "Трансформация в букет роз",
    desc: "Превращает грубость в распускающуюся розу.",
    example: ".иди нахуй"
  },
  {
    category: "💫 Живые Анимации & Смайлы",
    cmd: ".загрузка",
    title: "Прогресс-бар 0-100%",
    desc: "Анимированная шкала загрузки.",
    example: ".загрузка"
  },
  {
    category: "💫 Живые Анимации & Смайлы",
    cmd: ".матрица",
    title: "Зеленый код Матрицы",
    desc: "Бегущий бинарный код и фраза из фильма.",
    example: ".матрица"
  },

  // 5. Модерация & Приватность
  {
    category: "🔇 Модерация и Приватность",
    cmd: ".мут [время]",
    title: "Тихий мут собеседника",
    desc: "Мгновенно и бесшумно удаляет любые входящие сообщения от спамера.",
    example: ".мут 15м"
  },
  {
    category: "🔇 Модерация и Приватность",
    cmd: ".антимут",
    title: "Белый список контактов",
    desc: "Защищает избранный контакт от действия мута.",
    example: ".антимут"
  },
  {
    category: "🔇 Модерация и Приватность",
    cmd: ".самоуничтожение [сек] [текст]",
    title: "Секретное исчезающее сообщение",
    desc: "Удаляет сообщение через указанный таймер секунд.",
    example: ".самоуничтожение 10 Секретный пароль"
  },
  {
    category: "🔇 Модерация и Приватность",
    cmd: ".спам [текст] [кол-во]",
    title: "Безопасный спам (макс. 30)",
    desc: "Серийная отправка сообщений с защитой от флуда.",
    example: ".спам 'Проснись!' 10"
  },

  // 6. Утилиты и Финансы
  {
    category: "💎 Финансы и Утилиты",
    cmd: ".крипта",
    title: "Курсы BTC, ETH, TON, SOL",
    desc: "Котировки и суточная динамика в реальном времени.",
    example: ".крипта"
  },
  {
    category: "💎 Финансы и Утилиты",
    cmd: ".погода [город]",
    title: "Прогноз погоды",
    desc: "Температура, влажность, ветер и облачность.",
    example: ".погода Москва"
  },
  {
    category: "💎 Финансы и Утилиты",
    cmd: ".пароль [длина]",
    title: "Генератор надежных паролей",
    desc: "Создает безопасный пароль с кнопкой копирования.",
    example: ".пароль 16"
  },
  {
    category: "💎 Финансы и Утилиты",
    cmd: ".вики [запрос]",
    title: "Выжимка из Википедии",
    desc: "Быстрый поиск энциклопедической справки.",
    example: ".вики Телеграм"
  },
  {
    category: "💎 Финансы и Утилиты",
    cmd: ".калькулятор [выражение]",
    title: "Математический расчет на лету",
    desc: "Быстро считает формулы (.калькулятор 25*40 + 150).",
    example: ".калькулятор 150 * 4 + 80"
  },
  {
    category: "💎 Финансы и Утилиты",
    cmd: ".шрифт [1-4] [текст]",
    title: "Красивые Unicode шрифты",
    desc: "Жирный, курсив, моноширинный, баббл-стили.",
    example: ".шрифт 1 Привет, мир"
  },
  {
    category: "💎 Финансы и Утилиты",
    cmd: ".наша стата",
    title: "Карточка статистики переписки",
    desc: "Соотношение сообщений, баланс общения и ранг связи.",
    example: ".наша стата"
  },
  {
    category: "💎 Финансы и Утилиты",
    cmd: ".инфо",
    title: "Шуточный сканер собеседника",
    desc: "Определяет IQ, токсичность, доброту и вайб.",
    example: ".инфо"
  },
  {
    category: "💎 Финансы и Утилиты",
    cmd: ".комплимент",
    title: "Генератор приятных комплиментов",
    desc: "Поднимает настроение собеседнику.",
    example: ".комплимент"
  }
];

document.addEventListener('DOMContentLoaded', () => {
  initTabs();
  loadUserProfile();
  loadCatalog();
  loadAnimations();
  loadCRM();
  loadAutoresponderSettings();
  loadMutes();
  loadAchievements();
  setupEventListeners();
});

function showToast(message) {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.innerHTML = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 2800);
}

function initTabs() {
  const tabBtns = document.querySelectorAll('.tab-btn');
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.getAttribute('data-tab');
      switchTab(targetTab);
    });
  });
}

function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(b => {
    b.classList.toggle('active', b.getAttribute('data-tab') === tabId);
  });
  document.querySelectorAll('.tab-pane').forEach(p => {
    p.classList.toggle('active', p.id === `tab-${tabId}`);
  });
}

// 1. CATALOG TAB
function loadCatalog(filterText = '') {
  const list = document.getElementById('catalogList');
  if (!list) return;
  list.innerHTML = '';

  const search = filterText.toLowerCase().trim();

  // Group by category
  const categories = {};
  ALL_FUNCTIONS_CATALOG.forEach(item => {
    if (search) {
      const matched = item.cmd.toLowerCase().includes(search) || 
                      item.title.toLowerCase().includes(search) || 
                      item.desc.toLowerCase().includes(search);
      if (!matched) return;
    }
    if (!categories[item.category]) {
      categories[item.category] = [];
    }
    categories[item.category].push(item);
  });

  if (Object.keys(categories).length === 0) {
    list.innerHTML = '<div style="text-align:center; padding: 30px; color: var(--text-secondary);">Ничего не найдено по вашему запросу.</div>';
    return;
  }

  for (const [catName, items] of Object.entries(categories)) {
    const section = document.createElement('div');
    section.className = 'card';
    section.style.marginBottom = '16px';

    let itemsHtml = '';
    items.forEach(it => {
      itemsHtml += `
        <div class="mute-item" style="margin-bottom: 8px; flex-direction: column; align-items: flex-start; gap: 6px;">
          <div style="display:flex; justify-content:space-between; width:100%; align-items:center;">
            <span style="font-weight:800; color:#64b5f6; font-size:15px;">${it.cmd}</span>
            <div style="display:flex; gap:6px;">
              <button class="btn-secondary" style="padding:4px 10px; font-size:11px;" onclick="copyCommand('${it.cmd.split(' ')[0]}')">📋 Копия</button>
              <button class="btn-primary" style="padding:4px 10px; font-size:11px;" onclick="tryInSimulator('${it.example}')">⚡ Тест</button>
            </div>
          </div>
          <div style="font-weight:700; font-size:13px; color:#fff;">${it.title}</div>
          <div style="font-size:12px; color:var(--text-secondary);">${it.desc}</div>
          <div style="font-size:11px; color:var(--text-muted); background:var(--bg-main); padding:4px 8px; border-radius:6px; width:100%;">Пример: <code>${it.example}</code></div>
        </div>
      `;
    });

    section.innerHTML = `
      <h3 style="color:#f1c40f; margin-bottom: 12px; font-size: 15px;">${catName} (${items.length})</h3>
      <div style="display:flex; flex-direction:column; gap:6px;">
        ${itemsHtml}
      </div>
    `;
    list.appendChild(section);
  }
}

function tryInSimulator(cmdExample) {
  switchTab('dashboard');
  setSimInput(cmdExample);
  showToast(`Команда <b>${cmdExample.split(' ')[0]}</b> перенесена в симулятор! Нажмите «Отправить».`);
}

// 2. USER PROFILE
async function loadUserProfile() {
  try {
    const res = await fetch(`/api/user/${DEMO_USER_ID}`);
    const data = await res.json();
    document.getElementById('userName').textContent = data.first_name || 'evzhem';
    document.getElementById('userAvatar').textContent = (data.first_name || 'E')[0];
    
    if (data.is_premium) {
      document.getElementById('userBadge').textContent = '👑 VIP Премиум';
    } else {
      document.getElementById('userBadge').textContent = '🆓 Базовый';
      document.getElementById('userBadge').className = 'badge';
    }

    if (data.is_connected) {
      document.getElementById('connDot').className = 'status-dot connected';
      document.getElementById('connText').textContent = `Telegram Business: ${data.connection_rights}`;
    }

    document.getElementById('statOutgoing').textContent = data.stats.total_outgoing || 0;
    document.getElementById('statIncoming').textContent = data.stats.total_incoming || 0;
    document.getElementById('statDialogues').textContent = data.stats.total_dialogues || 0;

    document.getElementById('statTotAll').textContent = (data.stats.total_outgoing + data.stats.total_incoming) || 0;
    document.getElementById('statTotOut').textContent = data.stats.total_outgoing || 0;
    document.getElementById('statTotIn').textContent = data.stats.total_incoming || 0;

    const arSwitch = document.getElementById('quickToggleAR');
    arSwitch.checked = data.autoresponder_active;
    updateARStatusPill(data.autoresponder_active);
  } catch (err) {
    console.error('Error loading profile:', err);
  }
}

function updateARStatusPill(isActive) {
  const pill = document.getElementById('arStatusPill');
  if (isActive) {
    pill.innerHTML = '<span class="pill-dot on"></span> Режим: Активен 🟢 (Автоответчик отвечает в ЛС)';
  } else {
    pill.innerHTML = '<span class="pill-dot off"></span> Режим: Выключен 🔴 (Сообщения не перехватываются)';
  }
}

// 3. ANIMATIONS STUDIO
async function loadAnimations() {
  try {
    const res = await fetch(`/api/animations?user_id=${DEMO_USER_ID}`);
    const data = await res.json();
    activeAnimations = [...data.builtin, ...data.custom];
    renderAnimationsGrid();
  } catch (err) {
    console.error('Error loading animations:', err);
  }
}

function renderAnimationsGrid() {
  const grid = document.getElementById('animationsGrid');
  if (!grid) return;
  grid.innerHTML = '';

  const filtered = activeAnimations.filter(a => {
    if (currentFilter === 'all') return true;
    if (currentFilter === 'custom') return a.is_custom;
    return a.category === currentFilter;
  });

  if (filtered.length === 0) {
    grid.innerHTML = '<div style="grid-column: 1/-1; text-align:center; padding: 30px; color: var(--text-secondary);">В этой категории пока нет анимаций.</div>';
    return;
  }

  filtered.forEach(anim => {
    const card = document.createElement('div');
    card.className = 'anim-card';
    const lastFrame = anim.frames[anim.frames.length - 1];
    const previewText = anim.frames.length > 2 ? `${anim.frames[0]} ➔ ${lastFrame}` : lastFrame;

    card.innerHTML = `
      <div>
        <div class="anim-top">
          <div class="anim-cmd">${anim.command}</div>
          ${anim.is_premium ? '<span class="badge badge-vip">⭐ VIP</span>' : ''}
          ${anim.is_custom ? '<span class="badge" style="background:#8e44ad;color:#fff;">🎨 Кастом</span>' : ''}
        </div>
        <div class="anim-title">${anim.title}</div>
      </div>
      <div class="anim-preview-box" id="preview-${anim.name}">${previewText}</div>
      <div class="anim-actions">
        <button class="btn-play-anim" onclick="testAnimation('${anim.name}')">▶️ Тест</button>
        <button class="btn-copy-cmd" onclick="copyCommand('${anim.command}')">📋 Копия</button>
      </div>
    `;
    grid.appendChild(card);
  });
}

function copyCommand(cmd) {
  navigator.clipboard.writeText(cmd).then(() => {
    showToast(`Команда <b>${cmd}</b> скопирована! Отправьте её в любой ЛС чат.`);
  }).catch(() => {
    showToast(`Команда <b>${cmd}</b> готова к отправке.`);
  });
}

function testAnimation(animName) {
  const anim = activeAnimations.find(a => a.name === animName);
  if (!anim) return;

  const box = document.getElementById(`preview-${animName}`);
  if (!box) return;

  let frameIdx = 0;
  const intervalMs = Math.max(anim.interval * 1000, 320);

  box.style.borderColor = '#2481cc';
  const timer = setInterval(() => {
    if (frameIdx < anim.frames.length) {
      box.textContent = anim.frames[frameIdx];
      frameIdx++;
    } else {
      clearInterval(timer);
      setTimeout(() => {
        box.style.borderColor = 'rgba(255, 255, 255, 0.05)';
      }, 1000);
    }
  }, intervalMs);
}

// 4. LIVE CHAT SIMULATOR (DASHBOARD)
function setSimInput(text) {
  document.getElementById('simInput').value = text;
  document.getElementById('simInput').focus();
}

async function sendSimulatedMessage() {
  const input = document.getElementById('simInput');
  const text = input.value.trim();
  if (!text) return;

  const chat = document.getElementById('chatMessages');

  const outMsg = document.createElement('div');
  outMsg.className = 'msg outgoing';
  const now = new Date();
  const timeStr = `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`;
  
  outMsg.innerHTML = `
    <div class="msg-bubble">${text}</div>
    <div class="msg-time">${timeStr}</div>
  `;
  chat.appendChild(outMsg);
  input.value = '';
  chat.scrollTop = chat.scrollHeight;

  const bubble = outMsg.querySelector('.msg-bubble');

  try {
    const res = await fetch('/api/simulate/command', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ command_text: text, user_id: DEMO_USER_ID })
    });
    const data = await res.json();

    if (data.type === 'animation') {
      let frameIdx = 0;
      const intervalMs = Math.max(data.interval * 1000, 300);
      const timer = setInterval(() => {
        if (frameIdx < data.frames.length) {
          bubble.textContent = data.frames[frameIdx];
          chat.scrollTop = chat.scrollHeight;
          frameIdx++;
        } else {
          clearInterval(timer);
        }
      }, intervalMs);
    } else if (data.type === 'text') {
      bubble.innerHTML = data.result;
      chat.scrollTop = chat.scrollHeight;
    }
  } catch (err) {
    console.error('Simulation error:', err);
  }
}

// 5. CRM CONTACTS
async function loadCRM() {
  try {
    const res = await fetch(`/api/crm/contacts/${DEMO_USER_ID}`);
    const data = await res.json();
    const list = document.getElementById('crmNotesList');
    if (!list) return;
    list.innerHTML = '';

    if (data.notes.length === 0) {
      list.innerHTML = '<div style="color:var(--text-secondary);font-size:13px;">Заметок пока нет. Напишите в чате <code>.заметка Текст</code> или <code>.тег VIP</code>.</div>';
      return;
    }

    data.notes.forEach(n => {
      const item = document.createElement('div');
      item.className = 'mute-item';
      item.innerHTML = `
        <div>
          <div class="mute-name">${n.name} (ID: ${n.target_id})</div>
          <div style="font-size:13px; color:#fff; margin-top:2px;">📝 ${n.text}</div>
          <div class="mute-meta">${n.date}</div>
        </div>
      `;
      list.appendChild(item);
    });
  } catch (err) {
    console.error('CRM error:', err);
  }
}

// 6. AUTORESPONDER SETTINGS
async function loadAutoresponderSettings() {
  try {
    const res = await fetch(`/api/autoresponder/${DEMO_USER_ID}`);
    const data = await res.json();

    document.getElementById('arActive').checked = data.is_active;
    document.getElementById('arTextTemplate').value = data.text_template;
    document.getElementById('arAiPrompt').value = data.ai_prompt;
    document.getElementById('arTimeStart').value = data.work_hours_start;
    document.getElementById('arTimeEnd').value = data.work_hours_end;
    document.getElementById('arCooldown').value = data.cooldown_minutes;
    document.getElementById('cooldownLabel').textContent = `${data.cooldown_minutes} мин`;

    const radio = document.querySelector(`input[name="arMode"][value="${data.mode}"]`);
    if (radio) radio.checked = true;
    toggleModeFields(data.mode);
  } catch (err) {
    console.error('Error loading AR settings:', err);
  }
}

function toggleModeFields(mode) {
  document.getElementById('groupSchedule').style.display = (mode === 'schedule') ? 'flex' : 'none';
  document.getElementById('groupAiPrompt').style.display = (mode === 'ai') ? 'block' : 'none';
  document.getElementById('groupTextTemplate').style.display = (mode === 'ai') ? 'none' : 'block';
}

async function saveAutoresponderSettings() {
  const is_active = document.getElementById('arActive').checked;
  const mode = document.querySelector('input[name="arMode"]:checked').value;
  const text_template = document.getElementById('arTextTemplate').value;
  const ai_prompt = document.getElementById('arAiPrompt').value;
  const work_hours_start = document.getElementById('arTimeStart').value;
  const work_hours_end = document.getElementById('arTimeEnd').value;
  const cooldown_minutes = parseInt(document.getElementById('arCooldown').value);

  try {
    const res = await fetch(`/api/autoresponder/${DEMO_USER_ID}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        is_active,
        mode,
        text_template,
        ai_prompt,
        work_hours_start,
        work_hours_end,
        cooldown_minutes,
        keywords_json: "[]"
      })
    });
    const data = await res.json();
    if (data.status === 'ok') {
      showToast('✅ Настройки автоответчика сохранены!');
      document.getElementById('quickToggleAR').checked = is_active;
      updateARStatusPill(is_active);
    }
  } catch (err) {
    showToast('❌ Ошибка сохранения');
  }
}

// 7. MUTES & MODERATION
async function loadMutes() {
  try {
    const res = await fetch(`/api/mutes/${DEMO_USER_ID}`);
    const data = await res.json();
    const list = document.getElementById('mutesList');
    list.innerHTML = '';

    if (data.length === 0) {
      list.innerHTML = '<div style="color:var(--text-secondary);font-size:13px;">Список мутов пуст. Вы можете отправлять <code>.мут</code> прямо в чате.</div>';
      return;
    }

    data.forEach(m => {
      const item = document.createElement('div');
      item.className = 'mute-item';
      item.innerHTML = `
        <div>
          <div class="mute-name">${m.target_name}</div>
          <div class="mute-meta">ID: ${m.target_id} • До: ${m.muted_until}</div>
        </div>
        <button class="btn-danger" style="padding:4px 10px;font-size:12px;" onclick="deleteMute(${m.target_id})">Размутить 🔊</button>
      `;
      list.appendChild(item);
    });
  } catch (err) {
    console.error('Error loading mutes:', err);
  }
}

async function addMuteManual() {
  const targetId = document.getElementById('muteTargetId').value;
  const targetName = document.getElementById('muteTargetName').value || `User ${targetId}`;
  if (!targetId) {
    showToast('❌ Введите Telegram ID');
    return;
  }

  try {
    const res = await fetch(`/api/mutes/${DEMO_USER_ID}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_id: parseInt(targetId), target_name: targetName })
    });
    if (res.ok) {
      showToast(`🔇 Пользователь ${targetName} замучен!`);
      document.getElementById('muteTargetId').value = '';
      document.getElementById('muteTargetName').value = '';
      loadMutes();
    }
  } catch (err) {
    showToast('❌ Ошибка добавления');
  }
}

async function deleteMute(targetId) {
  try {
    const res = await fetch(`/api/mutes/${DEMO_USER_ID}/${targetId}`, { method: 'DELETE' });
    if (res.ok) {
      showToast('🔊 Мут успешно снят!');
      loadMutes();
    }
  } catch (err) {
    showToast('❌ Ошибка');
  }
}

// 8. ACHIEVEMENTS
async function loadAchievements() {
  try {
    const res = await fetch(`/api/achievements/${DEMO_USER_ID}`);
    const data = await res.json();
    const grid = document.getElementById('achievementsGrid');
    grid.innerHTML = '';

    data.forEach(a => {
      const card = document.createElement('div');
      card.className = `ach-card ${a.is_unlocked ? 'unlocked' : ''}`;
      card.innerHTML = `
        <div class="ach-icon">${a.icon}</div>
        <div class="ach-body">
          <div class="ach-title-row">
            <span>${a.title}</span>
            <span style="color:${a.is_unlocked ? 'var(--accent-success)' : 'var(--text-secondary)'}">
              ${a.is_unlocked ? '✅ Получено' : `${a.current_count}/${a.target_count}`}
            </span>
          </div>
          <div class="ach-desc">${a.description}</div>
          <div class="progress-bar-wrap">
            <div class="progress-bar-fill" style="width: ${a.progress_pct}%"></div>
          </div>
        </div>
      `;
      grid.appendChild(card);
    });
  } catch (err) {
    console.error('Error loading achievements:', err);
  }
}

// 9. EVENT LISTENERS
function setupEventListeners() {
  document.getElementById('btnSimSend').addEventListener('click', sendSimulatedMessage);
  document.getElementById('simInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendSimulatedMessage();
  });

  // Search in catalog
  const searchInput = document.getElementById('catalogSearch');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      loadCatalog(e.target.value);
    });
  }

  // Filter chips
  document.querySelectorAll('.filter-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      currentFilter = chip.getAttribute('data-filter');
      renderAnimationsGrid();
    });
  });

  const modal = document.getElementById('createAnimModal');
  document.getElementById('btnOpenCreateModal').addEventListener('click', () => modal.classList.add('open'));
  document.getElementById('btnCloseModal').addEventListener('click', () => modal.classList.remove('open'));
  document.getElementById('btnCancelModal').addEventListener('click', () => modal.classList.remove('open'));

  document.getElementById('customInterval').addEventListener('input', (e) => {
    document.getElementById('customIntervalLabel').textContent = `${e.target.value} сек`;
  });

  document.getElementById('arCooldown').addEventListener('input', (e) => {
    document.getElementById('cooldownLabel').textContent = `${e.target.value} мин`;
  });

  document.querySelectorAll('input[name="arMode"]').forEach(radio => {
    radio.addEventListener('change', (e) => toggleModeFields(e.target.value));
  });

  document.getElementById('btnSaveAutoresponder').addEventListener('click', saveAutoresponderSettings);

  document.getElementById('quickToggleAR').addEventListener('change', async (e) => {
    const isChecked = e.target.checked;
    document.getElementById('arActive').checked = isChecked;
    await saveAutoresponderSettings();
  });

  document.getElementById('btnSaveCustomAnim').addEventListener('click', async () => {
    const cmdName = document.getElementById('customCmdName').value.trim();
    const framesRaw = document.getElementById('customCmdFrames').value.trim();
    const interval = parseFloat(document.getElementById('customInterval').value);

    if (!cmdName || !framesRaw) {
      showToast('❌ Заполните название и хотя бы 2 кадра');
      return;
    }

    const frames = framesRaw.split('\n').map(f => f.trim()).filter(f => f.length > 0);
    try {
      const res = await fetch(`/api/animations/custom?user_id=${DEMO_USER_ID}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command_name: cmdName, frames, interval })
      });
      if (res.ok) {
        showToast(`🎉 Кастомная команда <b>.${cmdName}</b> успешно создана!`);
        modal.classList.remove('open');
        document.getElementById('customCmdName').value = '';
        document.getElementById('customCmdFrames').value = '';
        loadAnimations();
      }
    } catch (err) {
      showToast('❌ Ошибка создания');
    }
  });

  document.getElementById('btnAddMute').addEventListener('click', addMuteManual);
}

function buyPlan(plan) {
  showToast(`⭐ Переход к оплате Telegram Stars... (Тариф: ${plan})`);
  setTimeout(() => {
    showToast('🎉 Оплата Telegram Stars успешна! VIP Премиум активирован!');
    document.getElementById('userBadge').textContent = '👑 VIP Премиум';
    document.getElementById('userBadge').className = 'badge badge-vip';
  }, 1200);
}
