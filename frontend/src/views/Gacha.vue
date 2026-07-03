<template>
  <div class="gacha-page">
    <h1 class="page-title">抽卡召唤</h1>

    <van-tabs v-model:active="activeTab" shrink color="#667eea" title-active-color="#667eea" title-inactive-color="rgba(255,255,255,0.5)" class="gacha-tabs">
      <van-tab title="抽卡">
    <!-- Info Section -->
    <van-cell-group :border="false" class="info-cell-group">
      <van-cell title="当前卡金" :value="String(userStore.cardGold)" class="dark-info-cell">
        <template #icon>
          <van-icon name="gold-coin-o" size="20" class="info-icon icon-gold" />
        </template>
      </van-cell>
      <van-cell title="免费次数" :value="String(userStore.freeDraws)" class="dark-info-cell">
        <template #icon>
          <van-icon name="coupon-o" size="20" class="info-icon icon-ticket" />
        </template>
      </van-cell>
      <van-cell title="单抽费用" value="100 卡金" class="dark-info-cell">
        <template #icon>
          <van-icon name="balance-o" size="20" class="info-icon icon-cost" />
        </template>
      </van-cell>
      <van-cell title="十连费用" value="1000 卡金" class="dark-info-cell">
        <template #icon>
          <van-icon name="balance-list" size="20" class="info-icon icon-cost10" />
        </template>
      </van-cell>
    </van-cell-group>

    <!-- Draw Buttons -->
    <div class="draw-buttons">
      <van-button
        round
        :loading="drawing"
        loading-text="抽卡中..."
        :disabled="drawing"
        class="draw-btn draw-btn-single"
        @click="confirmDraw(1)"
      >
        <van-icon name="gem-o" class="btn-icon" />
        单抽
      </van-button>
      <van-button
        type="primary"
        round
        :loading="drawing"
        loading-text="抽卡中..."
        :disabled="drawing"
        class="draw-btn draw-btn-ten"
        @click="confirmDraw(10)"
      >
        <van-icon name="diamond-o" class="btn-icon" />
        十连抽
      </van-button>
    </div>

    <!-- Draw Result Popup -->
    <van-popup
      v-model:show="showResultPopup"
      position="bottom"
      round
      :style="{ maxHeight: '85vh' }"
      class="result-popup"
    >
      <div class="popup-header">
        <h2 class="popup-title">抽卡结果</h2>
        <van-icon name="cross" size="22" class="popup-close" @click="showResultPopup = false" />
      </div>
      <div class="popup-body">
        <div class="card-grid">
          <div
            v-for="(card, index) in drawnCards"
            :key="index"
            class="game-card card-reveal"
            :style="{ animationDelay: index * 0.12 + 's' }"
          >
            <CardIcon :image-id="card.image" :category="card.category" :name="card.name" size="medium" />
            <div class="card-name">{{ card.name }}</div>
            <van-tag
              :type="rarityTagType(card.rarity)"
              size="medium"
              round
              class="card-rarity-tag"
            >
              {{ card.rarity }}
            </van-tag>
            <div class="card-stars">
              <van-icon
                v-for="s in card.stars"
                :key="s"
                name="star"
                size="12"
                color="#ffd700"
              />
            </div>
            <div class="card-stats">
              <div class="stat-item">
                <span class="stat-value">{{ card.attack }}</span>
                <span>攻击</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ card.defense }}</span>
                <span>防御</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ Math.round(card.hp) }}</span>
                <span>生命</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="popup-footer">
        <van-button type="primary" round block @click="showResultPopup = false" class="popup-confirm-btn">
          确认
        </van-button>
      </div>
    </van-popup>

    <!-- Inline Results (always visible after draw) -->
    <div v-if="drawnCards.length > 0 && !showResultPopup" class="inline-results">
      <div class="section-header">上次抽卡结果</div>
      <div class="card-grid">
        <div
          v-for="(card, index) in drawnCards"
          :key="index"
          class="game-card"
        >
          <CardIcon :image-id="card.image" :category="card.category" :name="card.name" size="medium" />
          <div class="card-name">{{ card.name }}</div>
          <van-tag
            :type="rarityTagType(card.rarity)"
            size="medium"
            round
            class="card-rarity-tag"
          >
            {{ card.rarity }}
          </van-tag>
          <div class="card-stars">
            <van-icon
              v-for="s in card.stars"
              :key="s"
              name="star"
              size="12"
              color="#ffd700"
            />
          </div>
          <div class="card-stats">
            <div class="stat-item">
              <span class="stat-value">{{ card.attack }}</span>
              <span>攻击</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ card.defense }}</span>
              <span>防御</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ Math.round(card.hp) }}</span>
              <span>生命</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Probability Info -->
    <div class="section-header">抽卡概率</div>
    <div class="probability-section">
      <div class="prob-row">
        <van-tag type="default" size="large" round plain>普通</van-tag>
        <van-progress :percentage="60" :stroke-width="8" color="#9ca3af" class="prob-bar" />
        <span class="prob-pct">60%</span>
      </div>
      <div class="prob-row">
        <van-tag type="success" size="large" round plain>高级</van-tag>
        <van-progress :percentage="25" :stroke-width="8" color="#22c55e" class="prob-bar" />
        <span class="prob-pct">25%</span>
      </div>
      <div class="prob-row">
        <van-tag type="primary" size="large" round plain>史诗</van-tag>
        <van-progress :percentage="12" :stroke-width="8" color="#a855f7" class="prob-bar" />
        <span class="prob-pct">12%</span>
      </div>
      <div class="prob-row">
        <van-tag type="warning" size="large" round plain>典藏</van-tag>
        <van-progress :percentage="3" :stroke-width="8" color="#fbbf24" class="prob-bar" />
        <span class="prob-pct">3%</span>
      </div>
      <p class="prob-note">
        注：星级会在基础星级上随机浮动，有机会获得更高星级的卡片
      </p>
    </div>
      </van-tab>

      <van-tab title="商城">
        <Shop />
      </van-tab>
    </van-tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useUserStore } from '../store/user'
import { cardApi } from '../utils/api'
import CardIcon from '../components/CardIcon.vue'
import { showFailToast, showDialog } from 'vant'
import 'vant/es/toast/style'
import 'vant/es/dialog/style'
import Shop from './Shop.vue'

const userStore = useUserStore()
const drawing = ref(false)
const drawnCards = ref([])
const showResultPopup = ref(false)
const activeTab = ref(0)

const rarityTagType = (rarity) => {
  const map = {
    '普通': 'default',
    '高级': 'success',
    '史诗': 'primary',
    '典藏': 'warning',
  }
  return map[rarity] || 'default'
}

const confirmDraw = async (count) => {
  if (drawing.value) return

  const cost = count === 1 ? 100 : 1000
  const freeAvailable = userStore.freeDraws

  // If user has no free draws and not enough gold, warn
  if (freeAvailable < count && userStore.cardGold < cost) {
    showFailToast('卡金不足')
    return
  }

  // For ten-draw, confirm with dialog
  if (count === 10) {
    try {
      await showDialog({
        title: '确认十连抽',
        message: freeAvailable >= count
          ? `将使用 ${count} 次免费抽卡机会`
          : `将消耗 ${cost} 卡金进行十连抽，确认吗？`,
        confirmButtonText: '确认抽卡',
        cancelButtonText: '取消',
        showCancelButton: true,
        theme: 'round-button',
      })
    } catch {
      // User cancelled
      return
    }
  }

  await performDraw(count)
}

const performDraw = async (count) => {
  drawing.value = true
  drawnCards.value = []

  try {
    const res = await cardApi.draw(count)

    if (res.data.success) {
      drawnCards.value = res.data.cards
      showResultPopup.value = true

      // Update user store
      userStore.updateGold(-res.data.cost)
      userStore.updateFreeDraws(-res.data.free_used)
    }
  } catch (e) {
    showFailToast(e.response?.data?.detail || '抽卡失败')
  } finally {
    drawing.value = false
  }
}
</script>

<style scoped>
.gacha-page {
  padding: 16px;
  padding-bottom: 80px;
  max-width: 600px;
  margin: 0 auto;
}

.section-header {
  font-size: 16px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.85);
  margin: 24px 0 12px;
  padding-left: 4px;
}

/* Info section */
.info-cell-group {
  background: rgba(255, 255, 255, 0.06) !important;
  backdrop-filter: blur(12px);
  border-radius: 16px !important;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.08);
  margin-bottom: 20px;
}

:deep(.dark-info-cell) {
  background: transparent !important;
  color: #fff;
}

:deep(.dark-info-cell .van-cell__title) {
  color: rgba(255, 255, 255, 0.7);
}

:deep(.dark-info-cell .van-cell__value) {
  color: #fff;
  font-weight: 700;
  font-size: 16px;
}

:deep(.dark-info-cell::after) {
  border-color: rgba(255, 255, 255, 0.06);
}

.info-icon {
  margin-right: 12px;
}

.icon-gold { color: #ffd700; }
.icon-ticket { color: #667eea; }
.icon-cost { color: rgba(255, 255, 255, 0.5); }
.icon-cost10 { color: rgba(255, 255, 255, 0.5); }

/* Draw buttons */
.draw-buttons {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin: 24px 0;
}

.draw-btn {
  flex: 1;
  height: 56px;
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.draw-btn-single {
  background: rgba(255, 255, 255, 0.08) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
  color: #fff !important;
}

.draw-btn-single:hover {
  border-color: rgba(102, 126, 234, 0.5) !important;
}

.draw-btn-ten {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border: none !important;
}

.btn-icon {
  font-size: 20px;
}

/* Popup */
:deep(.result-popup) {
  background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%) !important;
}

.popup-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 20px 12px;
}

.popup-title {
  font-size: 20px;
  font-weight: 700;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.popup-close {
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  padding: 4px;
}

.popup-close:hover {
  color: #fff;
}

.popup-body {
  padding: 0 16px 16px;
  overflow-y: auto;
  max-height: 60vh;
}

.popup-footer {
  padding: 12px 20px 20px;
}

.popup-confirm-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  border: none !important;
  height: 44px;
  font-weight: 600;
}

/* Card grid */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}

.game-card {
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
  border-radius: 16px;
  padding: 16px 12px;
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.08);
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.game-card:hover {
  border-color: rgba(102, 126, 234, 0.4);
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.2);
}

.card-name {
  font-size: 14px;
  font-weight: 700;
  color: #fff;
  margin-top: 8px;
  margin-bottom: 4px;
}

.card-rarity-tag {
  margin-bottom: 6px;
}

.card-stars {
  display: flex;
  gap: 2px;
  justify-content: center;
  margin-bottom: 8px;
}

.card-stats {
  display: flex;
  justify-content: space-around;
  width: 100%;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.6);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.stat-item .stat-value {
  font-weight: 700;
  color: #fff;
  font-size: 13px;
}

/* Inline results */
.inline-results {
  margin-top: 8px;
}

/* Probability section */
.probability-section {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(12px);
  border-radius: 16px;
  padding: 20px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.prob-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.prob-row:last-of-type {
  margin-bottom: 0;
}

:deep(.prob-row .van-tag) {
  min-width: 48px;
  justify-content: center;
}

.prob-bar {
  flex: 1;
  background: rgba(255, 255, 255, 0.08) !important;
  border-radius: 4px;
}

:deep(.prob-bar .van-progress__portion) {
  border-radius: 4px;
}

.prob-pct {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  min-width: 36px;
  text-align: right;
}

.prob-note {
  margin-top: 16px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 13px;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .gacha-page {
    padding: 12px;
    padding-bottom: 80px;
  }

  .draw-buttons {
    flex-direction: column;
  }

  .draw-btn {
    width: 100%;
  }

  .card-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }

  .prob-row {
    flex-wrap: wrap;
  }
}
</style>
