<template>
  <div>
    <h2>Analytics</h2>

    <div class="cards" v-if="summary">
      <div class="card">
        <div class="card-label">Total tickets</div>
        <div class="card-value">{{ summary.total_tickets }}</div>
      </div>
      <div class="card">
        <div class="card-label">Open / In progress</div>
        <div class="card-value">{{ summary.open_tickets }}</div>
      </div>
      <div class="card">
        <div class="card-label">Avg resolution time</div>
        <div class="card-value">
          {{ summary.avg_resolution_hours != null ? summary.avg_resolution_hours + 'h' : '—' }}
        </div>
      </div>
      <div class="card">
        <div class="card-label">Avg AI confidence</div>
        <div class="card-value">
          {{ summary.avg_ai_confidence != null ? Math.round(summary.avg_ai_confidence * 100) + '%' : '—' }}
        </div>
      </div>
    </div>

    <div class="charts" v-if="summary">
      <div class="chart-box">
        <h3>Tickets by day (D3)</h3>
        <D3VolumeChart :data="summary.volume_by_day" />
      </div>
      <div class="chart-box">
        <h3>Severity breakdown</h3>
        <Pie :data="pieData" :options="{ plugins: { legend: { position: 'bottom' } } }" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import { Pie } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import D3VolumeChart from '../components/charts/D3VolumeChart.vue'

ChartJS.register(ArcElement, Tooltip, Legend)

const summary = ref(null)

const SEVERITY_COLORS = {
  unclassified: '#9ca3af',
  low: '#22c55e',
  medium: '#eab308',
  high: '#f97316',
  critical: '#ef4444',
}

const pieData = computed(() => {
  if (!summary.value) return { labels: [], datasets: [] }
  const rows = summary.value.severity_breakdown
  return {
    labels: rows.map((r) => r.severity),
    datasets: [
      {
        data: rows.map((r) => r.count),
        backgroundColor: rows.map((r) => SEVERITY_COLORS[r.severity] || '#ccc'),
      },
    ],
  }
})

onMounted(async () => {
  const { data } = await axios.get('/api/analytics/summary', { params: { days: 14 } })
  summary.value = data
})
</script>

<style scoped>
.cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 2rem; }
.card { background: #fff; border-radius: 10px; padding: 1rem; box-shadow: 0 1px 6px rgba(0,0,0,0.06); }
.card-label { font-size: 0.8rem; color: #888; }
.card-value { font-size: 1.6rem; font-weight: 700; margin-top: 0.25rem; }
.charts { display: grid; grid-template-columns: 1.3fr 1fr; gap: 1.5rem; }
.chart-box { background: #fff; border-radius: 10px; padding: 1rem; box-shadow: 0 1px 6px rgba(0,0,0,0.06); }
</style>
