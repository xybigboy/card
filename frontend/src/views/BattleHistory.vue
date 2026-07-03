<script setup>
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { battleApi } from '../utils/api'
import BattleDetail from '../components/BattleDetail.vue'

const router = useRouter()

const activeTab = ref('all')
const records = ref([])
const page = ref(1)
const loading = ref(false)
const finished = ref(false)
const listError = ref(false)
const refreshing = ref(false)

// Battle detail popup state
const showDetail = ref(false)
const selectedBattleId = ref(null)

const filteredRecords = computed(() => {
  if (activeTab.value === 'all') return records.value
  return records.value.filter(r => r.result === activeTab.value)
})

const goBack = () => {
  router.back()
}

const formatRelativeTime = (timestamp) => {
  if (!timestamp) return ''
  const now = Date.now()
  const date = new Date(timestamp).getTime()
  const diff = Math.floor((now - date) / 1000)

  if (diff < 60) return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + '分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + '小时前'
  if (diff < 172800) return '昨天'
  if (diff < 2592000) return Math.floor(diff / 86400) + '天前'
  return new Date(timestamp).toLocaleDateString()
}

const resultTagType = (result) => {
  switch (result) {
    case 'win': return 'success'
    case 'lose': return 'danger'
    default: return 'default'
  }
}

const resultTagLabel = (result) => {
  switch (result) {
    case 'win': return '胜'
    case 'lose': return '负'
    default: return '平'
  }
}

const resultTagColor = (result) => {
  switch (result) {
    case 'win': return '#22c55e'
    case 'lose': return '#ef4444'
    default: return '#9ca3af'
  }
}

const loadHistory = async () => {
  try {
    const res = await battleApi.getHistory(50)
    const allRecords = res.data.records || res.data.items || []

    records.value = Array.isArray(allRecords) ? allRecords : []
    finished.value = true  // Backend doesn't support pagination, load all at once

    listError.value = false
  } catch (e) {
    listError.value = true
    showToast({ message: '加载对战记录失败', type: 'fail' })
  } finally {
    loading.value = false
  }
}

const onLoad = () => {
  loading.value = true
  loadHistory()
}

const onRefresh = async () => {
  page.value = 1
  finished.value = false
  listError.value = false
  records.value = []
  refreshing.value = false
  loading.value = true
  loadHistory()
}

const openDetail = (record) => {
  selectedBattleId.value = record.id
  showDetail.value = true
}

const closeDetail = () => {
  showDetail.value = false
  selectedBattleId.value = null
}

watch(activeTab, () => {
  // Tab changed, no need to reload - just filter client-side
})
</script>

<template>
  <div class="battle-history-page">
    <van-nav-bar
      title="对战记录"
      left-arrow
      @click-left="goBack"
      class="history-nav"
    />

    <van-tabs
      v-model:active="activeTab"
      class="history-tabs"
      line-width="60px"
      shrink
    >
      <van-tab title="全部" name="all" />
      <van-tab title="胜利" name="win" />
      <van-tab title="失败" name="lose" />
    </van-tabs>

    <van-pull-refresh v-model="refreshing" @refresh="onRefresh" class="history-refresh">
      <van-empty
        v-if="!loading && finished && filteredRecords.length === 0"
        description="暂无对战记录"
        class="empty-state"
      />

      <van-list
        v-else
        v-model:loading="loading"
        :finished="finished"
        finished-text="没有更多了"
        :error="listError"
        error-text="加载失败，点击重试"
        @load="onLoad"
      >
        <div class="records-list">
          <van-cell
            v-for="record in filteredRecords"
            :key="record.id"
            class="record-cell glass-card"
            clickable
            @click="openDetail(record)"
          >
            <template #title>
              <div class="record-header">
                <div class="record-opponent">
                  <span class="opponent-label">对手</span>
                  <span class="opponent-name">{{ record.opponent_name || '未知' }}</span>
                </div>
                <van-tag
                  :color="resultTagColor(record.result)"
                  class="result-tag"
                >
                  {{ resultTagLabel(record.result) }}
                </van-tag>
              </div>
            </template>

            <template #value>
              <div class="record-body">
                <div class="record-cards">
                  <span class="card-name player-card">{{ record.player_card_name || '我方卡片' }}</span>
                  <span class="card-vs">vs</span>
                  <span class="card-name opponent-card">{{ record.opponent_card_name || '对方卡片' }}</span>
                </div>

                <div class="record-info">
                  <div class="info-item">
                    <span class="info-label">卡金</span>
                    <span class="info-value gold">{{ record.reward_gold || 0 }}</span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">积分</span>
                    <span
                      class="info-value"
                      :class="(record.rating_change || 0) >= 0 ? 'positive' : 'negative'"
                    >
                      {{ (record.rating_change || 0) > 0 ? '+' : '' }}{{ record.rating_change || 0 }}
                    </span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">回合</span>
                    <span class="info-value">{{ record.rounds || 0 }}</span>
                  </div>
                  <div class="info-item time-item">
                    <span class="info-value time-value">{{ formatRelativeTime(record.created_at) }}</span>
                  </div>
                </div>
              </div>
            </template>
          </van-cell>
        </div>
      </van-list>
    </van-pull-refresh>

    <!-- Battle Detail Popup -->
    <BattleDetail
      :battle-id="selectedBattleId"
      :show="showDetail"
      @close="closeDetail"
    />
  </div>
</template>

<style scoped>
.battle-history-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}

.history-nav {
  background: rgba(255, 255, 255, 0.05) !important;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.history-nav :deep(.van-nav-bar__title) {
  color: rgba(255, 255, 255, 0.9);
}

.history-nav :deep(.van-icon) {
  color: rgba(255, 255, 255, 0.7) !important;
}

.history-tabs {
  background: transparent;
}

.history-tabs :deep(.van-tabs__nav) {
  background: rgba(255, 255, 255, 0.03);
}

.history-tabs :deep(.van-tab) {
  color: rgba(255, 255, 255, 0.5);
}

.history-tabs :deep(.van-tab--active) {
  color: rgba(255, 255, 255, 0.9);
}

.history-tabs :deep(.van-tabs__line) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.history-refresh {
  padding: 0 12px;
}

.empty-state {
  padding-top: 60px;
}

.empty-state :deep(.van-empty__description) {
  color: rgba(255, 255, 255, 0.5);
}

.records-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-bottom: 16px;
}

.glass-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
}

.record-cell {
  background: transparent !important;
  padding: 14px 16px;
}

.record-cell::after {
  display: none;
}

.record-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.record-opponent {
  display: flex;
  align-items: center;
  gap: 8px;
}

.opponent-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
}

.opponent-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.result-tag {
  font-size: 0.8rem;
  font-weight: 700;
  padding: 2px 10px;
  border-radius: 4px;
}

.record-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.record-cards {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
}

.card-name {
  color: rgba(255, 255, 255, 0.7);
}

.card-name.player-card {
  color: #4facfe;
}

.card-name.opponent-card {
  color: #f5576c;
}

.card-vs {
  color: rgba(255, 255, 255, 0.3);
  font-size: 0.7rem;
}

.record-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.info-label {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.4);
}

.info-value {
  font-size: 0.8rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
}

.info-value.gold {
  color: #fbbf24;
}

.info-value.positive {
  color: #22c55e;
}

.info-value.negative {
  color: #ef4444;
}

.time-item {
  margin-left: auto;
}

.time-value {
  color: rgba(255, 255, 255, 0.4);
  font-weight: 400;
  font-size: 0.75rem;
}

/* Van-list finished/error text */
:deep(.van-list__finished-text) {
  color: rgba(255, 255, 255, 0.3);
  padding: 16px 0;
}

:deep(.van-list__error-text) {
  color: rgba(255, 255, 255, 0.5);
  padding: 16px 0;
}

:deep(.van-loading) {
  color: rgba(255, 255, 255, 0.5);
}

/* Van-pull-refresh text */
:deep(.van-pull-refresh__text) {
  color: rgba(255, 255, 255, 0.5);
}
</style>
