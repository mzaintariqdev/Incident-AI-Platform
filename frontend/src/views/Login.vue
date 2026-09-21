<template>
  <div class="auth-box">
    <h2>{{ isRegister ? 'Create account' : 'Log in' }}</h2>
    <form @submit.prevent="submit">
      <input v-model="email" type="email" placeholder="Email" required />
      <input v-model="password" type="password" placeholder="Password" required minlength="8" />
      <button type="submit">{{ isRegister ? 'Register' : 'Log in' }}</button>
    </form>
    <p class="error" v-if="error">{{ error }}</p>
    <button class="link-btn" @click="isRegister = !isRegister">
      {{ isRegister ? 'Already have an account? Log in' : "No account? Register" }}
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const email = ref('')
const password = ref('')
const error = ref('')
const isRegister = ref(false)

const auth = useAuthStore()
const router = useRouter()

async function submit() {
  error.value = ''
  try {
    if (isRegister.value) {
      await auth.register(email.value, password.value)
      isRegister.value = false
      error.value = 'Account created — now log in.'
      return
    }
    await auth.login(email.value, password.value)
    router.push('/tickets')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Something went wrong'
  }
}
</script>

<style scoped>
.auth-box { max-width: 360px; margin: 4rem auto; background: #fff; padding: 2rem; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); }
form { display: flex; flex-direction: column; gap: 0.75rem; }
input { padding: 0.6rem; border: 1px solid #ddd; border-radius: 6px; }
button { padding: 0.6rem; border-radius: 6px; border: none; background: #2563eb; color: #fff; cursor: pointer; }
.link-btn { background: none; color: #2563eb; margin-top: 1rem; }
.error { color: #dc2626; font-size: 0.9rem; }
</style>
