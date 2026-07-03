<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '../store/user'
import { guildApi } from '../utils/api'
import { showToast, showDialog, showConfirmDialog } from 'vant'
import CardIcon from '../components/CardIcon.vue'

const userStore = useUserStore()

// State
const loading = ref(true)
const myGuild = ref(null)
const guildList = ref([])
const searchKeyword = ref('')
const searchResults = ref([])
const hasSearched = ref(false)
const activeTab = ref('info')
const applications = ref([])
const checkInStatus = ref(null)
const checkInLoading = ref(false)

// Create guild popup
const showCreatePopup = ref(false)
const createForm = ref({ name: '', description: '' })
const creating = ref(false)

// Deposit popup
const showDepositPopup = ref(false)
const depositAmount = ref('')
const depositing = ref(false)

// Distribute popup
const showDistributePopup = ref(false)
const distributeForm = ref({ userId: '', amount: '' })
const distributing = ref(false)

// Computed
const isInGuild = computed(() => myGuild.value !== null)
const isLeader = computed(() => {
  if (!myGuild.value) return false
  return myGuild.value.role === 'leader' || myGuild.value.leader_name === userStore.username
})
const hasPendingApply = computed(() => {
  // If not in guild, check if user has a pending application
  return myGuild.value?.pending_application !== undefined && myGuild.value.pending_application
})

// Load my guild status
const loadMyGuild = async () => {
  try {
    const res = await guildApi.my()
    // Backend returns {success, guild, role} — guild is null when not in a guild
    if (res.data.guild) {
      myGuild.value = { ...res.data.guild, role: res.data.role }
    } else {
      myGuild.value = null
    }
  } catch (e) {
    // 404 or other errors mean not in a guild
    myGuild.value = null
  }
}

// Load guild list
const loadGuildList = async () => {
  try {
    const res = await guildApi.list()
    guildList.value = res.data.guilds || res.data || []
  } catch (e) {
    console.error('Failed to load guild list:', e)
    guildList.value = []
  }
}

// Search guilds
const searchGuilds = async () => {
  if (!searchKeyword.value.trim()) {
    searchResults.value = []
    hasSearched.value = false
    return
  }
  hasSearched.value = true
  try {
    const res = await guildApi.search(searchKeyword.value.trim())
    searchResults.value = res.data.guilds || res.data || []
  } catch (e) {
    searchResults.value = []
  }
}

const clearSearch = () => {
  searchKeyword.value = ''
  searchResults.value = []
  hasSearched.value = false
}

// Create guild
const openCreatePopup = () => {
  createForm.value = { name: '', description: '' }
  showCreatePopup.value = true
}

const handleCreate = async () => {
  if (!createForm.value.name.trim()) {
    showToast('请输入公会名称')
    return
  }
  creating.value = true
  try {
    await guildApi.create({
      name: createForm.value.name.trim(),
      description: createForm.value.description.trim()
    })
    showToast('公会创建成功!')
    showCreatePopup.value = false
    await loadMyGuild()
    await loadCheckInStatus()
  } catch (e) {
    showToast(e.response?.data?.detail || '创建失败')
  } finally {
    creating.value = false
  }
}

// Apply to guild
const handleApply = async (guild) => {
  try {
    await guildApi.apply(guild.id)
    showToast(`已申请加入「${guild.name}」`)
    await loadMyGuild()
  } catch (e) {
    showToast(e.response?.data?.detail || '申请失败')
  }
}

// Cancel application
const handleCancelApply = async () => {
  if (!myGuild.value?.pending_guild_id) return
  try {
    await guildApi.cancelApply(myGuild.value.pending_guild_id)
    showToast('已取消申请')
    await loadMyGuild()
  } catch (e) {
    showToast(e.response?.data?.detail || '取消失败')
  }
}

// Leave guild
const handleLeave = () => {
  showConfirmDialog({
    title: '离开公会',
    message: '确定要离开当前公会吗？离开后将失去公会特权。',
    confirmButtonText: '确认离开',
    cancelButtonText: '取消'
  }).then(async () => {
    try {
      await guildApi.leave()
      showToast('已离开公会')
      myGuild.value = null
      await loadMyGuild()
      await loadGuildList()
    } catch (e) {
      showToast(e.response?.data?.detail || '离开失败')
    }
  }).catch(() => {})
}

// Disband guild
const handleDisband = () => {
  showConfirmDialog({
    title: '解散公会',
    message: '警告：解散公会将删除所有成员和公会资金，此操作不可撤销！',
    confirmButtonText: '确认解散',
    cancelButtonText: '取消',
    confirmButtonColor: '#ef4444'
  }).then(async () => {
    try {
      await guildApi.disband()
      showToast('公会已解散')
      myGuild.value = null
      await loadGuildList()
    } catch (e) {
      showToast(e.response?.data?.detail || '解散失败')
    }
  }).catch(() => {})
}

// Check in
const loadCheckInStatus = async () => {
  try {
    const res = await guildApi.checkInStatus()
    checkInStatus.value = res.data
  } catch (e) {
    checkInStatus.value = null
  }
}

const handleCheckIn = async () => {
  checkInLoading.value = true
  try {
    const res = await guildApi.checkIn()
    showToast(res.data?.message || '签到成功!')
    await loadCheckInStatus()
    await loadMyGuild()
    userStore.fetchUserInfo()
  } catch (e) {
    showToast(e.response?.data?.detail || '签到失败')
  } finally {
    checkInLoading.value = false
  }
}

// Load applications (leader only)
const loadApplications = async () => {
  if (!myGuild.value) return
  try {
    const res = await guildApi.applications(myGuild.value.id)
    applications.value = res.data.applications || res.data || []
  } catch (e) {
    applications.value = []
  }
}

// Approve / reject applications
const handleApprove = async (app) => {
  try {
    await guildApi.approve(app.id)
    showToast(`已通过「${app.username}」的申请`)
    await loadApplications()
    await loadMyGuild()
  } catch (e) {
    showToast(e.response?.data?.detail || '操作失败')
  }
}

const handleReject = async (app) => {
  try {
    await guildApi.reject(app.id)
    showToast(`已拒绝「${app.username}」的申请`)
    await loadApplications()
  } catch (e) {
    showToast(e.response?.data?.detail || '操作失败')
  }
}

// Deposit
const openDepositPopup = () => {
  depositAmount.value = ''
  showDepositPopup.value = true
}

const handleDeposit = async () => {
  const amount = parseInt(depositAmount.value)
  if (!amount || amount <= 0) {
    showToast('请输入有效金额')
    return
  }
  if (amount > userStore.cardGold) {
    showToast('卡金不足')
    return
  }
  depositing.value = true
  try {
    await guildApi.deposit(myGuild.value.id, amount)
    showToast('贡献成功!')
    showDepositPopup.value = false
    await loadMyGuild()
    await userStore.fetchUserInfo()
  } catch (e) {
    showToast(e.response?.data?.detail || '贡献失败')
  } finally {
    depositing.value = false
  }
}

// Distribute funds
const openDistributePopup = () => {
  distributeForm.value = { userId: '', amount: '' }
  showDistributePopup.value = true
}

const handleDistribute = async () => {
  const amount = parseInt(distributeForm.value.amount)
  if (!distributeForm.value.userId) {
    showToast('请选择成员')
    return
  }
  if (!amount || amount <= 0) {
    showToast('请输入有效金额')
    return
  }
  distributing.value = true
  try {
    await guildApi.distribute(myGuild.value.id, {
      user_id: parseInt(distributeForm.value.userId),
      amount
    })
    showToast('发放成功!')
    showDistributePopup.value = false
    await loadMyGuild()
  } catch (e) {
    showToast(e.response?.data?.detail || '发放失败')
  } finally {
    distributing.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const rarityTagType = (rarity) => {
  const map = { '普通': 'default', '高级': 'success', '史诗': 'primary', '典藏': 'warning' }
  return map[rarity] || 'default'
}

const init = async () => {
  loading.value = true
  await loadMyGuild()
  if (myGuild.value) {
    await loadCheckInStatus()
    if (isLeader.value) {
      await loadApplications()
    }
  } else {
    await loadGuildList()
  }
  loading.value = false
}

onMounted(() => {
  init()
})
</script>

<template>
  <div class="guild-page">
    <h1 class="page-title">公会</h1>

    <!-- Loading -->
    <div v-if="loading" class="loading-wrap">
      <van-loading type="spinner" size="36px" color="#667eea" />
    </div>

    <!-- ===== In Guild ===== -->
    <template v-else-if="isInGuild">
      <!-- Leader tabs -->
      <van-tabs v-if="isLeader" v-model:active="activeTab" class="guild-tabs" animated>
        <van-tab title="公会信息" name="info" />
        <van-tab title="入会申请" name="applications" />
      </van-tabs>

      <!-- Tab: Guild Info -->
      <div v-show="!isLeader || activeTab === 'info'" class="guild-info-section">
        <!-- Guild header card -->
        <div class="glass-card guild-header-card">
          <div class="guild-header-top">
            <div class="guild-emblem">
              <van-icon name="flag-o" size="32" color="#fbbf24" />
            </div>
            <div class="guild-header-info">
              <h2 class="guild-name">{{ myGuild.name }}</h2>
              <p class="guild-desc" v-if="myGuild.description">{{ myGuild.description }}</p>
            </div>
          </div>
          <div class="guild-stats-row">
            <div class="guild-stat-item">
              <van-icon name="medal-o" size="16" color="#667eea" />
              <span class="stat-label">等级</span>
              <span class="stat-value">Lv.{{ myGuild.level || 1 }}</span>
            </div>
            <div class="guild-stat-item">
              <van-icon name="friends-o" size="16" color="#4facfe" />
              <span class="stat-label">成员</span>
              <span class="stat-value">{{ myGuild.member_count || (myGuild.members?.length || 0) }}/{{ myGuild.max_members || 50 }}</span>
            </div>
            <div class="guild-stat-item">
              <van-icon name="gold-coin-o" size="16" color="#fbbf24" />
              <span class="stat-label">公会资金</span>
              <span class="stat-value gold">{{ myGuild.fund || 0 }}</span>
            </div>
          </div>
          <div class="guild-leader-row">
            <van-icon name="manager-o" size="14" />
            <span>会长: {{ myGuild.leader_name }}</span>
          </div>
        </div>

        <!-- Check-in card -->
        <div class="glass-card checkin-card">
          <div class="checkin-info">
            <h3 class="card-section-title">每日签到</h3>
            <p class="checkin-status" v-if="checkInStatus?.checked_in">
              <van-icon name="success" color="#22c55e" /> 今日已签到
            </p>
            <p class="checkin-status" v-else>
              <van-icon name="clock-o" color="#fbbf24" /> 今日尚未签到
            </p>
          </div>
          <van-button
            :type="checkInStatus?.checked_in ? 'default' : 'primary'"
            :loading="checkInLoading"
            :disabled="checkInStatus?.checked_in"
            size="small"
            round
            @click="handleCheckIn"
          >
            {{ checkInStatus?.checked_in ? '已签到' : '签到' }}
          </van-button>
        </div>

        <!-- Fund actions -->
        <div class="glass-card fund-actions-card" v-if="isLeader">
          <h3 class="card-section-title">公会资金管理</h3>
          <div class="fund-action-buttons">
            <van-button type="primary" plain size="small" icon="gold-coin-o" @click="openDepositPopup">
              贡献资金
            </van-button>
            <van-button type="warning" plain size="small" icon="share-o" @click="openDistributePopup">
              发放奖励
            </van-button>
          </div>
        </div>

        <!-- Members list -->
        <h2 class="section-title">公会成员</h2>
        <van-cell-group inset class="members-group">
          <van-cell
            v-for="member in (myGuild.members || [])"
            :key="member.user_id || member.id"
            class="member-cell"
          >
            <template #icon>
              <div class="member-avatar">
                <van-icon name="user-o" size="20" />
              </div>
            </template>
            <template #title>
              <div class="member-row">
                <span class="member-name">{{ member.username }}</span>
                <van-tag
                  v-if="member.role === 'leader' || member.username === myGuild.leader_name"
                  type="warning"
                  size="mini"
                  round
                >
                  会长
                </van-tag>
                <van-tag
                  v-else-if="member.role === 'officer'"
                  type="primary"
                  size="mini"
                  round
                  plain
                >
                  副会长
                </van-tag>
              </div>
            </template>
            <template #value>
              <span class="member-contribution">贡献 {{ member.contribution || 0 }}</span>
            </template>
          </van-cell>
        </van-cell-group>
        <div v-if="!myGuild.members || myGuild.members.length === 0" class="empty-hint">
          暂无成员数据
        </div>

        <!-- Action buttons -->
        <div class="guild-action-buttons">
          <van-button
            v-if="!isLeader"
            type="danger"
            plain
            block
            round
            icon="cross"
            @click="handleLeave"
          >
            离开公会
          </van-button>
          <van-button
            v-if="isLeader"
            type="danger"
            plain
            block
            round
            icon="delete-o"
            @click="handleDisband"
          >
            解散公会
          </van-button>
        </div>
      </div>

      <!-- Tab: Applications (leader only) -->
      <div v-if="isLeader && activeTab === 'applications'" class="applications-section">
        <h2 class="section-title">入会申请</h2>
        <van-cell-group inset class="applications-group" v-if="applications.length > 0">
          <van-cell
            v-for="app in applications"
            :key="app.id"
            class="application-cell"
          >
            <template #icon>
              <div class="member-avatar">
                <van-icon name="user-o" size="20" />
              </div>
            </template>
            <template #title>
              <span class="member-name">{{ app.username }}</span>
            </template>
            <template #label>
              <span class="apply-time">申请时间: {{ formatDate(app.created_at) }}</span>
            </template>
            <template #value>
              <div class="app-actions">
                <van-button type="success" size="mini" round @click="handleApprove(app)">
                  通过
                </van-button>
                <van-button type="danger" size="mini" round plain @click="handleReject(app)">
                  拒绝
                </van-button>
              </div>
            </template>
          </van-cell>
        </van-cell-group>
        <van-empty v-else description="暂无入会申请" class="dark-empty" />
      </div>
    </template>

    <!-- ===== Not In Guild ===== -->
    <template v-else>
      <!-- Pending application banner -->
      <div v-if="hasPendingApply" class="glass-card pending-banner">
        <van-icon name="clock-o" size="24" color="#fbbf24" />
        <div class="pending-info">
          <p class="pending-title">申请审核中</p>
          <p class="pending-sub">已申请加入「{{ myGuild.pending_guild_name || '公会' }}」，等待会长审核</p>
        </div>
        <van-button type="default" size="small" plain @click="handleCancelApply">
          撤销
        </van-button>
      </div>

      <!-- Create guild button -->
      <div class="glass-card create-guild-card">
        <div class="create-guild-info">
          <van-icon name="add-o" size="28" color="#667eea" />
          <div>
            <p class="create-guild-title">创建公会</p>
            <p class="create-guild-desc">创建公会，招揽伙伴一起战斗</p>
          </div>
        </div>
        <van-button type="primary" size="small" round @click="openCreatePopup">
          创建
        </van-button>
      </div>

      <!-- Search -->
      <div class="search-section">
        <van-search
          v-model="searchKeyword"
          placeholder="搜索公会名称"
          shape="round"
          class="guild-search"
          @search="searchGuilds"
          @clear="clearSearch"
        />
      </div>

      <!-- Guild list -->
      <h2 class="section-title">{{ hasSearched ? '搜索结果' : '全部公会' }}</h2>
      <van-cell-group inset class="guild-list-group">
        <van-cell
          v-for="guild in (hasSearched ? searchResults : guildList)"
          :key="guild.id"
          class="guild-list-cell"
        >
          <template #icon>
            <div class="guild-list-emblem">
              <van-icon name="flag-o" size="20" color="#fbbf24" />
            </div>
          </template>
          <template #title>
            <div class="guild-list-name">{{ guild.name }}</div>
            <div class="guild-list-desc" v-if="guild.description">{{ guild.description }}</div>
          </template>
          <template #label>
            <div class="guild-list-meta">
              <span>Lv.{{ guild.level || 1 }}</span>
              <span class="meta-dot">·</span>
              <span>{{ guild.member_count || 0 }}/{{ guild.max_members || 50 }}人</span>
              <span class="meta-dot">·</span>
              <span>会长: {{ guild.leader_name }}</span>
            </div>
          </template>
          <template #value>
            <van-button
              type="primary"
              size="mini"
              round
              @click="handleApply(guild)"
            >
              申请
            </van-button>
          </template>
        </van-cell>
      </van-cell-group>
      <van-empty
        v-if="(hasSearched ? searchResults : guildList).length === 0"
        :description="hasSearched ? '未找到匹配的公会' : '暂无公会，快来创建第一个吧!'"
        class="dark-empty"
      />
    </template>

    <!-- Create Guild Popup -->
    <van-popup
      v-model:show="showCreatePopup"
      round
      position="center"
      class="dark-popup"
      :close-on-click-overlay="false"
    >
      <div class="popup-content">
        <h3 class="popup-title">创建公会</h3>
        <van-field
          v-model="createForm.name"
          label="公会名称"
          placeholder="请输入公会名称"
          maxlength="20"
          class="dark-field"
        />
        <van-field
          v-model="createForm.description"
          label="公会简介"
          type="textarea"
          placeholder="选填，介绍一下你的公会"
          maxlength="100"
          rows="2"
          autosize
          class="dark-field"
        />
        <div class="popup-actions">
          <van-button block round plain @click="showCreatePopup = false">取消</van-button>
          <van-button block round type="primary" :loading="creating" @click="handleCreate">创建</van-button>
        </div>
      </div>
    </van-popup>

    <!-- Deposit Popup -->
    <van-popup
      v-model:show="showDepositPopup"
      round
      position="center"
      class="dark-popup"
      :close-on-click-overlay="false"
    >
      <div class="popup-content">
        <h3 class="popup-title">贡献公会资金</h3>
        <p class="popup-hint">当前卡金: {{ userStore.cardGold }}</p>
        <van-field
          v-model="depositAmount"
          label="贡献金额"
          type="digit"
          placeholder="请输入贡献的卡金数量"
          class="dark-field"
        />
        <div class="popup-actions">
          <van-button block round plain @click="showDepositPopup = false">取消</van-button>
          <van-button block round type="primary" :loading="depositing" @click="handleDeposit">确认</van-button>
        </div>
      </div>
    </van-popup>

    <!-- Distribute Popup -->
    <van-popup
      v-model:show="showDistributePopup"
      round
      position="center"
      class="dark-popup"
      :close-on-click-overlay="false"
    >
      <div class="popup-content">
        <h3 class="popup-title">发放公会奖励</h3>
        <p class="popup-hint">公会资金: {{ myGuild?.fund || 0 }}</p>
        <van-field
          v-model="distributeForm.userId"
          label="成员ID"
          type="digit"
          placeholder="请输入成员的用户ID"
          class="dark-field"
        />
        <van-field
          v-model="distributeForm.amount"
          label="发放金额"
          type="digit"
          placeholder="请输入发放的卡金数量"
          class="dark-field"
        />
        <div class="popup-actions">
          <van-button block round plain @click="showDistributePopup = false">取消</van-button>
          <van-button block round type="warning" :loading="distributing" @click="handleDistribute">确认</van-button>
        </div>
      </div>
    </van-popup>

    <van-toast id="guild-toast" />
    <van-dialog id="guild-dialog" />
  </div>
</template>

<style scoped>
.guild-page {
  padding: 0 16px 80px;
  max-width: 600px;
  margin: 0 auto;
}

.page-title {
  text-align: center;
  font-size: 1.5rem;
  margin-bottom: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.loading-wrap {
  display: flex;
  justify-content: center;
  padding: 60px 0;
}

.glass-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
}

/* Tabs */
.guild-tabs {
  margin-bottom: 16px;
}

.guild-tabs :deep(.van-tabs__nav) {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
}

.guild-tabs :deep(.van-tab) {
  color: rgba(255, 255, 255, 0.6);
}

.guild-tabs :deep(.van-tab--active) {
  color: #fff;
}

.guild-tabs :deep(.van-tabs__line) {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

/* Guild header card */
.guild-header-top {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.guild-emblem {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.2), rgba(245, 158, 11, 0.2));
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.guild-header-info {
  flex: 1;
}

.guild-name {
  font-size: 1.25rem;
  font-weight: 700;
  color: #fff;
  margin: 0 0 4px;
}

.guild-desc {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

.guild-stats-row {
  display: flex;
  gap: 20px;
  padding: 16px 0;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  margin-bottom: 12px;
}

.guild-stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

.stat-value {
  font-size: 15px;
  font-weight: 700;
  color: #fff;
}

.stat-value.gold {
  color: #fbbf24;
}

.guild-leader-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
}

/* Check-in card */
.checkin-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.checkin-info {
  flex: 1;
}

.card-section-title {
  font-size: 15px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 6px;
}

.checkin-status {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* Fund actions */
.fund-actions-card {
  padding: 16px 20px;
}

.fund-action-buttons {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

/* Section title */
.section-title {
  font-size: 16px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
  margin: 0 0 14px 4px;
}

/* Members group */
.members-group {
  background: rgba(255, 255, 255, 0.04);
  border-radius: 14px;
  overflow: hidden;
  margin-bottom: 24px;
}

.members-group :deep(.van-cell-group--inset) {
  background: transparent;
}

.member-cell {
  background: transparent !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.member-cell:last-child {
  border-bottom: none;
}

.member-cell :deep(.van-cell__title) {
  color: #fff;
}

.member-cell :deep(.van-cell__value) {
  color: rgba(255, 255, 255, 0.5);
}

.member-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(102, 126, 234, 0.15);
  color: #667eea;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
}

.member-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.member-name {
  font-size: 14px;
  font-weight: 600;
}

.member-contribution {
  font-size: 12px;
}

.empty-hint {
  text-align: center;
  color: rgba(255, 255, 255, 0.4);
  font-size: 14px;
  padding: 20px;
}

/* Action buttons */
.guild-action-buttons {
  margin-top: 8px;
}

/* Applications */
.applications-group {
  background: rgba(255, 255, 255, 0.04);
  border-radius: 14px;
  overflow: hidden;
}

.applications-group :deep(.van-cell-group--inset) {
  background: transparent;
}

.application-cell {
  background: transparent !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.application-cell:last-child {
  border-bottom: none;
}

.application-cell :deep(.van-cell__title) {
  color: #fff;
}

.application-cell :deep(.van-cell__label) {
  color: rgba(255, 255, 255, 0.4);
}

.apply-time {
  font-size: 12px;
}

.app-actions {
  display: flex;
  gap: 8px;
}

/* Pending banner */
.pending-banner {
  display: flex;
  align-items: center;
  gap: 16px;
}

.pending-info {
  flex: 1;
}

.pending-title {
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 4px;
}

.pending-sub {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

/* Create guild card */
.create-guild-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.create-guild-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.create-guild-title {
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 4px;
}

.create-guild-desc {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

/* Search */
.search-section {
  margin-bottom: 8px;
}

.guild-search {
  background: transparent;
}

.guild-search :deep(.van-search__content) {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.guild-search :deep(.van-field__control::placeholder) {
  color: rgba(255, 255, 255, 0.3);
}

.guild-search :deep(.van-field__control) {
  color: #fff;
}

/* Guild list */
.guild-list-group {
  background: rgba(255, 255, 255, 0.04);
  border-radius: 14px;
  overflow: hidden;
}

.guild-list-group :deep(.van-cell-group--inset) {
  background: transparent;
}

.guild-list-cell {
  background: transparent !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.guild-list-cell:last-child {
  border-bottom: none;
}

.guild-list-cell :deep(.van-cell__title) {
  color: #fff;
}

.guild-list-cell :deep(.van-cell__label) {
  color: rgba(255, 255, 255, 0.4);
}

.guild-list-emblem {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(251, 191, 36, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
}

.guild-list-name {
  font-size: 15px;
  font-weight: 600;
  color: #fff;
}

.guild-list-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 2px;
}

.guild-list-meta {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 4px;
}

.meta-dot {
  margin: 0 4px;
}

/* Dark empty */
.dark-empty :deep(.van-empty__description) {
  color: rgba(255, 255, 255, 0.4);
}

/* Popup */
.dark-popup {
  background: rgba(20, 20, 40, 0.95) !important;
  backdrop-filter: blur(16px);
  width: 90vw;
  max-width: 400px;
}

.popup-content {
  padding: 24px;
}

.popup-title {
  font-size: 1.1rem;
  font-weight: 700;
  color: #fff;
  margin: 0 0 16px;
  text-align: center;
}

.popup-hint {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  margin: 0 0 12px;
}

.dark-field {
  background: rgba(255, 255, 255, 0.04) !important;
  border-radius: 10px;
  margin-bottom: 12px;
}

.dark-field :deep(.van-field__label) {
  color: rgba(255, 255, 255, 0.7);
}

.dark-field :deep(.van-field__control) {
  color: #fff;
}

.dark-field :deep(.van-field__control::placeholder) {
  color: rgba(255, 255, 255, 0.3);
}

.popup-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.popup-actions :deep(.van-button--plain) {
  background: rgba(255, 255, 255, 0.08) !important;
  color: rgba(255, 255, 255, 0.85) !important;
  border-color: rgba(255, 255, 255, 0.15) !important;
}

@media (max-width: 768px) {
  .guild-stats-row {
    flex-wrap: wrap;
    gap: 12px;
  }

  .fund-action-buttons {
    flex-direction: column;
  }

  .popup-actions {
    flex-direction: column;
  }
}
</style>
