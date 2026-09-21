<template>
  <div>
    <h2>Tickets</h2>

    <div class="filters">
      <select v-model="statusFilter" @change="fetchTickets(1)">
        <option value="">All statuses</option>
        <option value="open">Open</option>
        <option value="in_progress">In progress</option>
        <option value="resolved">Resolved</option>
        <option value="closed">Closed</option>
      </select>

      <select v-model="severityFilter" @change="fetchTickets(1)">
        <option value="">All severities</option>
        <option value="unclassified">Unclassified</option>
        <option value="low">Low</option>
        <option value="medium">Medium</option>
        <option value="high">High</option>
        <option value="critical">Critical</option>
      </select>

      <span class="live-dot" :class="{ connected: wsConnected }"></span>
      <span class="live-label">{{ wsConnected ? 'Live' : 'Reconnecting...' }}</span>
    </div>

    <table>
      <thead>
        <tr>
          <th>Title</th>
          <th>Severity</th>
          <th>Status</th>
          <th>AI Summary</th>
          <th>Created</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="t in tickets" :key="t.id" :class="'sev-' + t.severity">
          <td>{{ t.title }}</td>
          <td><span class="badge">{{ t.severity }}</span></td>
          <td>
            <select :value="t.status" @change="updateStatus(t, $event.target.value)">
              <option value="open">open</option>
              <option value="in_progress">in_progress</option>
              <option value="resolved">resolved</option>
              <option value="closed">closed</option>
            </select>
          </td>
          <td class="summary">{{ t.ai_summary || '(processing...)' }}</td>
          <td>{{ new Date(t.created_at).toLocaleString() }}</td>
        </tr>
        <tr v-if="tickets.length === 0">
          <td colspan="5" class="empty">No tickets yet. Try running seed_demo_data.py.</td>
        </tr>
      </tbody>
    </table>

    <div class="pagination">
      <button :disabled="page <= 1" @click="fetchTickets(page - 1)">Prev</button>
      <span>Page {{ page }} of {{ totalPages }}</span>
      <button :disabled="page >= totalPages" @click="fetchTickets(page + 1)">Next</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'

const tickets = ref([])
const page = ref(1)
const totalPages = ref(1)
const statusFilter = ref('')
const severityFilter = ref('')
const wsConnected = ref(false)
let socket = null

async function fetchTickets(newPage = 1) {
  page.value = newPage
  const params = { page: newPage, page_size: 10 }
  if (statusFilter.value) params.status = statusFilter.value
  if (severityFilter.value) params.severity = severityFilter.value

  const { data } = await axios.get('/api/tickets', { params })
  tickets.value = data.items
  totalPages.value = data.total_pages
}

async function updateStatus(ticket, newStatus) {
  await axios.patch(`/api/tickets/${ticket.id}`, { status: newStatus })
  ticket.status = newStatus
}

function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  socket = new WebSocket(`${protocol}://${window.location.hostname}:8000/ws/tickets`)
  socket.onopen = () => (wsConnected.value = true)
  socket.onclose = () => {
    wsConnected.value = false
    setTimeout(connectWebSocket, 3000) // simple reconnect
  }
  socket.onmessage = () => {
    // any ticket_created / ticket_updated event -> just refresh the current page
    fetchTickets(page.value)
  }
}

onMounted(() => {
  fetchTickets()
  connectWebSocket()
})

onUnmounted(() => {
  socket?.close()
})
</script>

<style scoped>
.filters { display: flex; gap: 0.75rem; align-items: center; margin-bottom: 1rem; }
table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; }
th, td { text-align: left; padding: 0.6rem 0.8rem; border-bottom: 1px solid #eee; font-size: 0.9rem; }
.badge { padding: 0.2rem 0.5rem; border-radius: 999px; background: #e5e7eb; font-size: 0.75rem; }
.sev-critical .badge { background: #fecaca; }
.sev-high .badge { background: #fed7aa; }
.sev-medium .badge { background: #fef08a; }
.sev-low .badge { background: #bbf7d0; }
.summary { color: #555; font-style: italic; max-width: 320px; }
.empty { text-align: center; color: #888; padding: 2rem; }
.pagination { display: flex; gap: 1rem; align-items: center; margin-top: 1rem; }
.live-dot { width: 8px; height: 8px; border-radius: 50%; background: #dc2626; display: inline-block; }
.live-dot.connected { background: #16a34a; }
.live-label { font-size: 0.8rem; color: #666; }
</style>
