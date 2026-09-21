import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import Login from '../views/Login.vue'
import Tickets from '../views/Tickets.vue'
import Analytics from '../views/Analytics.vue'

const routes = [
  { path: '/', redirect: '/tickets' },
  { path: '/login', name: 'login', component: Login },
  { path: '/tickets', name: 'tickets', component: Tickets, meta: { requiresAuth: true } },
  { path: '/analytics', name: 'analytics', component: Analytics, meta: { requiresAuth: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login' }
  }
})

export default router
