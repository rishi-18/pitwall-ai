import axios from 'axios'

export const api = axios.create({

  baseURL:
    import.meta.env.VITE_API_BASE_URL ||
    'http://localhost:8000',

  timeout: 10000,

  headers: {
    'Content-Type': 'application/json',
  },
})


api.interceptors.request.use((config) => {

  const token =
    localStorage.getItem('access_token')

  if (token) {
    config.headers.Authorization =
      Bearer 
  }

  return config
})


api.interceptors.response.use(

  (res) => res,

  async (err) => {

    if (err.response?.status === 401) {

      localStorage.removeItem('access_token')

      window.location.href = '/login'
    }

    return Promise.reject(err)
  }
)


export const pitwall = {

  sessions: {

    list: (
      year = 2024,
      type = 'R'
    ) =>
      api.get('/v1/sessions/', {
        params: {
          year,
          session_type: type,
        },
      }),

  },

  standings: {

    drivers: (
      year = 2024
    ) =>
      api.get('/v1/standings/drivers', {
        params: { year },
      }),

  },

}
