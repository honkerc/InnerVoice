import { createRouter, createWebHistory } from "vue-router";
import { isAuthenticated } from "@/lib/auth";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: () => import("@/views/LoginView.vue"), meta: { public: true } },
    { path: "/", component: () => import("@/views/ChatView.vue") },
    { path: "/settings", component: () => import("@/views/SettingsView.vue") },
  ],
});

router.beforeEach((to) => {
  if (to.meta.public) {
    if (isAuthenticated() && to.path === "/login") return "/";
    return true;
  }
  if (!isAuthenticated()) return "/login";
  return true;
});

export default router;
