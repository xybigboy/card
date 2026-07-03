<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { adminApi } from '../utils/api'

const router = useRouter()

const adminUsername = ref('')
const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const loading = ref(false)
const profileLoading = ref(false)

// AI Provider management
const providers = ref([])
const providersLoading = ref(false)
const showProviderForm = ref(false)
const editingProviderId = ref(null)
const providerSaving = ref(false)
const providerTab = ref('text') // 'text' or 'image'
const providerForm = ref({ name: '', base_url: '', model: '', api_key: '', is_active: true, provider_type: 'text' })

const loadProviders = async () => {
  providersLoading.value = true
  try {
    const res = await adminApi.getAiProviders(providerTab.value)
    if (res.data.success) {
      providers.value = res.data.providers || []
    }
  } catch (e) {
    showToast({ message: '加载AI提供商失败', type: 'fail' })
  } finally {
    providersLoading.value = false
  }
}

const switchProviderTab = (tab) => {
  if (providerTab.value === tab) return
  providerTab.value = tab
  loadProviders()
}

const openAddProvider = () => {
  editingProviderId.value = null
  providerForm.value = { name: '', base_url: '', model: '', api_key: '', is_active: true, provider_type: providerTab.value }
  showProviderForm.value = true
}

const openEditProvider = (p) => {
  editingProviderId.value = p.id
  providerForm.value = {
    name: p.name,
    base_url: p.base_url,
    model: p.model,
    api_key: p.api_key_full || '',
    is_active: p.is_active,
    provider_type: p.provider_type || providerTab.value
  }
  showProviderForm.value = true
}

const submitProvider = async () => {
  if (!providerForm.value.name.trim()) { showToast({ message: '请输入名称', type: 'fail' }); return }
  if (!providerForm.value.base_url.trim()) { showToast({ message: '请输入Base URL', type: 'fail' }); return }
  if (!providerForm.value.model.trim()) { showToast({ message: '请输入模型名称', type: 'fail' }); return }
  if (!providerForm.value.api_key.trim()) { showToast({ message: '请输入API Key', type: 'fail' }); return }

  providerSaving.value = true
  try {
    if (editingProviderId.value) {
      await adminApi.updateAiProvider(editingProviderId.value, providerForm.value)
      showToast({ message: '更新成功', type: 'success' })
    } else {
      await adminApi.createAiProvider(providerForm.value)
      showToast({ message: '添加成功', type: 'success' })
    }
    showProviderForm.value = false
    await loadProviders()
  } catch (e) {
    showToast({ message: e.response?.data?.detail || '保存失败', type: 'fail' })
  } finally {
    providerSaving.value = false
  }
}

const deleteProvider = async (p) => {
  if (!confirm(`确定要删除「${p.name}」吗？`)) return
  try {
    await adminApi.deleteAiProvider(p.id)
    showToast({ message: '删除成功', type: 'success' })
    await loadProviders()
  } catch (e) {
    showToast({ message: e.response?.data?.detail || '删除失败', type: 'fail' })
  }
}

// Reward distribution
const rewardUsers = ref([])
const rewardTemplates = ref([])
const rewardLoading = ref(false)
const sendingReward = ref(false)
const rewardForm = ref({
  target_type: 'all',
  username: '',
  card_gold: 0,
  template_id: null,
  card_count: 1,
  card_stars: 1,
})

const loadRewardData = async () => {
  rewardLoading.value = true
  try {
    const [usersRes, templatesRes] = await Promise.all([
      adminApi.getUsers(),
      adminApi.getCardTemplates(),
    ])
    if (usersRes.data.success) {
      rewardUsers.value = usersRes.data.users || []
    }
    if (templatesRes.data.success) {
      rewardTemplates.value = templatesRes.data.templates || []
    }
  } catch (e) {
    showToast({ message: '加载奖励数据失败', type: 'fail' })
  } finally {
    rewardLoading.value = false
  }
}

const sendReward = async () => {
  if (rewardForm.value.target_type === 'user' && !rewardForm.value.username.trim()) {
    showToast({ message: '请输入玩家用户名', type: 'fail' })
    return
  }
  if (rewardForm.value.template_id && (!rewardForm.value.card_count || rewardForm.value.card_count <= 0)) {
    showToast({ message: '请输入有效的卡牌数量', type: 'fail' })
    return
  }
  if (rewardForm.value.template_id && (!rewardForm.value.card_stars || rewardForm.value.card_stars < 1)) {
    showToast({ message: '请输入有效的卡牌星级', type: 'fail' })
    return
  }

  sendingReward.value = true
  try {
    const payload = { ...rewardForm.value }
    // Only include card fields when a template is selected
    if (!payload.template_id) {
      delete payload.template_id
      delete payload.card_count
      delete payload.card_stars
    }
    const res = await adminApi.sendReward(payload)
    showToast({ message: res.data.message || '奖励发放成功', type: 'success' })
    // Reset card fields but keep target type
    rewardForm.value.card_gold = 0
    rewardForm.value.template_id = null
    rewardForm.value.card_count = 1
    rewardForm.value.card_stars = 1
  } catch (e) {
    showToast({ message: e.response?.data?.detail || '发放奖励失败', type: 'fail' })
  } finally {
    sendingReward.value = false
  }
}

// Database config management
const dbConfigs = ref([])
const currentDb = ref(null)
const dbLoading = ref(false)
const showDbForm = ref(false)
const editingDbId = ref(null)
const dbSaving = ref(false)
const testing = ref(false)
const migrating = ref(false)
const dbForm = ref({ name: '', db_type: 'mysql', host: '', port: 3306, database: '', username: 'root', password: '' })

const loadDbConfigs = async () => {
  dbLoading.value = true
  try {
    const res = await adminApi.getDbConfigs()
    if (res.data.success) {
      dbConfigs.value = res.data.configs
      currentDb.value = res.data.current
    }
  } catch (e) {
    showToast({ message: '加载数据库配置失败', type: 'fail' })
  } finally {
    dbLoading.value = false
  }
}

const openAddDb = () => {
  editingDbId.value = null
  dbForm.value = { name: '', db_type: 'mysql', host: '', port: 3306, database: '', username: 'root', password: '' }
  showDbForm.value = true
}

const openEditDb = (c) => {
  editingDbId.value = c.id
  dbForm.value = { name: c.name, db_type: c.db_type, host: c.host, port: c.port, database: c.database, username: c.username, password: c.password }
  showDbForm.value = true
}

const handleTestConnection = async () => {
  testing.value = true
  try {
    const res = await adminApi.testDbConnection(dbForm.value)
    if (res.data.success) {
      showToast({ message: '连接成功', type: 'success' })
    } else {
      showToast({ message: res.data.message || '连接失败', type: 'fail' })
    }
  } catch (e) {
    showToast({ message: e.response?.data?.detail || '连接失败', type: 'fail' })
  } finally {
    testing.value = false
  }
}

const submitDbConfig = async () => {
  if (!dbForm.value.name.trim()) { showToast({ message: '请输入名称', type: 'fail' }); return }
  if (dbForm.value.db_type === 'mysql' && !dbForm.value.host.trim()) { showToast({ message: '请输入主机地址', type: 'fail' }); return }
  dbSaving.value = true
  try {
    if (editingDbId.value) {
      await adminApi.updateDbConfig(editingDbId.value, dbForm.value)
      showToast({ message: '更新成功', type: 'success' })
    } else {
      await adminApi.createDbConfig(dbForm.value)
      showToast({ message: '添加成功', type: 'success' })
    }
    showDbForm.value = false
    await loadDbConfigs()
  } catch (e) {
    showToast({ message: e.response?.data?.detail || '保存失败', type: 'fail' })
  } finally {
    dbSaving.value = false
  }
}

const handleMigrate = async (c) => {
  if (!confirm(`确定要将所有数据迁移到「${c.name}」并切换吗？\n此操作会复制当前数据库的所有数据到目标数据库。`)) return
  migrating.value = true
  try {
    const res = await adminApi.migrateDb(c.id)
    showToast({ message: res.data.message, type: 'success' })
    await loadDbConfigs()
    if (res.data.need_restart) {
      setTimeout(() => {
        showToast({ message: '请重启服务使新数据库生效', type: 'warning', duration: 5000 })
      }, 2000)
    }
  } catch (e) {
    showToast({ message: e.response?.data?.detail || '迁移失败', type: 'fail' })
  } finally {
    migrating.value = false
  }
}

const deleteDbConfig = async (c) => {
  if (!confirm(`确定要删除配置「${c.name}」吗？`)) return
  try {
    await adminApi.deleteDbConfig(c.id)
    showToast({ message: '删除成功', type: 'success' })
    await loadDbConfigs()
  } catch (e) {
    showToast({ message: e.response?.data?.detail || '删除失败', type: 'fail' })
  }
}

const fetchProfile = async () => {
  profileLoading.value = true
  try {
    const res = await adminApi.getProfile()
    adminUsername.value = res.data.profile?.username || res.data.username || ''
  } catch (e) {
    showToast({ message: '获取管理员信息失败', type: 'fail' })
  } finally {
    profileLoading.value = false
  }
}

const handleChangePassword = async () => {
  if (!currentPassword.value.trim()) {
    showToast({ message: '请输入当前密码', type: 'fail' })
    return
  }
  if (!newPassword.value.trim()) {
    showToast({ message: '请输入新密码', type: 'fail' })
    return
  }
  if (newPassword.value.length < 6) {
    showToast({ message: '新密码至少6个字符', type: 'fail' })
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    showToast({ message: '两次输入的新密码不一致', type: 'fail' })
    return
  }

  loading.value = true
  try {
    const res = await adminApi.changePassword(currentPassword.value, newPassword.value)
    if (res.data.success) {
      showToast({ message: '密码修改成功，请重新登录', type: 'success' })
      localStorage.removeItem('admin_token')
      localStorage.removeItem('admin_username')
      setTimeout(() => {
        router.push('/admin/login')
      }, 1500)
    }
  } catch (e) {
    showToast({
      message: e.response?.data?.detail || '密码修改失败，请检查当前密码是否正确',
      type: 'fail',
    })
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.push('/admin/cards')
}

onMounted(() => {
  const token = localStorage.getItem('admin_token')
  if (!token) {
    router.push('/admin/login')
    return
  }
  fetchProfile()
  loadProviders()
  loadDbConfigs()
  loadRewardData()
})
</script>

<template>
  <div class="admin-settings-page">
    <van-nav-bar
      title="管理设置"
      left-arrow
      @click-left="goBack"
      class="settings-nav"
    />

    <div class="settings-content">
      <!-- Profile info -->
      <div class="glass-card profile-section">
        <h3 class="section-title">管理员信息</h3>
        <div v-if="profileLoading" class="profile-loading">
          <van-loading type="spinner" size="20px" color="#667eea" />
        </div>
        <div v-else class="profile-info">
          <div class="profile-row">
            <span class="profile-label">当前账号</span>
            <span class="profile-value">{{ adminUsername }}</span>
          </div>
        </div>
      </div>

      <!-- Password change form -->
      <div class="glass-card password-section">
        <h3 class="section-title">修改密码</h3>

        <form @submit.prevent="handleChangePassword" class="password-form">
          <van-cell-group inset class="form-fields">
            <van-field
              v-model="currentPassword"
              type="password"
              label="当前密码"
              placeholder="请输入当前密码"
              left-icon="lock"
              clearable
            />
            <van-field
              v-model="newPassword"
              type="password"
              label="新密码"
              placeholder="请输入新密码(至少6位)"
              left-icon="edit"
              clearable
            />
            <van-field
              v-model="confirmPassword"
              type="password"
              label="确认新密码"
              placeholder="请再次输入新密码"
              left-icon="shield-o"
              clearable
            />
          </van-cell-group>

          <van-button
            type="primary"
            block
            round
            size="large"
            :loading="loading"
            loading-text="提交中..."
            class="submit-btn"
            native-type="submit"
          >
            确认修改
          </van-button>
        </form>
      </div>

      <!-- AI Providers management -->
      <div class="glass-card provider-section">
        <div class="section-header">
          <h3 class="section-title no-border">AI 提供商配置</h3>
          <button class="add-provider-btn" @click="openAddProvider">+ 新增</button>
        </div>
        <p class="section-hint">OpenAI兼容接口，支持文本与图片模型提供商</p>

        <!-- Provider type tabs -->
        <div class="provider-type-tabs">
          <button
            class="type-tab"
            :class="{ active: providerTab === 'text' }"
            @click="switchProviderTab('text')"
          >
            文本模型
          </button>
          <button
            class="type-tab"
            :class="{ active: providerTab === 'image' }"
            @click="switchProviderTab('image')"
          >
            图片模型
          </button>
        </div>

        <div v-if="providersLoading" class="profile-loading">
          <van-loading type="spinner" size="20px" color="#667eea" />
        </div>

        <div v-else-if="providers.length === 0" class="empty-providers">
          暂无{{ providerTab === 'text' ? '文本' : '图片' }}提供商，请点击上方按钮添加
        </div>

        <div v-else class="provider-list">
          <div
            v-for="p in providers"
            :key="p.id"
            class="provider-item"
          >
            <div class="provider-info">
              <div class="provider-name">
                {{ p.name }}
                <span class="provider-type-badge" :class="p.provider_type || providerTab">
                  {{ (p.provider_type || providerTab) === 'image' ? '图片' : '文本' }}
                </span>
                <span class="provider-status" :class="{ inactive: !p.is_active }">
                  {{ p.is_active ? '启用' : '禁用' }}
                </span>
              </div>
              <div class="provider-detail">{{ p.model }}</div>
              <div class="provider-detail provider-url">{{ p.base_url }}</div>
              <div class="provider-detail">Key: {{ p.api_key }}</div>
            </div>
            <div class="provider-actions">
              <button class="edit-btn" @click="openEditProvider(p)">编辑</button>
              <button class="del-btn" @click="deleteProvider(p)">删除</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Reward distribution section -->
      <div class="glass-card reward-section">
        <div class="section-header">
          <h3 class="section-title no-border">发放奖励</h3>
        </div>
        <p class="section-hint">向全服或指定玩家发放金币与卡牌</p>

        <div v-if="rewardLoading" class="profile-loading">
          <van-loading type="spinner" size="20px" color="#667eea" />
        </div>

        <van-cell-group inset class="form-fields" v-else>
          <van-field name="target_type" label="发放对象">
            <template #input>
              <van-radio-group v-model="rewardForm.target_type" direction="horizontal">
                <van-radio name="all">全服</van-radio>
                <van-radio name="user">指定玩家</van-radio>
              </van-radio-group>
            </template>
          </van-field>

          <van-field
            v-if="rewardForm.target_type === 'user'"
            v-model="rewardForm.username"
            label="玩家用户名"
            placeholder="请输入玩家用户名"
            clearable
          />

          <van-field
            v-model.number="rewardForm.card_gold"
            type="number"
            label="金币数量"
            placeholder="0"
          />

          <van-field name="template_id" label="卡牌模板">
            <template #input>
              <select v-model="rewardForm.template_id" class="native-select">
                <option :value="null">不发放卡牌</option>
                <option v-for="t in rewardTemplates" :key="t.id" :value="t.id">
                  {{ t.name }} ({{ t.rarity }})
                </option>
              </select>
            </template>
          </van-field>

          <template v-if="rewardForm.template_id">
            <van-field
              v-model.number="rewardForm.card_count"
              type="number"
              label="卡牌数量"
              placeholder="1"
            />
            <van-field
              v-model.number="rewardForm.card_stars"
              type="number"
              label="卡牌星级"
              placeholder="1-10"
            />
          </template>
        </van-cell-group>

        <van-button
          type="primary"
          block
          round
          :loading="sendingReward"
          loading-text="发放中..."
          @click="sendReward"
          class="submit-btn"
        >
          发放奖励
        </van-button>

        <!-- User reference list -->
        <div v-if="rewardUsers.length > 0" class="user-ref-list">
          <div class="user-ref-title">玩家参考列表 ({{ rewardUsers.length }})</div>
          <div class="user-ref-scroll">
            <span
              v-for="u in rewardUsers"
              :key="u.id"
              class="user-ref-chip"
              @click="rewardForm.target_type = 'user'; rewardForm.username = u.username"
            >
              {{ u.username }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- AI Provider form popup -->
    <van-popup
      v-model:show="showProviderForm"
      position="bottom"
      round
      :style="{ maxHeight: '70vh' }"
      class="provider-popup"
    >
      <div class="popup-inner">
        <div class="popup-header">
          <h3 class="popup-title">{{ editingProviderId ? '编辑提供商' : '新增提供商' }}</h3>
          <van-icon name="cross" @click="showProviderForm = false" class="popup-close" />
        </div>
        <van-cell-group inset class="form-fields">
          <van-field v-model="providerForm.name" label="名称" placeholder="如: OpenAI、DeepSeek" />
          <van-field v-model="providerForm.base_url" label="Base URL" placeholder="https://api.openai.com/v1" />
          <van-field v-model="providerForm.model" label="模型" placeholder="如: gpt-4o-mini" />
          <van-field v-model="providerForm.api_key" label="API Key" placeholder="sk-..." type="password" />
          <van-field name="is_active" label="启用状态">
            <template #input>
              <van-switch v-model="providerForm.is_active" size="20" />
            </template>
          </van-field>
        </van-cell-group>
        <van-button
          type="primary"
          block
          round
          :loading="providerSaving"
          loading-text="保存中..."
          @click="submitProvider"
          class="submit-btn"
        >
          保存
        </van-button>
      </div>
    </van-popup>

    <!-- Database config section -->
    <div class="glass-card provider-section">
      <div class="section-header">
        <h3 class="section-title no-border">数据库配置</h3>
        <button class="add-provider-btn" @click="openAddDb">+ 新增</button>
      </div>
      <p class="section-hint">支持 SQLite / MySQL 切换，迁移数据后重启生效</p>

      <div v-if="currentDb" class="current-db-info">
        <span class="db-badge" :class="currentDb.db_type">{{ currentDb.db_type }}</span>
        <span class="db-name">{{ currentDb.name }}</span>
      </div>

      <div v-if="dbLoading" class="profile-loading">
        <van-loading type="spinner" size="20px" color="#667eea" />
      </div>

      <div v-else-if="dbConfigs.length === 0" class="empty-providers">
        暂无数据库配置，使用默认 SQLite
      </div>

      <div v-else class="provider-list">
        <div v-for="c in dbConfigs" :key="c.id" class="provider-item">
          <div class="provider-info">
            <div class="provider-name">
              {{ c.name }}
              <span class="db-badge" :class="c.db_type">{{ c.db_type }}</span>
              <span v-if="c.is_active" class="provider-status">当前</span>
            </div>
            <div v-if="c.db_type === 'mysql'" class="provider-detail">
              {{ c.username }}@{{ c.host }}:{{ c.port }}/{{ c.database }}
            </div>
            <div v-else class="provider-detail">{{ c.database }}</div>
          </div>
          <div class="provider-actions">
            <button class="edit-btn" @click="openEditDb(c)">编辑</button>
            <button class="migrate-btn" :disabled="migrating || c.is_active" @click="handleMigrate(c)">迁移</button>
            <button class="del-btn" @click="deleteDbConfig(c)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Database config popup -->
    <van-popup
      v-model:show="showDbForm"
      position="bottom"
      round
      :style="{ maxHeight: '80vh' }"
      class="provider-popup"
    >
      <div class="popup-inner">
        <div class="popup-header">
          <h3 class="popup-title">{{ editingDbId ? '编辑数据库' : '新增数据库' }}</h3>
          <van-icon name="cross" @click="showDbForm = false" class="popup-close" />
        </div>
        <van-cell-group inset class="form-fields">
          <van-field v-model="dbForm.name" label="名称" placeholder="如: 生产MySQL" />
          <van-field name="db_type" label="类型">
            <template #input>
              <van-radio-group v-model="dbForm.db_type" direction="horizontal">
                <van-radio name="sqlite">SQLite</van-radio>
                <van-radio name="mysql">MySQL</van-radio>
              </van-radio-group>
            </template>
          </van-field>
          <template v-if="dbForm.db_type === 'mysql'">
            <van-field v-model="dbForm.host" label="主机" placeholder="如: 127.0.0.1" />
            <van-field v-model.number="dbForm.port" type="number" label="端口" placeholder="3306" />
            <van-field v-model="dbForm.database" label="数据库名" placeholder="card_game" />
            <van-field v-model="dbForm.username" label="用户名" placeholder="root" />
            <van-field v-model="dbForm.password" label="密码" placeholder="" type="password" />
          </template>
          <template v-else>
            <van-field v-model="dbForm.database" label="文件路径" placeholder="/app/data/game.db" />
          </template>
        </van-cell-group>
        <div class="db-form-actions">
          <van-button plain type="primary" :loading="testing" loading-text="测试中..." @click="handleTestConnection">
            测试连接
          </van-button>
          <van-button type="primary" :loading="dbSaving" loading-text="保存中..." @click="submitDbConfig">
            保存
          </van-button>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<style scoped>
.admin-settings-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}

.settings-nav {
  background: rgba(255, 255, 255, 0.05) !important;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.settings-nav :deep(.van-nav-bar__title) {
  color: rgba(255, 255, 255, 0.9);
}

.settings-nav :deep(.van-icon) {
  color: rgba(255, 255, 255, 0.7) !important;
}

.settings-content {
  padding: 16px;
  max-width: 500px;
  margin: 0 auto;
}

.glass-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 16px;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.profile-loading {
  display: flex;
  justify-content: center;
  padding: 16px 0;
}

.profile-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.profile-label {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.9rem;
}

.profile-value {
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
  font-size: 0.95rem;
}

.form-fields {
  background: transparent !important;
  margin-bottom: 20px;
}

.form-fields :deep(.van-cell) {
  background: rgba(255, 255, 255, 0.04);
  color: #fff;
}

.form-fields :deep(.van-field__label) {
  color: rgba(255, 255, 255, 0.7);
}

.form-fields :deep(.van-field__control) {
  color: #fff;
}

.form-fields :deep(.van-field__control::placeholder) {
  color: rgba(255, 255, 255, 0.3);
}

.form-fields :deep(.van-icon) {
  color: rgba(255, 255, 255, 0.5);
}

.submit-btn {
  margin-top: 8px;
}

/* AI Providers section */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0;
}

.section-title.no-border {
  border-bottom: none;
  padding-bottom: 0;
  margin-bottom: 0;
}

.section-hint {
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.8rem;
  margin: 4px 0 16px;
}

.add-provider-btn {
  background: rgba(102, 126, 234, 0.3);
  color: #a5b4fc;
  border: 1px solid rgba(102, 126, 234, 0.4);
  border-radius: 8px;
  padding: 4px 14px;
  font-size: 0.8rem;
  cursor: pointer;
}

.empty-providers {
  color: rgba(255, 255, 255, 0.4);
  text-align: center;
  padding: 24px 0;
  font-size: 0.85rem;
}

.provider-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.provider-item {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 14px;
}

.provider-info {
  margin-bottom: 10px;
}

.provider-name {
  color: #fff;
  font-weight: 600;
  font-size: 0.95rem;
  display: flex;
  align-items: center;
  gap: 8px;
}

.provider-status {
  font-size: 0.7rem;
  font-weight: 400;
  color: #22c55e;
  background: rgba(34, 197, 94, 0.15);
  padding: 1px 8px;
  border-radius: 6px;
}

.provider-status.inactive {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.15);
}

.provider-detail {
  color: rgba(255, 255, 255, 0.45);
  font-size: 0.78rem;
  margin-top: 3px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.provider-url {
  font-family: monospace;
}

.provider-actions {
  display: flex;
  gap: 8px;
}

.provider-actions button {
  padding: 4px 16px;
  border-radius: 6px;
  font-size: 0.78rem;
  cursor: pointer;
  border: none;
}

.edit-btn {
  background: rgba(102, 126, 234, 0.25);
  color: #a5b4fc;
}

.del-btn {
  background: rgba(239, 68, 68, 0.2);
  color: #fca5a5;
}

/* Popup */
.provider-popup {
  background: rgba(20, 20, 40, 0.95) !important;
  backdrop-filter: blur(16px);
}

.popup-inner {
  padding: 20px;
}

.popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.popup-title {
  color: #fff;
  font-size: 1.05rem;
  font-weight: 600;
}

.popup-close {
  color: rgba(255, 255, 255, 0.5);
  font-size: 20px;
  cursor: pointer;
}

/* Database config section */
.db-badge {
  font-size: 0.65rem;
  font-weight: 600;
  padding: 1px 8px;
  border-radius: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.db-badge.mysql {
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.15);
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.db-badge.sqlite {
  color: #38bdf8;
  background: rgba(56, 189, 248, 0.15);
  border: 1px solid rgba(56, 189, 248, 0.3);
}

.current-db-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: rgba(34, 197, 94, 0.08);
  border: 1px solid rgba(34, 197, 94, 0.2);
  border-radius: 10px;
  margin-bottom: 14px;
}

.current-db-info .db-name {
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.88rem;
  font-weight: 500;
}

.migrate-btn {
  background: rgba(168, 85, 247, 0.25);
  color: #c4b5fd;
}

.migrate-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.db-form-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.db-form-actions .van-button {
  flex: 1;
}

/* Dark theme overrides for radio group in DB form */
.form-fields :deep(.van-radio__label) {
  color: rgba(255, 255, 255, 0.8);
}

.form-fields :deep(.van-radio__icon--checked .van-icon) {
  background-color: #667eea;
  border-color: #667eea;
}

/* Provider type tabs */
.provider-type-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.type-tab {
  flex: 1;
  padding: 8px 0;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.04);
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all 0.2s;
}

.type-tab.active {
  background: rgba(102, 126, 234, 0.25);
  color: #a5b4fc;
  border-color: rgba(102, 126, 234, 0.5);
}

/* Provider type badge */
.provider-type-badge {
  font-size: 0.65rem;
  font-weight: 600;
  padding: 1px 8px;
  border-radius: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.provider-type-badge.text {
  color: #38bdf8;
  background: rgba(56, 189, 248, 0.15);
  border: 1px solid rgba(56, 189, 248, 0.3);
}

.provider-type-badge.image {
  color: #c084fc;
  background: rgba(192, 132, 252, 0.15);
  border: 1px solid rgba(192, 132, 252, 0.3);
}

/* Native select (reward template dropdown) */
.native-select {
  background: transparent;
  color: #fff;
  border: none;
  outline: none;
  font-size: 0.875rem;
  width: 100%;
}

.native-select option {
  background: #1a1a2e;
  color: #fff;
}

/* Reward section */
.reward-section .submit-btn {
  margin-top: 4px;
}

.user-ref-list {
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.user-ref-title {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.78rem;
  margin-bottom: 10px;
}

.user-ref-scroll {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  max-height: 120px;
  overflow-y: auto;
}

.user-ref-chip {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.15s;
}

.user-ref-chip:hover {
  background: rgba(102, 126, 234, 0.2);
  border-color: rgba(102, 126, 234, 0.4);
  color: #a5b4fc;
}
</style>
