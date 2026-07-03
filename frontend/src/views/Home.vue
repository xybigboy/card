<template>
  <div class="home-page">
    <h1 class="page-title">欢迎回来，{{ userStore.username }}</h1>

    <!-- User Stats -->
    <van-cell-group :border="false" class="stats-cell-group">
      <van-cell title="卡金" :value="String(userStore.cardGold)" class="dark-stat-cell">
        <template #icon>
          <van-icon name="gold-coin-o" size="20" class="stat-cell-icon icon-gold" />
        </template>
      </van-cell>
      <van-cell title="免费抽卡" :value="String(userStore.freeDraws)" class="dark-stat-cell">
        <template #icon>
          <van-icon name="coupon-o" size="20" class="stat-cell-icon icon-draw" />
        </template>
      </van-cell>
      <van-cell title="积分 (ELO)" :value="String(userStore.rating)" class="dark-stat-cell">
        <template #icon>
          <van-icon name="star-o" size="20" class="stat-cell-icon icon-star" />
        </template>
      </van-cell>
      <van-cell title="胜 / 负" :value="winLossText" class="dark-stat-cell">
        <template #icon>
          <van-icon name="medal" size="20" class="stat-cell-icon icon-trophy" />
        </template>
      </van-cell>
      <van-cell title="胜率" :value="winRateText" class="dark-stat-cell">
        <template #icon>
          <van-icon name="chart-trending-o" size="20" class="stat-cell-icon icon-rate" />
        </template>
      </van-cell>
      <van-cell v-if="totalCards !== null" title="卡牌总数" :value="String(totalCards)" class="dark-stat-cell">
        <template #icon>
          <van-icon name="bag-o" size="20" class="stat-cell-icon icon-cards" />
        </template>
      </van-cell>
    </van-cell-group>

    <!-- Quick Actions Grid -->
    <div class="section-header">快速开始</div>
    <van-grid :column-num="5" :border="false" class="action-grid">
      <van-grid-item to="/gacha" class="action-grid-item">
        <template #icon>
          <van-icon name="gift-o" size="28" color="#667eea" />
        </template>
        <template #text>
          <span class="grid-label">抽卡</span>
        </template>
      </van-grid-item>
      <van-grid-item to="/battle" class="action-grid-item">
        <template #icon>
          <van-icon name="fire-o" size="28" color="#f5576c" />
        </template>
        <template #text>
          <span class="grid-label">对战</span>
        </template>
      </van-grid-item>
      <van-grid-item to="/brawl" class="action-grid-item">
        <template #icon>
          <van-icon name="flag-o" size="28" color="#f59e0b" />
        </template>
        <template #text>
          <span class="grid-label">乱斗</span>
        </template>
      </van-grid-item>
      <van-grid-item to="/guild" class="action-grid-item">
        <template #icon>
          <van-icon name="friends-o" size="28" color="#4facfe" />
        </template>
        <template #text>
          <span class="grid-label">工会</span>
        </template>
      </van-grid-item>
      <van-grid-item to="/mine" class="action-grid-item">
        <template #icon>
          <van-icon name="contact-o" size="28" color="#f093fb" />
        </template>
        <template #text>
          <span class="grid-label">我的</span>
        </template>
      </van-grid-item>
    </van-grid>

    <!-- Current Battle Card -->
    <div class="section-header">当前出战</div>
    <div v-if="battleCard" class="battle-card-section">
      <div class="battle-card-row">
        <CardIcon :image-id="battleCard.image" :category="battleCard.category" :name="battleCard.name" size="large" />
        <div class="battle-card-details">
          <div class="battle-card-name">{{ battleCard.name }}</div>
          <van-tag
            :type="rarityTagType(battleCard.rarity)"
            size="medium"
            round
            class="battle-rarity-tag"
          >
            {{ battleCard.rarity }}
          </van-tag>
          <div class="battle-card-stars">
            <van-icon
              v-for="s in battleCard.stars"
              :key="s"
              name="star"
              size="14"
              color="#ffd700"
            />
          </div>
          <div class="battle-card-stats-row">
            <span class="battle-stat">攻 {{ battleCard.attack }}</span>
            <span class="battle-stat">防 {{ battleCard.defense }}</span>
            <span class="battle-stat">血 {{ Math.round(battleCard.hp) }}</span>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="no-battle-card">
      <van-icon name="warning-o" size="32" color="rgba(255,255,255,0.3)" />
      <p class="no-battle-text">你还没有设置出战卡片</p>
      <van-button type="primary" size="small" round to="/warehouse">去仓库选择</van-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '../store/user'
import { cardApi } from '../utils/api'
import api from '../utils/api'
import CardIcon from '../components/CardIcon.vue'

const userStore = useUserStore()
const battleCard = ref(null)
const totalCards = ref(null)

const wins = computed(() => userStore.user?.wins || 0)
const losses = computed(() => userStore.user?.losses || 0)
const totalGames = computed(() => wins.value + losses.value)
const winRateText = computed(() => {
  if (totalGames.value === 0) return '--'
  return Math.round((wins.value / totalGames.value) * 100) + '%'
})
const winLossText = computed(() => `${wins.value} / ${losses.value}`)

const rarityTagType = (rarity) => {
  const map = {
    '普通': 'default',
    '高级': 'success',
    '史诗': 'primary',
    '典藏': 'warning',
  }
  return map[rarity] || 'default'
}

onMounted(async () => {
  // 先验证用户身份，失败则 401 拦截器自动跳转登录页
  try {
    await userStore.fetchUserInfo()
  } catch (e) {
    // 401 已由 api.js 拦截器处理（清除 token + 跳转 /login）
    // 不需要继续加载其他数据
    return
  }

  // fetchUserInfo 成功后再并发加载其他数据
  const [battleRes, warehouseRes] = await Promise.allSettled([
    api.get('/battle-card'),
    cardApi.getWarehouse(),
  ])

  if (battleRes.status === 'fulfilled') {
    battleCard.value = battleRes.value.data.card
  }

  if (warehouseRes.status === 'fulfilled') {
    const cards = warehouseRes.value.data.cards || warehouseRes.value.data || []
    totalCards.value = Array.isArray(cards) ? cards.length : 0
  }
})
</script>

<style scoped>
.home-page {
  padding: 16px;
  padding-bottom: 80px;
  max-width: 600px;
  margin: 0 auto;
}

/* Section headers */
.section-header {
  font-size: 16px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.85);
  margin: 24px 0 12px;
  padding-left: 4px;
}

/* Stats cell group */
.stats-cell-group {
  background: rgba(255, 255, 255, 0.06) !important;
  backdrop-filter: blur(12px);
  border-radius: 16px !important;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

:deep(.dark-stat-cell) {
  background: transparent !important;
  color: #fff;
}

:deep(.dark-stat-cell .van-cell__title) {
  color: rgba(255, 255, 255, 0.7);
}

:deep(.dark-stat-cell .van-cell__value) {
  color: #fff;
  font-weight: 700;
  font-size: 16px;
}

:deep(.dark-stat-cell::after) {
  border-color: rgba(255, 255, 255, 0.06);
}

.stat-cell-icon {
  margin-right: 12px;
}

.icon-gold { color: #ffd700; }
.icon-draw { color: #667eea; }
.icon-star { color: #f093fb; }
.icon-trophy { color: #4facfe; }
.icon-rate { color: #22c55e; }
.icon-cards { color: #ff6b35; }

/* Quick action grid */
.action-grid {
  background: rgba(255, 255, 255, 0.06) !important;
  backdrop-filter: blur(12px);
  border-radius: 16px !important;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 8px 0;
}

:deep(.action-grid-item .van-grid-item__content) {
  background: transparent !important;
  padding: 12px 0;
}

.grid-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.75);
  margin-top: 6px;
}

/* Battle card section */
.battle-card-section {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(12px);
  border-radius: 16px;
  padding: 20px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.battle-card-row {
  display: flex;
  align-items: center;
  gap: 20px;
}

.battle-card-details {
  flex: 1;
}

.battle-card-name {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 6px;
}

.battle-rarity-tag {
  margin-bottom: 8px;
}

.battle-card-stars {
  display: flex;
  gap: 2px;
  margin-bottom: 8px;
}

.battle-card-stats-row {
  display: flex;
  gap: 16px;
}

.battle-stat {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
}

.no-battle-card {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(12px);
  border-radius: 16px;
  padding: 32px 20px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  text-align: center;
}

.no-battle-text {
  color: rgba(255, 255, 255, 0.5);
  margin: 12px 0 16px;
  font-size: 14px;
}

@media (max-width: 768px) {
  .home-page {
    padding: 12px;
    padding-bottom: 80px;
  }

  .battle-card-row {
    flex-direction: column;
    text-align: center;
  }

  .battle-card-stars {
    justify-content: center;
  }

  .battle-card-stats-row {
    justify-content: center;
  }
}
</style>
