<template>
  <div class="collection-page">
    <h1 class="page-title">卡片图鉴</h1>

    <div class="collection-progress">
      <div class="progress-text">
        已收集 <span class="progress-owned">{{ ownedCount }}</span>/<span class="progress-total">{{ totalCount }}</span>
        <span class="progress-percent">({{ completionPercent }}%)</span>
      </div>
      <div class="progress-bar-wrap">
        <div class="progress-bar-fill" :style="{ width: completionPercent + '%' }"></div>
      </div>
    </div>

    <van-tabs v-model:active="activeRarityTab" shrink sticky offset-top="46" class="rarity-tabs">
      <van-tab v-for="tab in rarityTabs" :key="tab.value" :title="tab.label">
      </van-tab>
    </van-tabs>

    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <van-empty
        v-if="filteredCards.length === 0 && !loading"
        description="暂无卡片数据"
        image="search"
      />

      <div v-else class="card-grid">
        <div
          v-for="card in filteredCards"
          :key="card.template_id"
          class="collection-card"
          :class="{ 'card-unowned': !card.owned }"
          @click="selectCard(card)"
        >
          <div class="card-icon-wrapper" :class="{ 'icon-greyed': !card.owned }">
            <CardIcon :image-id="card.image" :category="card.category" :name="card.name" size="medium" class="card-icon-wrap" />
            <div v-if="!card.owned" class="card-lock-overlay">
              <van-icon name="lock" size="24" color="rgba(255,255,255,0.4)" />
            </div>
          </div>
          <div class="card-name" :class="{ 'name-hidden': !card.owned }">
            {{ card.owned ? card.name : '???' }}
          </div>
          <van-tag
            :type="rarityTagType(card.rarity)"
            size="medium"
            round
            class="card-rarity-tag"
          >{{ card.rarity }}</van-tag>
          <div v-if="card.owned" class="card-stars">
            <van-icon
              v-for="s in card.base_stars"
              :key="s"
              name="star-filled"
              color="#fbbf24"
              size="12"
            />
          </div>
          <div v-else class="card-stars card-stars-hidden">
            <van-icon name="star-filled" color="rgba(255,255,255,0.2)" size="12" />
            <van-icon name="star-filled" color="rgba(255,255,255,0.2)" size="12" />
            <van-icon name="star-filled" color="rgba(255,255,255,0.2)" size="12" />
          </div>
          <div v-if="card.owned" class="card-stats">
            <div class="stat-item">
              <span class="stat-value">{{ Math.round(card.base_attack) }}</span>
              <span class="stat-label">攻击</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ Math.round(card.base_defense) }}</span>
              <span class="stat-label">防御</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">{{ Math.round(card.base_hp) }}</span>
              <span class="stat-label">生命</span>
            </div>
          </div>
          <div v-else class="card-stats card-stats-hidden">
            <div class="stat-item">
              <span class="stat-value">???</span>
              <span class="stat-label">攻击</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">???</span>
              <span class="stat-label">防御</span>
            </div>
            <div class="stat-item">
              <span class="stat-value">???</span>
              <span class="stat-label">生命</span>
            </div>
          </div>
          <div v-if="card.owned && card.owned_count > 1" class="owned-count-badge">
            x{{ card.owned_count }}
          </div>
        </div>
      </div>
    </van-pull-refresh>

    <!-- Card Detail Popup -->
    <van-popup
      v-model:show="showDetail"
      position="bottom"
      round
      :style="{ maxHeight: '75vh' }"
      class="detail-popup"
    >
      <div v-if="selectedCard" class="card-detail">
        <div class="detail-close" @click="showDetail = false">
          <van-icon name="cross" size="20" />
        </div>

        <div class="card-detail-header">
          <div :class="{ 'icon-greyed': !selectedCard.owned }">
            <CardIcon :image-id="selectedCard.image" :category="selectedCard.category" :name="selectedCard.name" size="large" />
          </div>
          <div class="detail-info">
            <h2 class="detail-name">{{ selectedCard.owned ? selectedCard.name : '???' }}</h2>
            <van-tag
              :type="rarityTagType(selectedCard.rarity)"
              size="large"
              round
            >{{ selectedCard.rarity }}</van-tag>
            <div v-if="selectedCard.owned" class="detail-stars">
              <van-icon
                v-for="s in selectedCard.base_stars"
                :key="s"
                name="star-filled"
                color="#fbbf24"
                size="16"
              />
            </div>
            <div v-if="selectedCard.owned" class="detail-owned-count">
              拥有 {{ selectedCard.owned_count }} 张
            </div>
            <div v-if="!selectedCard.owned" class="detail-unowned-hint">
              尚未收集到此卡片
            </div>
          </div>
        </div>

        <template v-if="selectedCard.owned">
          <div class="card-detail-stats">
            <div class="stat-row">
              <span class="stat-row-label"><van-icon name="slash-o" /> 攻击力</span>
              <span class="stat-value">{{ Math.round(selectedCard.base_attack) }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-row-label"><van-icon name="shield-o" /> 防御力</span>
              <span class="stat-value">{{ Math.round(selectedCard.base_defense) }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-row-label"><van-icon name="heart-o" /> 生命值</span>
              <span class="stat-value">{{ Math.round(selectedCard.base_hp) }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-row-label"><van-icon name="fire-o" /> 速度</span>
              <span class="stat-value">{{ selectedCard.speed }}</span>
            </div>
          </div>

          <div class="skill-info">
            <div v-for="(sk, idx) in parsedSkills" :key="idx" class="skill-item">
              <h3 class="skill-title">
                <van-icon name="aim" />
                {{ sk.name || `技能 ${idx + 1}` }}
              </h3>
              <p class="skill-desc">{{ sk.desc || '无描述' }}</p>
            </div>
            <div v-if="parsedSkills.length === 0" class="skill-item">
              <h3 class="skill-title">
                <van-icon name="aim" />
                {{ selectedCard.skill_name || '无技能' }}
              </h3>
              <p class="skill-desc">{{ selectedCard.skill_desc || '这张卡片没有特殊技能' }}</p>
            </div>
          </div>
        </template>

        <template v-else>
          <div class="detail-locked-message">
            <van-icon name="lock" size="48" color="rgba(255,255,255,0.2)" />
            <p>收集此卡片以查看详细属性</p>
          </div>
        </template>
      </div>
    </van-popup>

    <van-toast id="collection-toast" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { cardApi } from '../utils/api'
import { showToast } from 'vant'
import CardIcon from '../components/CardIcon.vue'

const collection = ref([])
const activeRarityTab = ref(0)
const loading = ref(false)
const refreshing = ref(false)
const showDetail = ref(false)
const selectedCard = ref(null)

const rarityTabs = [
  { label: '全部', value: '' },
  { label: '普通', value: '普通' },
  { label: '高级', value: '高级' },
  { label: '史诗', value: '史诗' },
  { label: '典藏', value: '典藏' },
]

const currentRarity = computed(() => rarityTabs[activeRarityTab.value]?.value || '')

const filteredCards = computed(() => {
  if (!currentRarity.value) return collection.value
  return collection.value.filter(c => c.rarity === currentRarity.value)
})

const totalCount = computed(() => collection.value.length)
const ownedCount = computed(() => collection.value.filter(c => c.owned).length)
const completionPercent = computed(() => {
  const total = totalCount.value
  if (total === 0) return 0
  return Math.round(ownedCount.value / total * 100)
})

// 解析多重技能列表
const parsedSkills = computed(() => {
  if (!selectedCard.value?.skills_json) return []
  try {
    const parsed = JSON.parse(selectedCard.value.skills_json)
    if (Array.isArray(parsed) && parsed.length > 0) {
      return parsed.map(s => ({
        name: s.name || '',
        desc: s.desc || '',
      }))
    }
  } catch { /* fallback to empty */ }
  return []
})

const rarityTagType = (rarity) => {
  const map = { '普通': 'default', '高级': 'success', '史诗': 'primary', '典藏': 'warning' }
  return map[rarity] || 'default'
}

const loadCollection = async () => {
  loading.value = true
  try {
    const res = await cardApi.getCollection()
    collection.value = res.data.collection || []
  } catch (e) {
    console.error(e)
    showToast('加载图鉴失败')
  } finally {
    loading.value = false
  }
}

const onRefresh = async () => {
  await loadCollection()
  refreshing.value = false
}

const selectCard = (card) => {
  selectedCard.value = card
  showDetail.value = true
}

onMounted(() => {
  loadCollection()
})
</script>

<style scoped>
.collection-page {
  padding: 0 16px 20px;
}

.collection-progress {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 16px;
}

.progress-text {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 10px;
}

.progress-owned {
  color: #667eea;
  font-weight: bold;
  font-size: 18px;
}

.progress-total {
  color: rgba(255, 255, 255, 0.6);
  font-weight: bold;
}

.progress-percent {
  color: #fbbf24;
  font-weight: bold;
  margin-left: 6px;
}

.progress-bar-wrap {
  height: 6px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 3px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border-radius: 3px;
  transition: width 0.5s ease;
}

.rarity-tabs {
  margin-bottom: 12px;
}

.rarity-tabs :deep(.van-tabs__nav) {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
}

.rarity-tabs :deep(.van-tab) {
  color: rgba(255, 255, 255, 0.6);
}

.rarity-tabs :deep(.van-tab--active) {
  color: #fff;
}

.rarity-tabs :deep(.van-tabs__line) {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 14px;
}

.collection-card {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 14px;
  padding: 14px 10px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.collection-card:hover {
  transform: translateY(-3px);
  border-color: rgba(102, 126, 234, 0.4);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
}

.collection-card.card-unowned {
  background: rgba(255, 255, 255, 0.02);
  border-color: rgba(255, 255, 255, 0.05);
  opacity: 0.65;
}

.collection-card.card-unowned:hover {
  border-color: rgba(255, 255, 255, 0.15);
  box-shadow: none;
  transform: none;
}

.card-icon-wrapper {
  position: relative;
  display: inline-block;
  margin-bottom: 10px;
}

.icon-greyed {
  filter: grayscale(100%) brightness(0.4);
}

.card-lock-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
}

.card-name {
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.name-hidden {
  color: rgba(255, 255, 255, 0.3);
}

.card-rarity-tag {
  margin-bottom: 6px;
}

.card-stars {
  display: flex;
  justify-content: center;
  gap: 2px;
  margin-bottom: 4px;
}

.card-stars-hidden {
  opacity: 0.5;
}

.card-stats {
  display: flex;
  justify-content: space-around;
  gap: 4px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-weight: bold;
  font-size: 13px;
  color: #fff;
}

.card-stats-hidden .stat-value {
  color: rgba(255, 255, 255, 0.25);
}

.stat-label {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.45);
}

.card-stats-hidden .stat-label {
  color: rgba(255, 255, 255, 0.2);
}

.owned-count-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  font-weight: bold;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
}

/* Detail Popup */
.detail-popup {
  background: rgba(20, 20, 40, 0.97);
  backdrop-filter: blur(20px);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.card-detail {
  padding: 24px 20px 30px;
  position: relative;
}

.detail-close {
  position: absolute;
  top: 16px;
  right: 16px;
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  z-index: 10;
}

.detail-close:hover {
  color: #fff;
}

.card-detail-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 24px;
}

.detail-info {
  flex: 1;
}

.detail-name {
  font-size: 22px;
  font-weight: bold;
  color: #fff;
  margin: 0 0 8px;
}

.detail-stars {
  display: flex;
  gap: 3px;
  margin: 8px 0;
}

.detail-owned-count {
  font-size: 13px;
  color: #667eea;
  margin-top: 6px;
}

.detail-unowned-hint {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 6px;
}

.card-detail-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 20px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
}

.stat-row-label {
  display: flex;
  align-items: center;
  gap: 6px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
}

.stat-row .stat-value {
  font-size: 16px;
}

.skill-info {
  background: rgba(102, 126, 234, 0.1);
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: 12px;
  padding: 14px;
}

.skill-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  color: #667eea;
  margin: 0 0 8px;
}

.skill-desc {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
  line-height: 1.5;
}

.skill-item {
  padding: 10px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
.skill-item:last-child {
  border-bottom: none;
}

.detail-locked-message {
  text-align: center;
  padding: 30px 0;
  color: rgba(255, 255, 255, 0.3);
}

.detail-locked-message p {
  margin-top: 12px;
  font-size: 14px;
}

@media (max-width: 768px) {
  .card-detail-header {
    flex-direction: column;
    text-align: center;
  }

  .detail-stars {
    justify-content: center;
  }

  .card-detail-stats {
    grid-template-columns: 1fr;
  }

  .card-grid {
    grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
    gap: 10px;
  }
}
</style>
