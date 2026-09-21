<template>
  <div ref="chartEl" class="d3-chart"></div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  data: { type: Array, default: () => [] }, // [{ date: '2026-09-01', count: 3 }, ...]
})

const chartEl = ref(null)

function render() {
  const el = chartEl.value
  if (!el) return
  el.innerHTML = ''

  const width = el.clientWidth || 600
  const height = 260
  const margin = { top: 20, right: 20, bottom: 30, left: 40 }

  const svg = d3.select(el).append('svg').attr('width', width).attr('height', height)

  const data = props.data.length ? props.data : [{ date: 'no data', count: 0 }]

  const x = d3
    .scaleBand()
    .domain(data.map((d) => d.date))
    .range([margin.left, width - margin.right])
    .padding(0.3)

  const y = d3
    .scaleLinear()
    .domain([0, d3.max(data, (d) => d.count) || 1])
    .nice()
    .range([height - margin.bottom, margin.top])

  svg
    .append('g')
    .attr('transform', `translate(0,${height - margin.bottom})`)
    .call(d3.axisBottom(x).tickFormat((d) => d.slice(5))) // show MM-DD
    .selectAll('text')
    .attr('transform', 'rotate(-40)')
    .style('text-anchor', 'end')
    .style('font-size', '10px')

  svg.append('g').attr('transform', `translate(${margin.left},0)`).call(d3.axisLeft(y).ticks(5))

  const tooltip = d3
    .select(el)
    .append('div')
    .style('position', 'absolute')
    .style('background', '#1e1f26')
    .style('color', '#fff')
    .style('padding', '4px 8px')
    .style('border-radius', '4px')
    .style('font-size', '12px')
    .style('pointer-events', 'none')
    .style('opacity', 0)

  svg
    .append('g')
    .selectAll('rect')
    .data(data)
    .join('rect')
    .attr('x', (d) => x(d.date))
    .attr('y', (d) => y(d.count))
    .attr('width', x.bandwidth())
    .attr('height', (d) => height - margin.bottom - y(d.count))
    .attr('fill', '#2563eb')
    .attr('rx', 3)
    .on('mouseover', function (event, d) {
      d3.select(this).attr('fill', '#1d4ed8')
      tooltip.style('opacity', 1).text(`${d.date}: ${d.count} ticket(s)`)
    })
    .on('mousemove', (event) => {
      const [mx, my] = d3.pointer(event, el)
      tooltip.style('left', mx + 10 + 'px').style('top', my - 10 + 'px')
    })
    .on('mouseout', function () {
      d3.select(this).attr('fill', '#2563eb')
      tooltip.style('opacity', 0)
    })
}

onMounted(render)
watch(() => props.data, render, { deep: true })
</script>

<style scoped>
.d3-chart { position: relative; width: 100%; }
</style>
