import { defineStore } from 'pinia'
import api from '../utils/api'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null')
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    username: (state) => state.user?.username || '',
    cardGold: (state) => state.user?.card_gold || 0,
    freeDraws: (state) => state.user?.free_draws || 0,
    rating: (state) => state.user?.rating || 0
  },

  actions: {
    async login(username, password) {
      try {
        const res = await api.post('/login', { username, password })
        if (res.data.success) {
          this.token = res.data.token
          this.user = res.data.user
          localStorage.setItem('token', this.token)
          localStorage.setItem('user', JSON.stringify(this.user))
          return true
        }
        return false
      } catch (e) {
        throw e.response?.data?.detail || '登录失败'
      }
    },

    async register(username, password) {
      try {
        const res = await api.post('/register', { username, password })
        if (res.data.success) {
          this.token = res.data.token
          this.user = res.data.user
          localStorage.setItem('token', this.token)
          localStorage.setItem('user', JSON.stringify(this.user))
          return true
        }
        return false
      } catch (e) {
        throw e.response?.data?.detail || '注册失败'
      }
    },

    async fetchUserInfo() {
      if (!this.token) {
        this.logout()
        return null
      }
      try {
        const res = await api.get('/user')
        this.user = res.data
        localStorage.setItem('user', JSON.stringify(this.user))
        return res.data
      } catch (e) {
        // api.js 的 401 拦截器已经处理了跳转和 token 清除
        // 这里只需要清空本地状态
        if (e.response?.status === 401) {
          this.logout()
        }
        throw e
      }
    },

    updateGold(amount) {
      if (this.user) {
        this.user.card_gold += amount
        localStorage.setItem('user', JSON.stringify(this.user))
      }
    },

    updateFreeDraws(amount) {
      if (this.user) {
        this.user.free_draws += amount
        localStorage.setItem('user', JSON.stringify(this.user))
      }
    },

    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    }
  }
})
