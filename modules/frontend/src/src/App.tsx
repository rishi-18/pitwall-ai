import React from 'react'
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import LiveRace from './pages/LiveRace'
import RaceAnalyst from './pages/RaceAnalyst'
import Standings from './pages/Standings'

function NavLink({ to, children }: { to: string, children: React.ReactNode }) {
  const location = useLocation()
  const active = location.pathname === to
  return (
    <Link to={to} style={{
      color: active ? '#fff' : '#666',
      textDecoration: 'none',
      fontSize: '0.8rem',
      textTransform: 'uppercase',
      letterSpacing: '0.08em',
      fontFamily: 'monospace',
      borderBottom: active ? '2px solid #e10600' : '2px solid transparent',
      paddingBottom: '2px',
    }}>
      {children}
    </Link>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <nav style={{
        background: '#0d0d0d',
        borderBottom: '1px solid #1a1a1a',
        padding: '0.875rem 2rem',
        display: 'flex',
        gap: '2rem',
        alignItems: 'center',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}>
        <span style={{
          color: '#e10600', fontWeight: 'bold',
          fontSize: '0.875rem', letterSpacing: '0.15em',
          fontFamily: 'monospace', marginRight: '1rem'
        }}>
          PITWALL AI
        </span>
        <NavLink to="/">Dashboard</NavLink>
        <NavLink to="/standings">Standings</NavLink>
        <NavLink to="/live">Live Race</NavLink>
        <NavLink to="/analyst">Race Analyst</NavLink>
      </nav>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/standings" element={<Standings />} />
        <Route path="/live" element={<LiveRace />} />
        <Route path="/analyst" element={<RaceAnalyst />} />
      </Routes>
    </BrowserRouter>
  )
}