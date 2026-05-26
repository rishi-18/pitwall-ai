import React, { useEffect, useRef } from 'react'
import * as d3 from 'd3'

interface TelemetryPoint {
  timestamp: string
  speed: number
  throttle: number
  brake: boolean
}

interface Props {
  data: TelemetryPoint[]
  width?: number
  height?: number
}

export default function TelemetryChart({ data, width = 900, height = 300 }: Props) {
  const svgRef = useRef<SVGSVGElement>(null)

  useEffect(() => {
    if (!data.length || !svgRef.current) return

    const margin = { top: 20, right: 30, bottom: 40, left: 50 }
    const innerWidth = width - margin.left - margin.right
    const innerHeight = height - margin.top - margin.bottom

    // Clear previous render
    d3.select(svgRef.current).selectAll('*').remove()

    const svg = d3.select(svgRef.current)
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    // Parse timestamps
    const parsed = data.map((d, i) => ({
      ...d,
      index: i,
      speed: d.speed ?? 0,
      throttle: d.throttle ?? 0,
    }))

    // Scales
    const xScale = d3.scaleLinear()
      .domain([0, parsed.length - 1])
      .range([0, innerWidth])

    const yScale = d3.scaleLinear()
      .domain([0, 350])
      .range([innerHeight, 0])

    const throttleScale = d3.scaleLinear()
      .domain([0, 110])
      .range([innerHeight, 0])

    // Grid lines
    svg.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(yScale).tickSize(-innerWidth).tickFormat(() => ''))
      .selectAll('line')
      .style('stroke', '#1a1a1a')
      .style('stroke-width', '1px')

    svg.select('.grid .domain').remove()

    // Speed line
    const speedLine = d3.line<typeof parsed[0]>()
      .x(d => xScale(d.index))
      .y(d => yScale(d.speed))
      .curve(d3.curveMonotoneX)

    svg.append('path')
      .datum(parsed)
      .attr('fill', 'none')
      .attr('stroke', '#e10600')
      .attr('stroke-width', 1.5)
      .attr('d', speedLine)

    // Throttle line
    const throttleLine = d3.line<typeof parsed[0]>()
      .x(d => xScale(d.index))
      .y(d => throttleScale(d.throttle))
      .curve(d3.curveMonotoneX)

    svg.append('path')
      .datum(parsed)
      .attr('fill', 'none')
      .attr('stroke', '#00ff88')
      .attr('stroke-width', 1)
      .attr('opacity', 0.7)
      .attr('d', throttleLine)

    // Brake indicators
    parsed.filter(d => d.brake).forEach(d => {
      svg.append('line')
        .attr('x1', xScale(d.index))
        .attr('x2', xScale(d.index))
        .attr('y1', 0)
        .attr('y2', innerHeight)
        .attr('stroke', '#ff6b00')
        .attr('stroke-width', 0.5)
        .attr('opacity', 0.3)
    })

    // Axes
    svg.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(d3.axisBottom(xScale).ticks(10))
      .selectAll('text, line, path')
      .style('stroke', '#444')
      .style('fill', '#666')

    svg.append('g')
      .call(d3.axisLeft(yScale).ticks(6))
      .selectAll('text, line, path')
      .style('stroke', '#444')
      .style('fill', '#666')

    // Labels
    svg.append('text')
      .attr('x', -innerHeight / 2)
      .attr('y', -35)
      .attr('transform', 'rotate(-90)')
      .attr('text-anchor', 'middle')
      .style('fill', '#666')
      .style('font-size', '11px')
      .text('Speed (km/h)')

    // Legend
    const legend = svg.append('g').attr('transform', `translate(${innerWidth - 150}, 0)`)
    legend.append('line').attr('x1', 0).attr('x2', 20).attr('y1', 5).attr('y2', 5)
      .attr('stroke', '#e10600').attr('stroke-width', 2)
    legend.append('text').attr('x', 25).attr('y', 9)
      .style('fill', '#999').style('font-size', '11px').text('Speed')
    legend.append('line').attr('x1', 0).attr('x2', 20).attr('y1', 22).attr('y2', 22)
      .attr('stroke', '#00ff88').attr('stroke-width', 1.5)
    legend.append('text').attr('x', 25).attr('y', 26)
      .style('fill', '#999').style('font-size', '11px').text('Throttle %')
    legend.append('line').attr('x1', 0).attr('x2', 20).attr('y1', 39).attr('y2', 39)
      .attr('stroke', '#ff6b00').attr('stroke-width', 1.5)
    legend.append('text').attr('x', 25).attr('y', 43)
      .style('fill', '#999').style('font-size', '11px').text('Brake zones')

  }, [data, width, height])

  return (
    <svg ref={svgRef} style={{ background: '#0d0d0d', borderRadius: '8px' }} />
  )
}