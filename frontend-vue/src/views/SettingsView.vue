<template>
  <div class="settings-page">
    <header class="settings-header">
      <RouterLink to="/" class="settings-back">
        <IconChevronLeft :size="18" />
        <span>返回</span>
      </RouterLink>
      <nav class="settings-tabs">
        <button v-for="tab in TABS" :key="tab.key" type="button" class="settings-tab"
          :class="{ 'is-active': activeTab === tab.key }" @click="activeTab = tab.key">
          {{ tab.label }}
        </button>
      </nav>
    </header>

    <main class="settings-main">
      <SettingsSkeleton v-if="loading" />

      <div v-else-if="form" class="settings-stack">
        <section v-if="activeTab === 'profile'" class="settings-card">
          <div class="settings-card__grid">
            <div class="settings-card__col settings-card__col--profile">
              <div class="settings-card__title-row">
                <h2 class="settings-card__title">个人资料</h2>
                <ThemeToggle />
              </div>
              <div class="profile-block">
                <button type="button" class="profile-block__avatar" :disabled="uploading" title="点击更换头像"
                  @click="fileInputRef?.click()">
                  <img v-if="displayAvatarUrl" :src="displayAvatarUrl" alt="头像预览" />
                  <span v-else class="profile-block__fallback">{{ avatarFallback }}</span>
                  <span class="profile-block__overlay">点击更换</span>
                </button>
                <label class="field">
                  <span class="field__label">显示名称</span>
                  <input v-model="form.displayName" class="field-input" placeholder="我" />
                </label>
                <div class="profile-block__actions">
                  <button class="settings-btn settings-btn--secondary" type="button" :disabled="uploading"
                    @click="fileInputRef?.click()">
                    选择图片
                  </button>
                  <button v-if="pendingAvatarFile" class="settings-btn settings-btn--primary" type="button"
                    :disabled="uploading" @click="handleConfirmAvatar">
                    {{ uploading ? "上传中…" : "确认上传" }}
                  </button>
                  <button v-if="pendingAvatarFile" class="settings-btn settings-btn--secondary" type="button"
                    :disabled="uploading" @click="handleCancelAvatarPreview">
                    取消
                  </button>
                  <button v-if="form.avatarUrl && !pendingAvatarFile" class="settings-btn settings-btn--secondary"
                    type="button" :disabled="uploading" @click="handleRemoveAvatar">
                    恢复默认
                  </button>
                </div>
              </div>
              <input ref="fileInputRef" class="hidden" type="file" accept="image/*" @change="onAvatarSelect" />
              <label class="field-checkbox profile-block__transparent">
                <input v-model="form.avatarTransparent" class="field-checkbox__input" type="checkbox"
                  @change="onAvatarTransparentChange" />
                <span class="field-checkbox__text">头像透明背景</span>
                <span class="field-checkbox__hint">适合去背 PNG 头像</span>
              </label>
            </div>

            <div class="settings-card__col settings-card__col--account">
              <h2 class="settings-card__title">账户</h2>
              <p class="settings-card__desc">
                当前登录 <strong>{{ username }}</strong>，修改密码后需重新登录。
              </p>
              <form class="settings-fields settings-fields--account" @submit.prevent="handleChangeUsername">
                <label class="field field--full">
                  <span class="field__label">用户名</span>
                  <input v-model="newUsername" class="field-input" type="text" autocomplete="username" />
                </label>
                <p v-if="usernameMessage" class="field--full settings-message"
                  :class="usernameError ? 'settings-message--error' : 'settings-message--ok'">
                  {{ usernameMessage }}
                </p>
                <div class="field--full settings-actions">
                  <button class="settings-btn settings-btn--primary" type="submit" :disabled="changingUsername">
                    {{ changingUsername ? "修改中…" : "修改用户名" }}
                  </button>
                </div>
              </form>
              <form class="settings-fields settings-fields--account" @submit.prevent="handleChangePassword">
                <label class="field field--full">
                  <span class="field__label">当前密码</span>
                  <input v-model="currentPassword" class="field-input" type="password"
                    autocomplete="current-password" />
                </label>
                <label class="field">
                  <span class="field__label">新密码</span>
                  <input v-model="newPassword" class="field-input" type="password" autocomplete="new-password" />
                  <span class="field__hint">至少 6 位</span>
                </label>
                <label class="field">
                  <span class="field__label">确认新密码</span>
                  <input v-model="confirmPassword" class="field-input" type="password" autocomplete="new-password" />
                </label>
                <p v-if="passwordMessage" class="field--full settings-message"
                  :class="passwordError ? 'settings-message--error' : 'settings-message--ok'">
                  {{ passwordMessage }}
                </p>
                <div class="field--full settings-actions">
                  <button class="settings-btn settings-btn--primary" type="submit" :disabled="changingPassword">
                    {{ changingPassword ? "修改中…" : "修改密码" }}
                  </button>
                  <button class="settings-btn settings-btn--ghost" type="button" @click="handleLogout">退出登录</button>
                </div>
              </form>
            </div>
          </div>
        </section>

        <section v-if="activeTab === 'ai'" class="settings-card">
          <h2 class="settings-card__title">AI</h2>
          <p class="settings-card__desc">输入 @ai 或开启工具栏 AI 按钮时调用。</p>
          <div class="settings-fields">
            <label class="field">
              <span class="field__label">服务商</span>
              <select v-model="form.aiProvider" class="field-input" @change="onProviderChange">
                <option v-for="item in AI_PROVIDER_OPTIONS" :key="item.value" :value="item.value">
                  {{ item.label }}
                </option>
              </select>
            </label>
            <label class="field">
              <span class="field__label">模型名称</span>
              <select v-if="form.aiProvider === 'deepseek'" v-model="form.aiModel" class="field-input">
                <option v-for="item in DEEPSEEK_MODEL_OPTIONS" :key="item.value" :value="item.value">
                  {{ item.label }}
                </option>
              </select>
              <input v-else v-model="form.aiModel" class="field-input" placeholder="deepseek-v4-pro" />
            </label>
            <label class="field">
              <span class="field__label">API 地址</span>
              <input v-model="form.aiBaseUrl" class="field-input" placeholder="https://api.deepseek.com" />
            </label>
            <label class="field">
              <span class="field__label">API Key</span>
              <input v-model="apiKeyDraft" class="field-input" type="password" autocomplete="off"
                :placeholder="form.hasApiKey ? '留空则不修改，输入新 Key 以更换' : 'sk-...'" />
              <span class="field__hint">
                {{ form.hasApiKey ? "已配置 Key，仅提交到服务端保存，不会留在浏览器" : "仅提交到服务端保存，不会留在浏览器" }}
              </span>
            </label>
            <label v-if="form.aiProvider === 'deepseek'" class="field-checkbox">
              <input v-model="form.aiThinking" class="field-checkbox__input" type="checkbox" />
              <span class="field-checkbox__text">开启思考模式</span>
            </label>
            <label class="field">
              <span class="field__label">系统提示词</span>
              <textarea v-model="form.aiSystemPrompt" class="field-input field-textarea settings-editor"
                placeholder="你是写作与思考辅助工具，帮助用户整理自己写下的记录…" />
              <span class="field__hint">定义 AI 人设与语气；DeepSeek 风格排版规则会自动附加</span>
            </label>
          </div>
        </section>

        <section v-if="activeTab === 'persona'" class="settings-card">
          <h2 class="settings-card__title">AI 人格</h2>
          <p class="settings-card__desc">为 AI 设定不同的语气与视角，@ai 回复时使用当前"使用中"的人格系统提示词。</p>
          <div class="settings-fields">
            <div class="template-workspace">
              <div class="template-list">
                <button type="button" class="template-list__item" :class="{ 'is-active': selectedPersonaKey === 'none' }"
                  @click="selectedPersonaKey = 'none'">
                  <span class="template-list__name">不使用人格</span>
                  <span v-if="!form.activePersonaId" class="persona-active-badge">使用中</span>
                </button>
                <button v-for="p in personas" :key="p.id" type="button" class="template-list__item"
                  :class="{ 'is-active': selectedPersonaKey === p.id }" @click="selectedPersonaKey = p.id">
                  <span class="template-list__name">{{ p.icon ? `${p.icon} ` : "" }}{{ p.name || "未命名人格" }}</span>
                  <span v-if="form.activePersonaId === p.id" class="persona-active-badge">使用中</span>
                  <span class="template-list__del" title="删除" @click.stop="handleDeletePersona(p.id)">
                    <IconClose />
                  </span>
                </button>
                <p v-if="personaLoading" class="template-list__empty">加载中…</p>
                <button type="button" class="template-list__add" :disabled="creatingPersona" @click="handleAddPersona">
                  + 新增人格
                </button>
              </div>
              <div class="template-panel">
                <p v-if="selectedPersonaKey === 'none'" class="template-panel__empty">
                  不使用独立人格时，AI 回复将使用"AI"标签页里配置的系统提示词。
                </p>
                <template v-else-if="selectedPersona">
                  <input v-model="selectedPersona.name" class="field-input template-panel__name" placeholder="人格名称" />
                  <input v-model="selectedPersona.icon" class="field-input template-panel__name"
                    placeholder="图标 emoji（可选）" />
                  <textarea v-model="selectedPersona.systemPrompt" class="field-input field-textarea template-panel__content"
                    placeholder="你是……" />
                </template>
                <p v-else class="template-panel__empty">选择左侧人格进行编辑，或新增一个</p>
              </div>
            </div>
            <div class="settings-actions">
              <button type="button" class="settings-btn settings-btn--primary" :disabled="savingPersona || !selectedPersona"
                @click="handleSavePersona">
                {{ savingPersona ? "保存中…" : "保存人格" }}
              </button>
              <button type="button" class="settings-btn settings-btn--secondary" :disabled="settingActivePersona ||
                (form.activePersonaId ?? 'none') === selectedPersonaKey" @click="handleSetActivePersona">
                {{ settingActivePersona ? "切换中…" : "设为使用中" }}
              </button>
            </div>
            <p v-if="personaMessage" class="settings-message"
              :class="personaError ? 'settings-message--error' : 'settings-message--ok'">
              {{ personaMessage }}
            </p>
          </div>
        </section>

        <section v-if="activeTab === 'template'" class="settings-card">
          <h2 class="settings-card__title">消息模板</h2>
          <p class="settings-card__desc">
            常用记录格式，编辑器工具栏「模板」可一键插入。支持占位符
            <code>{date}</code> <code>{time}</code> <code>{datetime}</code> <code>{weekday}</code>，插入时自动替换为当前时间。
          </p>
          <div class="settings-fields">
            <div class="template-workspace">
              <div class="template-list">
                <button v-for="(tpl, index) in templateDraft" :key="index" type="button" class="template-list__item"
                  :class="{ 'is-active': index === selectedIndex }" @click="selectedIndex = index">
                  <span class="template-list__name">{{ tpl.name || "未命名模板" }}</span>
                  <span class="template-list__del" title="删除" @click.stop="removeTemplate(index)">
                    <IconClose />
                  </span>
                </button>
                <p v-if="!templateDraft.length" class="template-list__empty">还没有模板</p>
                <button type="button" class="template-list__add" @click="addTemplate">+ 新增模板</button>
              </div>
              <div class="template-panel">
                <template v-if="selectedTemplate">
                  <input v-model="selectedTemplate.name" class="field-input template-panel__name" placeholder="模板名称" />
                  <textarea v-model="selectedTemplate.content" class="field-input field-textarea template-panel__content"
                    placeholder="# 日精进 {date}" />
                </template>
                <p v-else class="template-panel__empty">选择左侧模板进行编辑，或新增一个</p>
              </div>
            </div>
            <div class="settings-actions">
              <button type="button" class="settings-btn settings-btn--primary" @click="handleSaveTemplates">
                保存模板
              </button>
              <button type="button" class="settings-btn settings-btn--secondary" @click="handleResetTemplates">
                恢复默认
              </button>
            </div>
            <p v-if="templateMessage" class="settings-message"
              :class="templateError ? 'settings-message--error' : 'settings-message--ok'">
              {{ templateMessage }}
            </p>
          </div>
        </section>

        <section v-if="activeTab === 'emoji'" class="settings-card">
          <h2 class="settings-card__title">表情列表</h2>
          <p class="settings-card__desc">每行一个 emoji，修改后保存即可在聊天中使用。</p>
          <div class="settings-fields">
            <label class="field">
              <textarea v-model="emojiDraft" class="field-input field-textarea settings-editor" />
            </label>
            <div class="settings-actions">
              <button class="settings-btn settings-btn--primary" type="button" :disabled="savingEmoji"
                @click="handleSaveEmoji">
                {{ savingEmoji ? "保存中…" : "保存表情" }}
              </button>
              <button class="settings-btn settings-btn--secondary" type="button" @click="handleResetEmoji">
                恢复默认
              </button>
            </div>
            <p v-if="emojiMessage" class="settings-message"
              :class="emojiError ? 'settings-message--error' : 'settings-message--ok'">
              {{ emojiMessage }}
            </p>
          </div>
        </section>

        <section v-if="activeTab === 'import'" class="settings-card">
          <h2 class="settings-card__title">导出记录</h2>
          <p class="settings-card__desc">导出全部聊天记录，附件以链接形式保留（不打包成 zip）。</p>
          <div class="settings-fields">
            <div class="settings-actions">
              <button class="settings-btn settings-btn--secondary" type="button" :disabled="exportingFormat === 'md'"
                @click="handleExport('md')">
                {{ exportingFormat === "md" ? "导出中…" : "导出 Markdown" }}
              </button>
              <button class="settings-btn settings-btn--secondary" type="button" :disabled="exportingFormat === 'json'"
                @click="handleExport('json')">
                {{ exportingFormat === "json" ? "导出中…" : "导出 JSON" }}
              </button>
            </div>
            <p v-if="exportError" class="settings-message settings-message--error">{{ exportError }}</p>
          </div>

          <h2 class="settings-card__title settings-card__title--secondary">导入 DeepSeek 分享</h2>
          <p class="settings-card__desc">粘贴 chat.deepseek.com/share/... 链接，按原时间顺序导入你与 AI 的对话。</p>
          <div class="settings-fields">
            <label class="field">
              <span class="field__label">分享链接</span>
              <input v-model="importUrl" class="field-input" placeholder="https://chat.deepseek.com/share/..."
                @input="clearImportState" />
            </label>
            <label class="field">
              <span class="field__label">导入方式</span>
              <select v-model="importMode" class="field-input">
                <option value="append">追加到现有记录后</option>
                <option value="replace">清空后导入</option>
              </select>
            </label>
            <div class="settings-actions">
              <button class="settings-btn settings-btn--secondary" type="button"
                :disabled="previewingImport || !importUrl.trim()" @click="handleImportPreview">
                {{ previewingImport ? "预览中…" : "预览" }}
              </button>
              <button class="settings-btn settings-btn--primary" type="button"
                :disabled="importing || !importUrl.trim()" @click="handleImport">
                {{ importing ? "导入中…" : "开始导入" }}
              </button>
            </div>
            <div v-if="importPreview" class="import-preview">
              <p class="import-preview__title">{{ importPreview.title }}</p>
              <p class="import-preview__summary">
                共 {{ importPreview.total }} 条（我 {{ importPreview.meCount }} / AI {{ importPreview.aiCount }}）
              </p>
              <p class="import-preview__range">
                {{ formatPreviewTime(importPreview.rangeFrom) }} — {{ formatPreviewTime(importPreview.rangeTo) }}
              </p>
              <div class="import-preview__list">
                <p v-for="(item, index) in importPreview.preview" :key="index" class="import-preview__item">
                  <span class="import-preview__meta">
                    {{ item.role === "me" ? "我" : "AI" }} · {{ formatPreviewTime(item.createdAt) }}
                  </span>
                  <br />
                  {{ item.content }}{{ item.content.length >= 160 ? "…" : "" }}
                </p>
              </div>
            </div>
            <p v-if="importFeedback" class="settings-message"
              :class="importError ? 'settings-message--error' : 'settings-message--ok'">
              {{ importFeedback }}
            </p>
          </div>
        </section>

        <div v-if="activeTab === 'profile' || activeTab === 'ai'" class="settings-save-bar">
          <p v-if="message"
            :class="['settings-message', messageError ? 'settings-message--error' : 'settings-message--ok']">
            {{ message }}
          </p>
          <button class="settings-btn settings-btn--primary settings-btn--wide" type="button" :disabled="saving"
            @click="handleSave">
            {{ saving ? "保存中…" : "保存设置" }}
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { RouterLink, useRouter } from "vue-router";
import SettingsSkeleton from "@/components/SettingsSkeleton.vue";
import ThemeToggle from "@/components/ThemeToggle.vue";
import { IconChevronLeft, IconClose } from "@/components/icons";
import { applyAvatarTransparency } from "@/lib/avatar-style";
import {
  AI_PRESETS,
  AI_PROVIDER_OPTIONS,
  DEEPSEEK_MODEL_OPTIONS,
} from "@/lib/ai-presets";
import {
  changePassword,
  changeUsername,
  createPersona,
  deletePersona,
  exportMessages,
  fetchPersonas,
  fetchSettings,
  importDeepSeekShare,
  previewDeepSeekShare,
  removeAvatar,
  saveSettings,
  setActivePersona,
  updatePersona,
  uploadAvatar,
} from "@/lib/api";
import { clearAuthTokens, readUsername, updateStoredUsername } from "@/lib/auth";
import { readEmojiList, writeEmojiList, resetEmojiList } from "@/lib/emoji-storage";
import {
  readTemplates,
  writeTemplates,
  resetTemplates,
  type MessageTemplate,
} from "@/lib/template-storage";
import type { DeepSeekImportMode, DeepSeekSharePreview } from "@/lib/import-types";
import type { AiProvider, UserSettings } from "@/lib/settings-types";
import type { Persona } from "@/lib/types";

const TABS = [
  { key: "profile", label: "资料" },
  { key: "ai", label: "AI" },
  { key: "persona", label: "人格" },
  { key: "template", label: "模板" },
  { key: "emoji", label: "表情" },
  { key: "import", label: "导入 / 导出" },
] as const;
type TabKey = (typeof TABS)[number]["key"];

const router = useRouter();
const username = ref(readUsername() ?? "admin");
const newUsername = ref(username.value);
const activeTab = ref<TabKey>("profile");
const loading = ref(true);
const saving = ref(false);
const uploading = ref(false);
const changingPassword = ref(false);
const changingUsername = ref(false);
const message = ref("");
const messageError = ref(false);
const usernameMessage = ref("");
const usernameError = ref(false);
const passwordMessage = ref("");
const passwordError = ref(false);
const form = ref<UserSettings | null>(null);
const currentPassword = ref("");
const newPassword = ref("");
const confirmPassword = ref("");
const fileInputRef = ref<HTMLInputElement | null>(null);
const avatarPreview = ref<string | null>(null);
const pendingAvatarFile = ref<File | null>(null);
const importUrl = ref("");
const importMode = ref<DeepSeekImportMode>("append");
const importPreview = ref<DeepSeekSharePreview | null>(null);
const previewingImport = ref(false);
const importing = ref(false);
const importFeedback = ref("");
const importError = ref(false);
const apiKeyDraft = ref("");

// emoji
const emojiDraft = ref("");
const savingEmoji = ref(false);
const emojiMessage = ref("");
const emojiError = ref(false);

// 模板
const templateDraft = ref<MessageTemplate[]>([]);
const selectedIndex = ref(-1);
const templateMessage = ref("");
const templateError = ref(false);

const selectedTemplate = computed(() =>
  selectedIndex.value >= 0 ? templateDraft.value[selectedIndex.value] ?? null : null,
);

// 人格
const personas = ref<Persona[]>([]);
const personaLoading = ref(false);
const selectedPersonaKey = ref<string>("none");
const creatingPersona = ref(false);
const savingPersona = ref(false);
const settingActivePersona = ref(false);
const personaMessage = ref("");
const personaError = ref(false);

const selectedPersona = computed(() =>
  selectedPersonaKey.value === "none" ? null : personas.value.find((p) => p.id === selectedPersonaKey.value) ?? null,
);

async function loadPersonas() {
  personaLoading.value = true;
  try {
    personas.value = await fetchPersonas();
  } catch {
    /* 人格列表非核心路径，静默失败 */
  } finally {
    personaLoading.value = false;
  }
}

async function handleAddPersona() {
  creatingPersona.value = true;
  personaMessage.value = "";
  personaError.value = false;
  try {
    const created = await createPersona({ name: "新人格", systemPrompt: "" });
    personas.value.push(created);
    selectedPersonaKey.value = created.id;
  } catch (err) {
    personaMessage.value = err instanceof Error ? err.message : "新增失败";
    personaError.value = true;
  } finally {
    creatingPersona.value = false;
  }
}

async function handleDeletePersona(id: string) {
  try {
    await deletePersona(id);
    personas.value = personas.value.filter((p) => p.id !== id);
    if (selectedPersonaKey.value === id) selectedPersonaKey.value = "none";
    if (form.value?.activePersonaId === id) form.value.activePersonaId = null;
  } catch (err) {
    personaMessage.value = err instanceof Error ? err.message : "删除失败";
    personaError.value = true;
  }
}

async function handleSavePersona() {
  if (!selectedPersona.value) return;
  savingPersona.value = true;
  personaMessage.value = "";
  personaError.value = false;
  try {
    const updated = await updatePersona(selectedPersona.value.id, {
      name: selectedPersona.value.name,
      icon: selectedPersona.value.icon,
      systemPrompt: selectedPersona.value.systemPrompt,
    });
    const index = personas.value.findIndex((p) => p.id === updated.id);
    if (index !== -1) personas.value[index] = updated;
    personaMessage.value = "人格已保存";
  } catch (err) {
    personaMessage.value = err instanceof Error ? err.message : "保存失败";
    personaError.value = true;
  } finally {
    savingPersona.value = false;
  }
}

async function handleSetActivePersona() {
  if (!form.value) return;
  settingActivePersona.value = true;
  personaMessage.value = "";
  personaError.value = false;
  try {
    const personaId = selectedPersonaKey.value === "none" ? null : selectedPersonaKey.value;
    form.value = await setActivePersona(personaId);
    personaMessage.value = "已切换使用中的人格";
  } catch (err) {
    personaMessage.value = err instanceof Error ? err.message : "切换失败";
    personaError.value = true;
  } finally {
    settingActivePersona.value = false;
  }
}

// 导出
const exportingFormat = ref<"md" | "json" | null>(null);
const exportError = ref("");

async function handleExport(format: "md" | "json") {
  exportingFormat.value = format;
  exportError.value = "";
  try {
    await exportMessages(format);
  } catch (err) {
    exportError.value = err instanceof Error ? err.message : "导出失败";
  } finally {
    exportingFormat.value = null;
  }
}

function clampSelection() {
  if (!templateDraft.value.length) {
    selectedIndex.value = -1;
  } else if (selectedIndex.value >= templateDraft.value.length) {
    selectedIndex.value = templateDraft.value.length - 1;
  }
}

onMounted(() => {
  emojiDraft.value = readEmojiList().join("\n");
  templateDraft.value = readTemplates();
  selectedIndex.value = templateDraft.value.length ? 0 : -1;
  void loadPersonas();
});

function addTemplate() {
  templateDraft.value.push({ name: "", content: "" });
  selectedIndex.value = templateDraft.value.length - 1;
}

function removeTemplate(index: number) {
  templateDraft.value.splice(index, 1);
  if (selectedIndex.value > index) selectedIndex.value -= 1;
  clampSelection();
}

function handleSaveTemplates() {
  templateMessage.value = "";
  templateError.value = false;
  const cleaned = templateDraft.value
    .map((t) => ({ name: t.name.trim(), content: t.content }))
    .filter((t) => t.name || t.content.trim());
  if (cleaned.some((t) => !t.name)) {
    templateMessage.value = "每个模板都需要一个名称";
    templateError.value = true;
    return;
  }
  writeTemplates(cleaned);
  templateDraft.value = cleaned;
  clampSelection();
  templateMessage.value = "模板已保存";
}

function handleResetTemplates() {
  resetTemplates();
  templateDraft.value = readTemplates();
  selectedIndex.value = templateDraft.value.length ? 0 : -1;
  templateMessage.value = "已恢复默认模板";
  templateError.value = false;
}

function handleSaveEmoji() {
  savingEmoji.value = true;
  emojiMessage.value = "";
  emojiError.value = false;
  try {
    const list = emojiDraft.value
      .split("\n")
      .map((line) => line.trim())
      .filter((line) => line.length > 0);
    if (list.length === 0) {
      emojiMessage.value = "至少需要一个 emoji";
      emojiError.value = true;
      return;
    }
    writeEmojiList(list);
    emojiMessage.value = "表情列表已保存";
    emojiError.value = false;
  } catch (err) {
    emojiMessage.value = err instanceof Error ? err.message : "保存失败";
    emojiError.value = true;
  } finally {
    savingEmoji.value = false;
  }
}

function handleResetEmoji() {
  resetEmojiList();
  emojiDraft.value = readEmojiList().join("\n");
  emojiMessage.value = "已恢复默认";
  emojiError.value = false;
}

const displayAvatarUrl = computed(() => avatarPreview.value || form.value?.avatarUrl || null);
const avatarFallback = computed(() => (form.value?.displayName || "我").slice(0, 1));

onMounted(async () => {
  try {
    const data = await fetchSettings();
    form.value = {
      ...data,
      aiThinking: data.aiThinking ?? true,
      avatarTransparent: data.avatarTransparent ?? false,
    };
    selectedPersonaKey.value = form.value.activePersonaId ?? "none";
    applyAvatarTransparency(form.value.avatarTransparent);
  } catch (err) {
    message.value = err instanceof Error ? err.message : "加载失败";
    messageError.value = true;
  } finally {
    loading.value = false;
  }
});

onUnmounted(() => {
  if (avatarPreview.value) URL.revokeObjectURL(avatarPreview.value);
});

function onAvatarTransparentChange() {
  if (form.value) applyAvatarTransparency(form.value.avatarTransparent);
}

function onProviderChange() {
  if (!form.value) return;
  const preset = AI_PRESETS[form.value.aiProvider as AiProvider];
  form.value.aiBaseUrl = preset.baseUrl;
  form.value.aiModel = preset.model;
}

function clearImportState() {
  importPreview.value = null;
  importFeedback.value = "";
  importError.value = false;
}

function formatPreviewTime(value: string) {
  return value.slice(0, 16).replace("T", " ");
}

function onAvatarSelect(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;
  if (avatarPreview.value) URL.revokeObjectURL(avatarPreview.value);
  pendingAvatarFile.value = file;
  avatarPreview.value = URL.createObjectURL(file);
  message.value = "";
  messageError.value = false;
}

function handleCancelAvatarPreview() {
  if (avatarPreview.value) URL.revokeObjectURL(avatarPreview.value);
  avatarPreview.value = null;
  pendingAvatarFile.value = null;
  if (fileInputRef.value) fileInputRef.value.value = "";
}

async function handleConfirmAvatar() {
  if (!pendingAvatarFile.value) return;
  uploading.value = true;
  message.value = "";
  messageError.value = false;
  try {
    form.value = await uploadAvatar(pendingAvatarFile.value);
    handleCancelAvatarPreview();
    message.value = "头像已更新";
    messageError.value = false;
  } catch (err) {
    message.value = err instanceof Error ? err.message : "上传失败";
    messageError.value = true;
  } finally {
    uploading.value = false;
  }
}

async function handleRemoveAvatar() {
  uploading.value = true;
  try {
    form.value = await removeAvatar();
    message.value = "已恢复默认头像";
    messageError.value = false;
  } catch (err) {
    message.value = err instanceof Error ? err.message : "删除头像失败";
    messageError.value = true;
  } finally {
    uploading.value = false;
  }
}

async function handleSave() {
  if (!form.value) return;
  saving.value = true;
  message.value = "";
  messageError.value = false;
  try {
    const payload: Parameters<typeof saveSettings>[0] = {
      displayName: form.value.displayName,
      aiProvider: form.value.aiProvider,
      aiModel: form.value.aiModel,
      aiBaseUrl: form.value.aiBaseUrl,
      aiSystemPrompt: form.value.aiSystemPrompt,
      aiThinking: form.value.aiThinking,
      avatarTransparent: form.value.avatarTransparent,
    };
    const nextKey = apiKeyDraft.value.trim();
    if (nextKey) payload.aiApiKey = nextKey;

    form.value = await saveSettings(payload);
    apiKeyDraft.value = "";
    message.value = "已保存";
    messageError.value = false;
  } catch (err) {
    message.value = err instanceof Error ? err.message : "保存失败";
    messageError.value = true;
  } finally {
    saving.value = false;
  }
}

async function handleChangeUsername() {
  usernameMessage.value = "";
  usernameError.value = false;
  const trimmed = newUsername.value.trim();
  if (trimmed.length < 2) {
    usernameMessage.value = "用户名至少 2 位";
    usernameError.value = true;
    return;
  }
  if (trimmed === username.value) return;
  changingUsername.value = true;
  try {
    const res = await changeUsername(trimmed);
    updateStoredUsername(res.username);
    username.value = res.username;
    newUsername.value = res.username;
    usernameMessage.value = "用户名已更新";
    usernameError.value = false;
  } catch (err) {
    usernameMessage.value = err instanceof Error ? err.message : "修改失败";
    usernameError.value = true;
  } finally {
    changingUsername.value = false;
  }
}

async function handleChangePassword() {
  passwordMessage.value = "";
  passwordError.value = false;
  if (!newPassword.value || newPassword.value.length < 6) {
    passwordMessage.value = "新密码至少 6 位";
    passwordError.value = true;
    return;
  }
  if (newPassword.value !== confirmPassword.value) {
    passwordMessage.value = "两次输入的新密码不一致";
    passwordError.value = true;
    return;
  }
  changingPassword.value = true;
  try {
    await changePassword(currentPassword.value, newPassword.value);
    clearAuthTokens();
    router.replace("/login");
  } catch (err) {
    passwordMessage.value = err instanceof Error ? err.message : "修改失败";
    passwordError.value = true;
  } finally {
    changingPassword.value = false;
  }
}

function handleLogout() {
  clearAuthTokens();
  router.replace("/login");
}

async function handleImportPreview() {
  if (!importUrl.value.trim()) return;
  previewingImport.value = true;
  importFeedback.value = "";
  importError.value = false;
  try {
    importPreview.value = await previewDeepSeekShare(importUrl.value.trim());
  } catch (err) {
    importPreview.value = null;
    importFeedback.value = err instanceof Error ? err.message : "预览失败";
    importError.value = true;
  } finally {
    previewingImport.value = false;
  }
}

async function handleImport() {
  if (!importUrl.value.trim()) return;
  if (importMode.value === "replace" && !window.confirm("将清空现有全部记录后再导入，确定继续？")) {
    return;
  }
  importing.value = true;
  importFeedback.value = "";
  importError.value = false;
  try {
    const result = await importDeepSeekShare(importUrl.value.trim(), importMode.value);
    importFeedback.value = `已导入 ${result.imported} 条：${result.title}`;
    importError.value = false;
  } catch (err) {
    importFeedback.value = err instanceof Error ? err.message : "导入失败";
    importError.value = true;
  } finally {
    importing.value = false;
  }
}
</script>
