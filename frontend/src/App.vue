<template>
  <div id="layout">
    <nav v-if="auth.isAuthenticated">
      <router-link to="/tickets">Tickets</router-link>
      <router-link to="/analytics">Analytics</router-link>
      <button @click="handleLogout">Log out</button>
    </nav>
    <main>
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()
const router = useRouter()

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<style>
body { font-family: system-ui, sans-serif; margin: 0; background: #f7f8fa; }
nav { display: flex; gap: 1rem; align-items: center; padding: 1rem 2rem; background: #1e1f26; }
nav a { color: #fff; text-decoration: none; font-weight: 500; }
nav a.router-link-active { color: #7dd3fc; }
nav button { margin-left: auto; }
main { padding: 2rem; max-width: 1100px; margin: 0 auto; }
</style>
