import { defineStore } from "pinia";
import { computed, ref } from "vue";
import { authApi } from "@/api/modules";
import type { UserProfile } from "@/api/types";

const ACCESS_KEY = "jobpilot_access_token";
const REFRESH_KEY = "jobpilot_refresh_token";

export const useUserStore = defineStore("user", () => {
  const accessToken = ref(localStorage.getItem(ACCESS_KEY) || "");
  const refreshToken = ref(localStorage.getItem(REFRESH_KEY) || "");
  const profile = ref<UserProfile | null>(null);
  const isAuthenticated = computed(() => Boolean(accessToken.value));
  const isAdmin = computed(() => Boolean(profile.value?.is_superuser));

  function setTokens(access: string, refresh: string) {
    accessToken.value = access;
    refreshToken.value = refresh;
    localStorage.setItem(ACCESS_KEY, access);
    localStorage.setItem(REFRESH_KEY, refresh);
  }

  function clearSession() {
    accessToken.value = "";
    refreshToken.value = "";
    profile.value = null;
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  }

  async function login(username: string, password: string) {
    const tokens = await authApi.login({ username, password });
    setTokens(tokens.access_token, tokens.refresh_token);
    await fetchProfile();
  }

  async function register(username: string, email: string, password: string) {
    await authApi.register({ username, email, password });
    await login(username, password);
  }

  async function fetchProfile() {
    if (!accessToken.value) {
      return null;
    }

    profile.value = await authApi.me();
    return profile.value;
  }

  async function logout() {
    try {
      await authApi.logout();
    } finally {
      clearSession();
    }
  }

  return {
    accessToken,
    refreshToken,
    profile,
    isAuthenticated,
    isAdmin,
    setTokens,
    clearSession,
    login,
    register,
    fetchProfile,
    logout
  };
});
