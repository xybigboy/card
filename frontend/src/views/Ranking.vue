<template>
  <div class="ranking-page">
    <h1 class="page-title">排行榜</h1>

    <van-tabs v-model:active="activeTab" shrink class="rank-tabs">
      <van-tab title="排行">
        <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
          <van-empty
            v-if="ranking.length === 0 && !loading"
            description="暂无排行数据"
            image="search"
          />

          <van-cell-group v-else inset class="rank-group">
            <div
              v-for="(player, index) in ranking"
              :key="player.username"
              class="rank-item"
              :class="{
                'is-me': player.username === userStore.username,
                'top-gold': index === 0,
                'top-silver': index === 1,
                'top-bronze': index === 2,
              }"
            >
              <div class="rank-position">
                <span v-if="index === 0" class="rank-badge badge-gold">冠军</span>
                <span v-else-if="index === 1" class="rank-badge badge-silver">亚军</span>
                <span v-else-if="index === 2" class="rank-badge badge-bronze">季军</span>
                <span v-else class="rank-number">{{ index + 1 }}</span>
              </div>

              <div class="rank-player">
                <span class="player-name">{{ player.username }}</span>
                <van-tag v-if="player.username === userStore.username" type="primary" round size="small">
                  我
                </van-tag>
              </div>

              <div class="rank-rating">
                <span class="rating-value">{{ player.rating }}</span>
                <span class="rating-label">积分</span>
              </div>

              <div class="rank-record">
                <span class="wins">{{ player.wins }}胜</span>
                <span class="separator">/</span>
                <span class="losses">{{ player.losses }}负</span>
                <span class="win-rate" v-if="player.wins + player.losses > 0">
                  {{ Math.round((player.wins / (player.wins + player.losses)) * 100) }}%
                </span>
              </div>
            </div>
          </van-cell-group>
        </van-pull-refresh>
      </van-tab>
    </van-tabs>

    <!-- My Ranking Summary -->
    <div v-if="myRank" class="my-ranking-card">
      <div class="my-rank-header">
        <span class="my-rank-label">我的排名</span>
        <span class="my-rank-number">#{{ myRank }}</span>
      </div>
      <div class="my-rank-stats">
        <div class="my-stat">
          <span class="my-stat-value">{{ userStore.rating }}</span>
          <span class="my-stat-label">积分</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '../store/user'
import { rankingApi } from '../utils/api'

const userStore = useUserStore()
const ranking = ref([])
const activeTab = ref(0)
const refreshing = ref(false)
const loading = ref(false)

const myRank = computed(() => {
  const idx = ranking.value.findIndex(p => p.username === userStore.username)
  return idx !== -1 ? idx + 1 : null
})

const loadRanking = async () => {
  loading.value = true
  try {
    const res = await rankingApi.getList()
    ranking.value = res.data.ranking || res.data || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const onRefresh = async () => {
  await loadRanking()
  refreshing.value = false
}

onMounted(() => {
  loadRanking()
})
</script>

<style scoped>
.ranking-page {
  padding: 0 16px 20px;
}

.rank-tabs {
  margin-bottom: 16px;
}

.rank-tabs :deep(.van-tabs__nav) {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
}

.rank-tabs :deep(.van-tab) {
  color: rgba(255, 255, 255, 0.6);
}

.rank-tabs :deep(.van-tab--active) {
  color: #fff;
}

.rank-tabs :deep(.van-tabs__line) {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.rank-group {
  background: rgba(255, 255, 255, 0.04);
  border-radius: 14px;
  overflow: hidden;
}

.rank-group :deep(.van-cell-group--inset) {
  background: transparent;
}

.rank-item {
  display: grid;
  grid-template-columns: 72px 1fr 80px 100px;
  align-items: center;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  transition: background 0.2s ease;
}

.rank-item:last-child {
  border-bottom: none;
}

.rank-item:hover {
  background: rgba(255, 255, 255, 0.03);
}

.rank-item.is-me {
  background: rgba(102, 126, 234, 0.12);
}

.rank-item.is-me:hover {
  background: rgba(102, 126, 234, 0.16);
}

/* Top 3 background accents */
.rank-item.top-gold {
  background: rgba(255, 215, 0, 0.06);
  border-left: 3px solid #ffd700;
}

.rank-item.top-silver {
  background: rgba(192, 192, 192, 0.06);
  border-left: 3px solid #c0c0c0;
}

.rank-item.top-bronze {
  background: rgba(205, 127, 50, 0.06);
  border-left: 3px solid #cd7f32;
}

.rank-position {
  display: flex;
  align-items: center;
  justify-content: center;
}

.rank-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: bold;
  letter-spacing: 1px;
}

.badge-gold {
  background: linear-gradient(135deg, #ffd700, #ffb300);
  color: #1a1a2e;
}

.badge-silver {
  background: linear-gradient(135deg, #e0e0e0, #bdbdbd);
  color: #1a1a2e;
}

.badge-bronze {
  background: linear-gradient(135deg, #cd7f32, #b8690f);
  color: #1a1a2e;
}

.rank-number {
  font-size: 18px;
  font-weight: bold;
  color: rgba(255, 255, 255, 0.6);
}

.rank-player {
  display: flex;
  align-items: center;
  gap: 8px;
}

.player-name {
  font-size: 14px;
  font-weight: 500;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rank-rating {
  text-align: center;
}

.rating-value {
  display: block;
  font-size: 16px;
  font-weight: bold;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.rating-label {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.4);
}

.rank-record {
  text-align: center;
  font-size: 13px;
}

.wins {
  color: #22c55e;
  font-weight: bold;
}

.separator {
  color: rgba(255, 255, 255, 0.3);
  margin: 0 2px;
}

.losses {
  color: #f5576c;
  font-weight: bold;
}

.win-rate {
  display: block;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
  margin-top: 2px;
}

/* My Ranking Card */
.my-ranking-card {
  margin-top: 20px;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 14px;
  padding: 20px;
  text-align: center;
}

.my-rank-header {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.my-rank-label {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
}

.my-rank-number {
  font-size: 28px;
  font-weight: bold;
  background: linear-gradient(135deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.my-rank-stats {
  display: flex;
  justify-content: center;
  gap: 30px;
}

.my-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.my-stat-value {
  font-size: 22px;
  font-weight: bold;
  color: #fbbf24;
}

.my-stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
}

@media (max-width: 768px) {
  .rank-item {
    grid-template-columns: 56px 1fr 64px 80px;
    padding: 12px 10px;
    font-size: 13px;
  }

  .rank-badge {
    font-size: 11px;
    padding: 2px 6px;
  }

  .rating-value {
    font-size: 14px;
  }

  .rank-record {
    font-size: 12px;
  }
}
</style>
