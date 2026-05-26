import React, { useEffect, useState } from 'react'

const API = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface DriverStanding {
  position: string
  driver: string
  driver_id: string
  nationality: string
  team: string
  points: number
  wins: number
}

interface ConstructorStanding {
  position: string
  team: string
  nationality: string
  points: number
  wins: number
}

const TEAM_COLORS: Record<string, string> = {
  'Red Bull': '#3671C6',
  'Ferrari': '#E8002D',
  'Mercedes': '#27F4D2',
  'McLaren': '#FF8000',
  'Aston Martin': '#229971',
  'Alpine F1 Team': '#FF87BC',
  'RB F1 Team': '#6692FF',
  'Williams': '#64C4FF',
  'Haas F1 Team': '#B6BABD',
  'Sauber': '#52E252',
}

export default function Standings() {
  const [drivers, setDrivers] = useState<DriverStanding[]>([])
  const [constructors, setConstructors] = useState<ConstructorStanding[]>([])
  const [round, setRound] = useState(3)
  const [tab, setTab] = useState<'drivers' | 'constructors'>('drivers')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      fetch(`${API}/v1/standings/drivers?year=2024&round_number=${round}`).then(r => r.json()),
      fetch(`${API}/v1/standings/constructors?year=2024&round_number=${round}`).then(r => r.json()),
    ]).then(([d, c]) => {
      setDrivers(d.standings || [])
      setConstructors(c.standings || [])
      setLoading(false)
    }).catch(console.error)
  }, [round])

  const maxPoints = drivers[0]?.points || 1

  return (
    <div style={{ padding: '1.5rem 2rem', background: '#0a0a0a', minHeight: '100vh' }}>

      {/* Header */}
      <div style={{ marginBottom: '1.5rem', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
        <div>
          <h1 style={{ color: '#e10600', fontFamily: 'monospace', fontSize: '1.25rem', margin: 0 }}>
            2024 CHAMPIONSHIP STANDINGS
          </h1>
          <p style={{ color: '#555', fontSize: '0.8rem', marginTop: '0.25rem' }}>
            Live data via Jolpica API
          </p>
        </div>

        {/* Round selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{ color: '#666', fontSize: '0.8rem' }}>After Round</span>
          <select
            value={round}
            onChange={e => setRound(Number(e.target.value))}
            style={{
              background: '#111', border: '1px solid #333', color: 'white',
              padding: '0.4rem 0.75rem', borderRadius: '4px', fontSize: '0.875rem'
            }}
          >
            {Array.from({ length: 24 }, (_, i) => i + 1).map(r => (
              <option key={r} value={r}>Round {r}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '0', marginBottom: '1rem', borderBottom: '1px solid #222' }}>
        {(['drivers', 'constructors'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              background: 'none', border: 'none',
              borderBottom: tab === t ? '2px solid #e10600' : '2px solid transparent',
              color: tab === t ? '#fff' : '#555',
              padding: '0.6rem 1.5rem',
              cursor: 'pointer', fontSize: '0.8rem',
              textTransform: 'uppercase', letterSpacing: '0.1em',
              fontFamily: 'monospace',
            }}
          >
            {t}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ color: '#444', padding: '2rem', textAlign: 'center' }}>Loading standings...</div>
      ) : tab === 'drivers' ? (
        <div>
          {drivers.map((d, i) => (
            <div key={d.driver_id} style={{
              display: 'grid',
              gridTemplateColumns: '2.5rem 3rem 1fr 1fr 1fr auto',
              alignItems: 'center',
              gap: '1rem',
              padding: '0.75rem 1rem',
              marginBottom: '0.375rem',
              background: i === 0 ? '#0d0d0d' : '#0a0a0a',
              border: '1px solid #161616',
              borderLeft: `3px solid ${TEAM_COLORS[d.team] || '#333'}`,
              borderRadius: '4px',
            }}>
              <span style={{ color: '#555', fontSize: '0.8rem', fontFamily: 'monospace' }}>
                P{d.position}
              </span>
              <span style={{
                color: '#fff', fontWeight: 'bold', fontSize: '0.875rem',
                fontFamily: 'monospace'
              }}>
                {d.driver}
              </span>
              <span style={{ color: '#666', fontSize: '0.8rem' }}>{d.team}</span>
              <span style={{ color: '#666', fontSize: '0.8rem' }}>{d.nationality}</span>

              {/* Points bar */}
              <div style={{ position: 'relative', height: '6px', background: '#1a1a1a', borderRadius: '3px' }}>
                <div style={{
                  position: 'absolute', left: 0, top: 0, height: '100%',
                  width: `${(d.points / maxPoints) * 100}%`,
                  background: TEAM_COLORS[d.team] || '#e10600',
                  borderRadius: '3px',
                  transition: 'width 0.3s ease',
                }} />
              </div>

              <span style={{
                color: '#fff', fontWeight: 'bold', fontSize: '0.875rem',
                fontFamily: 'monospace', textAlign: 'right', minWidth: '4rem'
              }}>
                {d.points} pts
              </span>
            </div>
          ))}
        </div>
      ) : (
        <div>
          {constructors.map((c, i) => (
            <div key={c.team} style={{
              display: 'grid',
              gridTemplateColumns: '2.5rem 1fr 1fr auto',
              alignItems: 'center',
              gap: '1rem',
              padding: '0.75rem 1rem',
              marginBottom: '0.375rem',
              background: '#0a0a0a',
              border: '1px solid #161616',
              borderLeft: `3px solid ${TEAM_COLORS[c.team] || '#333'}`,
              borderRadius: '4px',
            }}>
              <span style={{ color: '#555', fontSize: '0.8rem', fontFamily: 'monospace' }}>
                P{c.position}
              </span>
              <span style={{ color: '#fff', fontWeight: 'bold', fontSize: '0.875rem' }}>
                {c.team}
              </span>
              <div style={{ position: 'relative', height: '6px', background: '#1a1a1a', borderRadius: '3px' }}>
                <div style={{
                  position: 'absolute', left: 0, top: 0, height: '100%',
                  width: `${(c.points / (constructors[0]?.points || 1)) * 100}%`,
                  background: TEAM_COLORS[c.team] || '#e10600',
                  borderRadius: '3px',
                }} />
              </div>
              <span style={{
                color: '#fff', fontWeight: 'bold', fontSize: '0.875rem',
                fontFamily: 'monospace', textAlign: 'right', minWidth: '4rem'
              }}>
                {c.points} pts
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}