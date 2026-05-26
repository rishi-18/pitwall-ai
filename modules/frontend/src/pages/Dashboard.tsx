import React, { useEffect, useState } from 'react'
import TelemetryChart from '../components/charts/TelemetryChart'

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const SESSION_KEY = 9158
const DRIVER = 1  // Verstappen

interface DriverSummary {
  driver_number: number
  data_points: number
  avg_speed: number
  top_speed: number
  avg_throttle: number
}

export default function Dashboard() {
  const [summary, setSummary] = useState<DriverSummary[]>([])
  const [telemetry, setTelemetry] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedDriver, setSelectedDriver] = useState(DRIVER)

  useEffect(() => {
    fetch(`${API}/v1/sessions/telemetry/summary?session_key=${SESSION_KEY}`)
      .then(r => r.json())
      .then(d => setSummary(d.drivers || []))
      .catch(console.error)
  }, [])

  useEffect(() => {
    setLoading(true)
    fetch(`${API}/v1/sessions/${SESSION_KEY}/telemetry/${selectedDriver}?downsample=5`)
      .then(r => r.json())
      .then(d => {
        setTelemetry(d.telemetry || [])
        setLoading(false)
      })
      .catch(console.error)
  }, [selectedDriver])

  const driverNames: Record<number, string> = {
    1: 'Verstappen', 11: 'Perez', 16: 'Leclerc', 55: 'Sainz',
    44: 'Hamilton', 63: 'Russell', 4: 'Norris', 81: 'Piastri',
    14: 'Alonso', 18: 'Stroll', 10: 'Gasly', 31: 'Ocon',
    3: 'Ricciardo', 22: 'Tsunoda', 23: 'Albon', 2: 'Sargeant',
    77: 'Bottas', 24: 'Zhou', 20: 'Magnussen', 27: 'Hulkenberg',
  }

  return (
    <div style={{ padding: '1.5rem 2rem', background: '#0a0a0a', minHeight: '100vh' }}>

      {/* Header */}
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ color: '#e10600', fontFamily: 'monospace', fontSize: '1.25rem', margin: 0 }}>
          2024 BAHRAIN GRAND PRIX — RACE
        </h1>
        <p style={{ color: '#555', fontSize: '0.8rem', marginTop: '0.25rem' }}>
          Session 9158 · 20 drivers · 838,622 telemetry points
        </p>
      </div>

      {/* Driver stats grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
        gap: '0.5rem',
        marginBottom: '1.5rem'
      }}>
        {summary.map(d => (
          <div
            key={d.driver_number}
            onClick={() => setSelectedDriver(d.driver_number)}
            style={{
              background: selectedDriver === d.driver_number ? '#1a0000' : '#111',
              border: `1px solid ${selectedDriver === d.driver_number ? '#e10600' : '#222'}`,
              borderRadius: '6px',
              padding: '0.75rem',
              cursor: 'pointer',
              transition: 'all 0.15s',
            }}
          >
            <div style={{ color: selectedDriver === d.driver_number ? '#e10600' : '#fff', fontWeight: 'bold', fontSize: '0.875rem' }}>
              #{d.driver_number} {driverNames[d.driver_number] || ''}
            </div>
            <div style={{ color: '#666', fontSize: '0.75rem', marginTop: '0.25rem' }}>
              Avg: {d.avg_speed} km/h
            </div>
            <div style={{ color: '#666', fontSize: '0.75rem' }}>
              Top: {d.top_speed} km/h
            </div>
          </div>
        ))}
      </div>

      {/* Telemetry chart */}
      <div style={{ background: '#111', borderRadius: '8px', padding: '1rem', border: '1px solid #1a1a1a' }}>
        <div style={{ marginBottom: '0.75rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ color: '#fff', fontSize: '0.875rem', fontFamily: 'monospace', margin: 0 }}>
            TELEMETRY — #{selectedDriver} {driverNames[selectedDriver]}
          </h2>
          <span style={{ color: '#555', fontSize: '0.75rem' }}>
            {loading ? 'Loading...' : `${telemetry.length} points (1:5 downsample)`}
          </span>
        </div>
        {loading ? (
          <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#444' }}>
            Fetching telemetry...
          </div>
        ) : (
          <TelemetryChart data={telemetry} width={1100} height={300} />
        )}
      </div>

    </div>
  )
}