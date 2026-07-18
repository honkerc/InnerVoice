<template>
  <div class="settings-page">
    <main class="settings-main">
      <div class="settings-top">
        <button type="button" class="settings-back" title="返回聊天" @click="router.push('/')">
          <IconChevronLeft />
          <span>返回</span>
        </button>

        <nav class="settings-tabs" aria-label="设置分类">
          <button v-for="tab in tabs" :key="tab.id" type="button" class="settings-tab"
            :class="{ 'settings-tab--active': activeTab === tab.id }" @click="activeTab = tab.id">
            {{ tab.label }}
          </button>
        </nav>
      </div>

      <SettingsSkeleton v-if="loading" />

      <div v-else-if="form" class="settings-panel">
        <section v-show="activeTab === 'profile'" class="settings-card">
          <div class="settings-card__grid">
            <div class="settings-card__col settings-card__col--profile">
              <h2 class="settings-card__title">个人资料</h2>
              <p class="settings-card__desc">头像与名称会显示在消息旁。</p>
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
              <label class="field-checkbox" style="margin-top: 12px">
                <input v-model="form.avatarTransparent" type="checkbox" class="field-checkbox__input" />
                <span>
                  <span class="field-checkbox__text">透明背景头像</span>
                  <span class="field-checkbox__hint">适用于 PNG 透明头像</span>
                </span>
              </label>
            </div>

            <div class="settings-card__col settings-card__col--account">
              <h2 class="settings-card__title">账户</h2>
              <p class="settings-card__desc">
                当前登录 <strong>{{ username }}</strong>，修改密码后需重新登录。
              </p>
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
                  <button class="settings-btn settings-btn--ghost" type="button" @click="handleLogout">
                    退出登录
                  </button>
                </div>
              </form>
            </div>
          </div>

          <div class="settings-save-bar">
            <p v-if="message && activeTab === 'profile'"
              :class="['settings-message', messageError ? 'settings-message--error' : 'settings-message--ok']">
              {{ message }}
            </p>
            <button class="settings-btn settings-btn--primary settings-btn--wide" type="button" :disabled="saving"
              @click="handleSave">
              {{ saving ? "保存中…" : "保存设置" }}
            </button>
          </div>
        </section>

        <section v-show="activeTab === 'ai'" class="settings-section">
          <h2 class="settings-section__title">AI</h2>
          <p class="settings-section__desc">输入 @ai 或开启工具栏 AI 按钮时调用。</p>
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
                {{
                  form.hasApiKey
                    ? "已配置 Key，仅提交到服务端保存，不会留在浏览器"
                    : "仅提交到服务端保存，不会留在浏览器"
                }}
              </span>
            </label>
            <label v-if="form.aiProvider === 'deepseek'" class="field-checkbox">
              <input v-model="form.aiThinking" class="field-checkbox__input" type="checkbox" />
              <span class="field-checkbox__text">开启思考模式</span>
              <span class="field-checkbox__hint">reasoning_effort=high</span>
            </label>
            <label class="field">
              <span class="field__label">系统提示词</span>
              <textarea v-model="form.aiSystemPrompt" class="field-input field-textarea" rows="8"
                placeholder="你是写作与思考辅助工具，帮助用户整理自己写下的记录…" />
              <span class="field__hint">定义 AI 人设与语气；DeepSeek 风格排版规则会自动附加</span>
            </label>
          </div>

          <div class="settings-save-bar">
            <p v-if="message && activeTab === 'ai'"
              :class="['settings-message', messageError ? 'settings-message--error' : 'settings-message--ok']">
              {{ message }}
            </p>
            <button class="settings-btn settings-btn--primary settings-btn--wide" type="button" :disabled="saving"
              @click="handleSave">
              {{ saving ? "保存中…" : "保存设置" }}
            </button>
          </div>
        </section>

        <section v-show="activeTab === 'emoji'" class="settings-card">
          <h2 class="settings-card__title">表情列表</h2>
          <p class="settings-card__desc">每行一个 emoji，修改后保存即可在聊天中使用。</p>
          <div class="settings-fields">
            <label class="field">
              <textarea v-model="emojiDraft" class="field-input field-textarea" rows="8" />
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

        <section v-show="activeTab === 'import'" class="settings-card">
          <h2 class="settings-card__title">导入 DeepSeek 分享</h2>
          <p class="settings-card__desc">
            粘贴 chat.deepseek.com/share/... 链接，按原时间顺序导入你与 AI 的对话。
          </p>
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
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";
import SettingsSkeleton from "@/components/SettingsSkeleton.vue";
import { IconChevronLeft } from "@/components/icons";
import {
  AI_PRESETS,
  AI_PROVIDER_OPTIONS,
  DEEPSEEK_MODEL_OPTIONS,
} from "@/lib/ai-presets";
import {
  changePassword,
  fetchSettings,
  importDeepSeekShare,
  previewDeepSeekShare,
  removeAvatar,
  saveSettings,
  uploadAvatar,
} from "@/lib/api";
import { clearAuthTokens, readUsername } from "@/lib/auth";
import { readEmojiList, writeEmojiList, resetEmojiList } from "@/lib/emoji-storage";
import type { DeepSeekImportMode, DeepSeekSharePreview } from "@/lib/import-types";
import type { AiProvider, UserSettings } from "@/lib/settings-types";

type SettingsTab = "profile" | "ai" | "emoji" | "import";

const tabs: { id: SettingsTab; label: string }[] = [
  { id: "profile", label: "个人资料" },
  { id: "ai", label: "AI" },
  { id: "emoji", label: "表情" },
  { id: "import", label: "导入" },
];

const router = useRouter();
const username = readUsername() ?? "admin";
const activeTab = ref<SettingsTab>("profile");
const loading = ref(true);
const saving = ref(false);
const uploading = ref(false);
const changingPassword = ref(false);
const message = ref("");
const messageError = ref(false);
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

const emojiDraft = ref("");
const savingEmoji = ref(false);
const emojiMessage = ref("");
const emojiError = ref(false);

onMounted(() => {
  emojiDraft.value = readEmojiList().join("\n");
});

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
    form.value = { ...data, aiThinking: data.aiThinking ?? true };
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
