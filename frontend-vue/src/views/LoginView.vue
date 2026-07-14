<template>
  <div class="login-page">
    <form class="login-card" @submit.prevent="submit">
      <h1>与神对话</h1>
      <p class="hint">登录后开始记录</p>
      <div class="field">
        <label>用户名</label>
        <input v-model="username" autocomplete="username" />
      </div>
      <div class="field">
        <label>密码</label>
        <input v-model="password" type="password" autocomplete="current-password" />
      </div>
      <p v-if="error" class="form-error">{{ error }}</p>
      <button class="btn btn-primary" type="submit" :disabled="loading" style="width: 100%">
        {{ loading ? "登录中…" : "登录" }}
      </button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { login } from "@/lib/api";

const router = useRouter();
const username = ref("admin");
const password = ref("");
const loading = ref(false);
const error = ref("");

async function submit() {
  loading.value = true;
  error.value = "";
  try {
    await login(username.value.trim(), password.value);
    await router.replace("/");
  } catch (err) {
    error.value = err instanceof Error ? err.message : "登录失败";
  } finally {
    loading.value = false;
  }
}
</script>
