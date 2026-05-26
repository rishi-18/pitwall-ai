import React, { useState } from 'react'

import {
  useLiveStore
} from '../store'


export default function LiveRace() {

  const {
    isConnected,
    liveEvents,
    connectToSession,
    disconnect,
  } = useLiveStore()

  const [sessionKey, setSessionKey] =
    useState('')

  return (

    <div
      style={{
        padding: '2rem',
        color: 'white',
        background: '#0a0a0a',
        minHeight: '100vh',
      }}
    >

      <h2
        style={{
          fontFamily: 'monospace',
          color: '#e10600',
        }}
      >
        LIVE RACE FEED
      </h2>

    </div>
  )
}
