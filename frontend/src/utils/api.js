import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

// Request interceptor - add auth token as query param (backend expects ?token=xxx)
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) {
    config.params = { ...config.params, token }
  }
  return config
})

// Response interceptor - handle 401
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// Auth APIs
export const authApi = {
  login: (username, password) => api.post('/login', { username, password }),
  register: (username, password) => api.post('/register', { username, password }),
}

// Card APIs
export const cardApi = {
  draw: (count) => api.post(`/draw?count=${count}`),
  getWarehouse: () => api.get('/cards'),
  getCollection: () => api.get('/cards/collection'),
  upgrade: (cardId) => api.post(`/cards/${cardId}/upgrade`),
  sell: (cardId) => api.post(`/cards/${cardId}/sell`),
  bulkSell: (rarity) => api.post('/cards/bulk-sell', { rarity }),
  setBattle: (cardId) => api.post(`/cards/${cardId}/set-battle`),
  consumeCards: (targetCardId, materialIds) => api.post(`/cards/${targetCardId}/consume`, { material_card_ids: materialIds }),
  // 皮肤/多图片
  getSkins: (cardId) => api.get(`/cards/${cardId}/skins`),
  uploadSkin: (cardId, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/cards/${cardId}/skins`, formData, { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 30000 })
  },
  selectSkin: (cardId, imagePath) => api.put(`/cards/${cardId}/skin`, null, { params: { image_path: imagePath } }),
}

// Battle APIs
export const battleApi = {
  getHistory: (limit = 20) => api.get('/battle/history', { params: { limit } }),
  getDetail: (id) => api.get(`/battle/${id}`),
}

// Shop APIs
export const shopApi = {
  getInfo: () => api.get('/shop/info'),
  buyDraws: (count) => api.post(`/shop/buy-draws?count=${count}`),
}

// Ranking APIs
export const rankingApi = {
  getList: () => api.get('/ranking'),
}

// Guild APIs
export const guildApi = {
  create: (data) => api.post('/guilds/create', data),
  list: () => api.get('/guilds/list'),
  search: (name) => api.get('/guilds/search', { params: { name } }),
  my: () => api.get('/guilds/my'),
  detail: (guildId) => api.get(`/guilds/${guildId}`),
  apply: (guildId) => api.post(`/guilds/${guildId}/apply`),
  cancelApply: (guildId) => api.post(`/guilds/${guildId}/cancel-apply`),
  applications: (guildId) => api.get(`/guilds/${guildId}/applications`),
  approve: (appId) => api.post(`/guilds/applications/${appId}/approve`),
  reject: (appId) => api.post(`/guilds/applications/${appId}/reject`),
  leave: () => api.post('/guilds/leave'),
  disband: () => api.post('/guilds/disband'),
  checkIn: () => api.post('/guilds/check-in'),
  checkInStatus: () => api.get('/guilds/check-in/status'),
  deposit: (guildId, amount) => api.post(`/guilds/${guildId}/deposit`, { amount }),
  distribute: (guildId, data) => api.post(`/guilds/${guildId}/distribute`, data),
  ranking: () => api.get('/guilds/ranking'),
}

// Challenge APIs
export const challengeApi = {
  byName: (username) => api.post('/challenge/by-name', { username }),
}

// Brawl APIs (WebSocket-based, but need REST for stats)
export const brawlApi = {
  getStats: () => api.get('/brawl/stats'),
}

// Admin APIs - separate axios instance that sends admin_token
const adminAxios = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

let adminRedirecting = false

adminAxios.interceptors.request.use(config => {
  const adminToken = localStorage.getItem('admin_token')
  if (adminToken) {
    config.params = { ...config.params, token: adminToken }
  }
  return config
})

adminAxios.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401 && !adminRedirecting) {
      adminRedirecting = true
      localStorage.removeItem('admin_token')
      if (window.location.pathname !== '/admin/login') {
        window.location.href = '/admin/login'
      }
    }
    return Promise.reject(error)
  }
)

export const adminApi = {
  login: (username, password) => adminAxios.post('/admin/login', { username, password }),
  getProfile: () => adminAxios.get('/admin/profile'),
  changePassword: (oldPassword, newPassword) => adminAxios.post('/admin/change-password', { old_password: oldPassword, new_password: newPassword }),
  getCardTemplates: () => adminAxios.get('/admin/card-templates'),
  createTemplate: (data) => adminAxios.post('/admin/card-templates', data),
  updateTemplate: (id, data) => adminAxios.put(`/admin/card-templates/${id}`, data),
  deleteTemplate: (id) => adminAxios.delete(`/admin/card-templates/${id}`),
  aiGenerate: (data) => adminAxios.post('/admin/ai-generate-cards', data, { timeout: 60000 }),
  batchSave: (cards) => adminAxios.post('/admin/batch-save-cards', { cards }),
  getAiProviders: (providerType) => adminAxios.get('/admin/ai-providers', { params: providerType ? { provider_type: providerType } : {} }),
  createAiProvider: (data) => adminAxios.post('/admin/ai-providers', data),
  updateAiProvider: (id, data) => adminAxios.put(`/admin/ai-providers/${id}`, data),
  deleteAiProvider: (id) => adminAxios.delete(`/admin/ai-providers/${id}`),
  getDbConfigs: () => adminAxios.get('/admin/db-configs'),
  createDbConfig: (data) => adminAxios.post('/admin/db-configs', data),
  updateDbConfig: (id, data) => adminAxios.put(`/admin/db-configs/${id}`, data),
  deleteDbConfig: (id) => adminAxios.delete(`/admin/db-configs/${id}`),
  testDbConnection: (data) => adminAxios.post('/admin/db-test-connection', data, { timeout: 15000 }),
  migrateDb: (configId) => adminAxios.post('/admin/db-migrate', { target_config_id: configId }, { timeout: 60000 }),
  getCurrentDb: () => adminAxios.get('/admin/db-current'),
  // Image generation
  generateImage: (data) => adminAxios.post('/admin/ai-generate-image', data, { timeout: 60000 }),
  generateCardImages: (providerId, templateIds, options = {}) => adminAxios.post('/admin/ai-generate-card-images', { image_provider_id: providerId, template_ids: templateIds, ...options }, { timeout: 120000 }),
  // 皮肤管理
  getTemplateSkins: (templateId) => adminAxios.get(`/admin/templates/${templateId}/skins`),
  uploadTemplateSkin: (templateId, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return adminAxios.post(`/admin/templates/${templateId}/skins`, formData, { headers: { 'Content-Type': 'multipart/form-data' }, timeout: 30000 })
  },
  deleteSkin: (skinId) => adminAxios.delete(`/admin/skins/${skinId}`),
  // Rewards
  getUsers: () => adminAxios.get('/admin/users'),
  sendReward: (data) => adminAxios.post('/admin/send-reward', data),
}

export default api
