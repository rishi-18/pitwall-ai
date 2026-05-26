
/// <reference types="vite/client" />
import { create } from 'zustand'

interface SessionState {
  selectedSessionKey: number | null
  selectedDriver: number | null

  setSession: (key: number) => void
  setDriver: (num: number) => void
}

interface LiveState {
  isConnected: boolean
  liveEvents: any[]
  wsRef: WebSocket | null

  connectToSession: (
    sessionKey: number
  ) => void

  disconnect: () => void

  pushEvent: (
    event: any
  ) => void
}

interface UIState {
  sidebarOpen: boolean
  toggleSidebar: () => void
  theme: 'dark' | 'light'
}


export const useSessionStore =
create<SessionState>((set) => ({

  selectedSessionKey: null,
  selectedDriver: null,

  setSession: (key) =>
    set({
      selectedSessionKey: key
    }),

  setDriver: (num) =>
    set({
      selectedDriver: num
    }),

}))


export const useLiveStore =
create<LiveState>((set, get) => ({

  isConnected: false,
  liveEvents: [],
  wsRef: null,

  connectToSession: (
    sessionKey: number
  ) => {

    const wsUrl =
      `${import.meta.env.VITE_WS_BASE_URL}/ws/live/`

    const ws = new WebSocket(wsUrl)

    ws.onopen = () =>
      set({ isConnected: true })

    ws.onclose = () =>
      set({
        isConnected: false,
        wsRef: null
      })

    ws.onmessage = (e) => {

      const event = JSON.parse(e.data)

      get().pushEvent(event)
    }

    set({ wsRef: ws })
  },

  disconnect: () => {

    get().wsRef?.close()

    set({
      isConnected: false,
      wsRef: null,
      liveEvents: [],
    })
  },

  pushEvent: (event) =>
    set((s) => ({
      liveEvents: [
        ...s.liveEvents.slice(-200),
        event,
      ],
    })),

}))


export const useUIStore =
create<UIState>((set) => ({

  sidebarOpen: true,

  toggleSidebar: () =>
    set((s) => ({
      sidebarOpen: !s.sidebarOpen
    })),

  theme: 'dark',

}))
