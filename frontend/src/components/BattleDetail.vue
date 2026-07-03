<script setup>
import { ref, watch } from 'vue'
import { battleApi } from '../utils/api'
import CardIcon from './CardIcon.vue'
import BattleLogEntry from './BattleLogEntry.vue'

const props = defineProps({
  battleId: { type: [Number, String], default: null },
  show: { type: Boolean, default: false },
})

const emit = defineEmits(['close'])

const detail = ref(null)
const loading = ref(false)
const loadError = ref('')

const fetchDetail = async () => {
  if (!props.battleId) return

  loading.value = true
  loadError.value = ''
  detail.value = null

  try {
    const res = await battleApi.getDetail(props.battleId)
    detail.value = res.data.battle || res.data
  } catch (e) {
    loadError.value = e.response?.data?.detail || '加载对战详情失败'
  } finally {
    loading.value = false
  }
}

watch(() => props.show, (newVal) => {
  if (newVal && props.battleId) {
    fetchDetail()
  }
  if (!newVal) {
    detail.value = null
    loadError.value = ''
  }
})

const resultLabel = (result) => {
  switch (result) {
    case 'win': return '胜利'
    case 'lose': return '失败'
    case 'draw': return '平局'
    default: return result
  }
}

const resultColor = (result) => {
  switch (result) {
    case 'win': return '#22c55e'
    case 'lose': return '#ef4444'
    case 'draw': return '#9ca3af'
    default: return '#667eea'
  }
}

const onClose = () => {
  emit('close')
}
</script>

<template>
  <van-popup
    :show="show"
    position="bottom"
    round
    :style="{ height: '85%' }"
    class="battle-detail-popup"
    @close="onClose"
  >
    <div class="detail-container">
      <!-- Header -->
      <div class="detail-header">
        <h3 class="detail-title">对战详情</h3>
        <van-icon name="cross" class="close-btn" @click="onClose" />
      </div>

      <!-- Loading -->
      <div v-if="loading" class="detail-loading">
        <van-loading type="spinner" size="36px" color="#667eea" />
        <p class="loading-text">加载中...</p>
      </div>

      <!-- Error -->
      <div v-else-if="loadError" class="detail-error">
        <van-icon name="warning-o" size="48" color="#ef4444" />
        <p class="error-text">{{ loadError }}</p>
        <van-button plain size="small" @click="fetchDetail">重试</van-button>
      </div>

      <!-- Detail content -->
      <div v-else-if="detail" class="detail-body">
        <!-- Result summary -->
        <div class="result-summary glass-card">
          <div class="result-badge" :style="{ color: resultColor(detail.result) }">
            {{ resultLabel(detail.result) }}
          </div>
          <div class="result-meta">
            <div class="meta-item">
              <span class="meta-label">奖励卡金</span>
              <span class="meta-value gold">{{ detail.reward_gold || 0 }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">积分变化</span>
              <span
                class="meta-value"
                :class="(detail.rating_change || 0) >= 0 ? 'positive' : 'negative'"
              >
                {{ (detail.rating_change || 0) > 0 ? '+' : '' }}{{ detail.rating_change || 0 }}
              </span>
            </div>
            <div class="meta-item">
              <span class="meta-label">对战回合</span>
              <span class="meta-value">{{ detail.rounds || 0 }} 回合</span>
            </div>
          </div>
        </div>

        <!-- Cards comparison -->
        <div class="cards-comparison glass-card">
          <div class="card-side player-side">
            <CardIcon :image-id="detail.player_card?.image || ''" size="medium" />
            <div class="card-side-name">{{ detail.player_card?.name || detail.player_name || '我方' }}</div>
            <div class="card-side-stats" v-if="detail.player_card">
              <span>ATK {{ detail.player_card.attack }}</span>
              <span>HP {{ detail.player_card.hp }}</span>
              <span>DEF {{ detail.player_card.defense }}</span>
            </div>
          </div>
          <div class="vs-divider">VS</div>
          <div class="card-side opponent-side">
            <CardIcon :image-id="detail.opponent_card?.image || ''" size="medium" />
            <div class="card-side-name">{{ detail.opponent_card?.name || detail.opponent_name || '对方' }}</div>
            <div class="card-side-stats" v-if="detail.opponent_card">
              <span>ATK {{ detail.opponent_card.attack }}</span>
              <span>HP {{ detail.opponent_card.hp }}</span>
              <span>DEF {{ detail.opponent_card.defense }}</span>
            </div>
          </div>
        </div>

        <!-- Battle log -->
        <div class="battle-log-section glass-card">
          <h4 class="log-section-title">战斗日志</h4>
          <div class="log-scroll">
            <BattleLogEntry
              v-for="(log, index) in (detail.battle_log || [])"
              :key="index"
              :entry="log"
            />
            <div v-if="!detail.battle_log || detail.battle_log.length === 0" class="no-log">
              暂无战斗日志
            </div>
          </div>
        </div>
      </div>
    </div>
  </van-popup>
</template>

<style scoped>
.battle-detail-popup {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%) !important;
}

.detail-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
}

.detail-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin: 0;
}

.close-btn {
  color: rgba(255, 255, 255, 0.5);
  font-size: 20px;
  cursor: pointer;
  padding: 4px;
}

.close-btn:hover {
  color: rgba(255, 255, 255, 0.8);
}

.detail-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: 12px;
}

.loading-text {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.85rem;
}

.detail-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: 12px;
}

.error-text {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
}

.detail-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.glass-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
}

/* Result summary */
.result-summary {
  text-align: center;
}

.result-badge {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 12px;
}

.result-meta {
  display: flex;
  justify-content: space-around;
}

.meta-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.meta-label {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.5);
}

.meta-value {
  font-size: 0.95rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.meta-value.gold {
  color: #fbbf24;
}

.meta-value.positive {
  color: #22c55e;
}

.meta-value.negative {
  color: #ef4444;
}

/* Cards comparison */
.cards-comparison {
  display: flex;
  align-items: center;
  justify-content: space-around;
}

.card-side {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.card-side-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.card-side-stats {
  display: flex;
  gap: 8px;
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
}

.vs-divider {
  font-size: 1.5rem;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Battle log */
.log-section-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
  margin: 0 0 12px 0;
}

.log-scroll {
  max-height: 300px;
  overflow-y: auto;
}

.no-log {
  text-align: center;
  color: rgba(255, 255, 255, 0.4);
  padding: 24px 0;
  font-size: 0.85rem;
}
</style>
