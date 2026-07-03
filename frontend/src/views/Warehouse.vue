<template>
  <div class="warehouse-page">
    <h1 class="page-title">卡片仓库</h1>

    <van-tabs v-model:active="activeRarityTab" shrink sticky offset-top="46" class="rarity-tabs">
      <van-tab v-for="tab in rarityTabs" :key="tab.value" :title="tab.label">
      </van-tab>
    </van-tabs>

    <div class="sort-bar">
      <span class="card-count">共 {{ totalCardCount }} 张 ({{ filteredCards.length }} 种)</span>
      <div class="sort-bar-actions">
        <button class="bulk-sell-btn" @click="showBulkSellDialog">批量出售</button>
        <select v-model="sortBy" class="sort-select">
          <option value="stars">按星级排序</option>
          <option value="level">按等级排序</option>
          <option value="attack">按攻击力排序</option>
        </select>
      </div>
    </div>

    <van-pull-refresh v-model="refreshing" @refresh="onRefresh">
      <van-empty
        v-if="totalCardCount === 0 && !loading"
        description="仓库空空如也"
        image="search"
      >
        <van-button type="primary" size="small" round to="/gacha">去抽卡</van-button>
      </van-empty>

      <div v-else class="card-grid">
        <van-swipe-cell
          v-for="card in filteredCards"
          :key="card.id"
          class="card-swipe-cell"
        >
          <div
            class="game-card"
            :class="{ 'on-battle': card.is_on_battle }"
            @click="selectCard(card)"
          >
            <van-tag v-if="card._count > 1" class="dup-count-tag">x{{ card._count }}</van-tag>
            <van-tag v-if="card.is_on_battle" type="warning" class="battle-tag">出战中</van-tag>
            <CardIcon :image-id="card.image" :category="card.category" :name="card.name" size="medium" class="card-icon-wrap" />
            <div class="card-name">{{ card.name }}</div>
            <van-tag
              :type="rarityTagType(card.rarity)"
              size="medium"
              round
              class="card-rarity-tag"
            >{{ card.rarity }}</van-tag>
            <div class="card-stars">
              <van-icon
                v-for="s in card.stars"
                :key="s"
                name="star-filled"
                color="#fbbf24"
                size="12"
              />
            </div>
            <div class="card-level">Lv.{{ card.level }}</div>
            <div class="card-stats">
              <div class="stat-item">
                <span class="stat-value">{{ Math.round(card.attack) }}</span>
                <span class="stat-label">攻击</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ Math.round(card.defense) }}</span>
                <span class="stat-label">防御</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ Math.round(card.hp) }}</span>
                <span class="stat-label">生命</span>
              </div>
            </div>
          </div>
          <template #right>
            <van-button square type="primary" class="swipe-btn" @click.stop="quickUpgrade(card)">升级</van-button>
            <van-button square type="danger" class="swipe-btn" @click.stop="quickSell(card)">出售</van-button>
          </template>
        </van-swipe-cell>
      </div>
    </van-pull-refresh>

    <!-- Card Detail Popup -->
    <van-popup
      v-model:show="showDetail"
      position="bottom"
      round
      :style="{ maxHeight: '85vh' }"
      class="detail-popup"
      @close="onDetailClose"
    >
      <div v-if="selectedCard" class="card-detail">
        <div class="detail-close" @click="showDetail = false">
          <van-icon name="cross" size="20" />
        </div>

        <div class="card-detail-header">
          <CardIcon :image-id="selectedCard.image" :category="selectedCard.category" :name="selectedCard.name" size="large" />
          <div class="detail-info">
            <h2 class="detail-name">{{ selectedCard.name }}</h2>
            <van-tag
              :type="rarityTagType(selectedCard.rarity)"
              size="large"
              round
            >{{ selectedCard.rarity }}</van-tag>
            <div class="detail-stars">
              <van-icon
                v-for="s in selectedCard.stars"
                :key="s"
                name="star-filled"
                color="#fbbf24"
                size="16"
              />
            </div>
            <div class="detail-level">等级 {{ selectedCard.level }}</div>
          </div>
        </div>

        <div class="card-detail-stats">
          <div class="stat-row">
            <span class="stat-row-label"><van-icon name="slash-o" /> 攻击力</span>
            <span class="stat-value">{{ Math.round(selectedCard.attack) }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-row-label"><van-icon name="shield-o" /> 防御力</span>
            <span class="stat-value">{{ Math.round(selectedCard.defense) }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-row-label"><van-icon name="heart-o" /> 生命值</span>
            <span class="stat-value">{{ Math.round(selectedCard.hp) }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-row-label"><van-icon name="fire-o" /> 速度</span>
            <span class="stat-value">{{ selectedCard.speed }}</span>
          </div>
        </div>

        <!-- 技能信息（支持多重技能） -->
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

        <!-- 皮肤选择 -->
        <div class="skin-section">
          <div class="skin-header">
            <h3 class="skin-title"><van-icon name="photo-o" /> 皮肤</h3>
          </div>
          <div class="skin-list" v-if="skins.length > 0">
            <div
              v-for="skin in skins"
              :key="skin.image_path"
              class="skin-item"
              :class="{ 'skin-selected': skin.is_selected }"
              @click="handleSelectSkin(skin)"
            >
              <img :src="skin.image_path" :alt="skin.source" class="skin-thumb" />
              <span class="skin-label">{{ skin.source === 'default' ? '默认' : skin.source === 'admin' ? '官方' : '自定义' }}</span>
            </div>
          </div>
          <div v-else class="skin-empty">暂无皮肤</div>
        </div>

        <!-- Duplicate cards section (material for upgrade) -->
        <div v-if="selectedGroupOthers.length > 0" class="duplicates-section">
          <h3 class="duplicates-title">
            <van-icon name="cards" />
            重复卡片 ({{ selectedGroupOthers.length }})
          </h3>
          <p class="duplicates-hint">选择重复卡片作为升级材料，每张提供属性加成</p>
          <div class="dup-list">
            <div
              v-for="dup in selectedGroupOthers"
              :key="dup.id"
              class="dup-item"
              :class="{ 'dup-selected': selectedMaterialIds.includes(dup.id) }"
              @click="toggleMaterial(dup.id)"
            >
              <div class="dup-info">
                <span class="dup-name">{{ dup.name }}</span>
                <span class="dup-detail">Lv.{{ dup.level }} / {{ dup.stars }}星</span>
              </div>
              <div class="dup-bonus">+{{ getMaterialBonus(dup) }}%</div>
              <div class="dup-check">
                <van-icon :name="selectedMaterialIds.includes(dup.id) ? 'checked' : 'circle'" size="20" :color="selectedMaterialIds.includes(dup.id) ? '#667eea' : 'rgba(255,255,255,0.3)'" />
              </div>
            </div>
          </div>
          <div v-if="selectedMaterialIds.length > 0" class="material-summary">
            已选 {{ selectedMaterialIds.length }} 张，总属性加成: +{{ totalMaterialBonus }}%
          </div>
          <van-button
            v-if="selectedMaterialIds.length > 0"
            type="warning"
            block
            round
            :loading="consuming"
            loading-text="融合中..."
            @click="consumeMaterialCards"
          >融合卡片 (消耗 {{ selectedMaterialIds.length }} 张)</van-button>
        </div>

        <div class="upgrade-cost-info">
          升级费用: <span class="cost-value">{{ upgradeCost }}</span> 卡金
        </div>

        <div class="card-actions">
          <van-button
            type="primary"
            block
            round
            :loading="upgrading"
            loading-text="升级中..."
            @click="upgradeCard"
          >升级 ({{ upgradeCost }} 卡金)</van-button>

          <van-button
            type="danger"
            block
            round
            plain
            :disabled="selectedCard.is_on_battle"
            @click="confirmSell"
          >出售 (获得 {{ sellValue }} 卡金)</van-button>

          <van-button
            type="success"
            block
            round
            :disabled="selectedCard.is_on_battle"
            @click="setBattleCard"
          >{{ selectedCard.is_on_battle ? '已出战' : '设为出战卡' }}</van-button>
        </div>
      </div>
    </van-popup>

    <van-toast id="warehouse-toast" />
    <van-dialog id="warehouse-dialog" />

    <van-action-sheet
      v-model:show="showBulkSellSheet"
      :actions="bulkSellActions"
      cancel-text="取消"
      description="选择要批量出售的稀有度（出战中的卡片将被保留）"
      @select="onSelectBulkSell"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '../store/user'
import { cardApi } from '../utils/api'
import { showToast, showDialog } from 'vant'
import CardIcon from '../components/CardIcon.vue'

const userStore = useUserStore()
const cards = ref([])
const activeRarityTab = ref(0)
const sortBy = ref('stars')
const selectedCard = ref(null)
const selectedGroupOthers = ref([])
const showDetail = ref(false)
const upgrading = ref(false)
const consuming = ref(false)
const refreshing = ref(false)
const loading = ref(false)
const showBulkSellSheet = ref(false)
const selectedMaterialIds = ref([])
// 皮肤相关
const skins = ref([])

const rarityTabs = [
  { label: '全部', value: '' },
  { label: '普通', value: '普通' },
  { label: '高级', value: '高级' },
  { label: '史诗', value: '史诗' },
  { label: '典藏', value: '典藏' },
]

const currentRarity = computed(() => rarityTabs[activeRarityTab.value]?.value || '')

const filteredCards = computed(() => {
  let list = [...cards.value]

  if (currentRarity.value) {
    list = list.filter(c => c.rarity === currentRarity.value)
  }

  // Group by template_id
  const groupMap = {}
  for (const card of list) {
    const tid = card.template_id
    if (!groupMap[tid]) {
      groupMap[tid] = { best: card, count: 1, others: [] }
    } else {
      groupMap[tid].count++
      groupMap[tid].others.push(card)
      // Keep highest-level / highest-star card as representative
      const best = groupMap[tid].best
      if (card.level > best.level || (card.level === best.level && card.stars > best.stars)) {
        groupMap[tid].best = card
      }
    }
  }

  const grouped = Object.values(groupMap).map(g => ({
    ...g.best,
    _count: g.count,
    _others: g.others.filter(c => c.id !== g.best.id),
  }))

  grouped.sort((a, b) => {
    if (sortBy.value === 'stars') return b.stars - a.stars
    if (sortBy.value === 'level') return b.level - a.level
    if (sortBy.value === 'attack') return b.attack - a.attack
    return 0
  })

  return grouped
})

const totalCardCount = computed(() => cards.value.length)

const upgradeCost = computed(() => {
  if (!selectedCard.value) return 0
  return Math.floor(50 * Math.pow(1.15, selectedCard.value.level - 1))
})

const sellValue = computed(() => {
  if (!selectedCard.value) return 0
  const rarityValues = { '普通': 20, '高级': 50, '史诗': 150, '典藏': 500 }
  const base = rarityValues[selectedCard.value.rarity] || 20
  const starBonus = (selectedCard.value.stars - 1) * 20
  const levelBonus = (selectedCard.value.level - 1) * 10
  return base + starBonus + levelBonus
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
        type: s.type || '',
        value: s.value || 0,
      }))
    }
  } catch { /* fallback to empty */ }
  return []
})

const rarityTagType = (rarity) => {
  const map = { '普通': 'default', '高级': 'success', '史诗': 'primary', '典藏': 'warning' }
  return map[rarity] || 'default'
}

// Material card system: consume duplicates for stat boost
const getMaterialBonus = (card) => {
  const rarityBonus = { '普通': 5, '高级': 10, '史诗': 20, '典藏': 40 }
  const base = rarityBonus[card.rarity] || 5
  const levelExtra = Math.floor((card.level - 1) * 2)
  return base + levelExtra
}

const totalMaterialBonus = computed(() => {
  return selectedMaterialIds.value.reduce((sum, id) => {
    const card = selectedGroupOthers.value.find(c => c.id === id)
    return sum + (card ? getMaterialBonus(card) : 0)
  }, 0)
})

const toggleMaterial = (id) => {
  const idx = selectedMaterialIds.value.indexOf(id)
  if (idx >= 0) {
    selectedMaterialIds.value.splice(idx, 1)
  } else {
    selectedMaterialIds.value.push(id)
  }
}

const consumeMaterialCards = async () => {
  if (consuming.value || selectedMaterialIds.value.length === 0) return
  consuming.value = true
  try {
    const res = await cardApi.consumeCards(selectedCard.value.id, selectedMaterialIds.value)
    if (res.data.success) {
      const idx = cards.value.findIndex(c => c.id === selectedCard.value.id)
      if (idx !== -1) {
        cards.value[idx] = res.data.card
        selectedCard.value = { ...res.data.card, _count: res.data.card._count || 1, _others: [] }
      }
      // Remove consumed cards from the raw list
      for (const mid of selectedMaterialIds.value) {
        cards.value = cards.value.filter(c => c.id !== mid)
      }
      selectedMaterialIds.value = []
      selectedGroupOthers.value = []
      showToast(`融合成功! 属性提升 +${res.data.bonus_percent}%`)
    }
  } catch (e) {
    showToast(e.response?.data?.detail || '融合失败')
  } finally {
    consuming.value = false
  }
}

const loadCards = async () => {
  loading.value = true
  try {
    const res = await cardApi.getWarehouse()
    cards.value = res.data.cards || res.data.warehouse || []
  } catch (e) {
    console.error(e)
    showToast('加载失败')
  } finally {
    loading.value = false
  }
}

const onRefresh = async () => {
  await loadCards()
  refreshing.value = false
}

const selectCard = (card) => {
  selectedCard.value = card
  selectedGroupOthers.value = card._others || []
  showDetail.value = true
  loadSkins(card.id)
}

const onDetailClose = () => {
  selectedCard.value = null
  selectedGroupOthers.value = []
  selectedMaterialIds.value = []
  skins.value = []
}

// 皮肤相关方法
const loadSkins = async (cardId) => {
  skins.value = []
  try {
    const res = await cardApi.getSkins(cardId)
    skins.value = res.data.skins || []
  } catch (e) {
    console.error('Failed to load skins:', e)
  }
}

const handleSelectSkin = async (skin) => {
  try {
    const res = await cardApi.selectSkin(selectedCard.value.id, skin.image_path)
    if (res.data.success) {
      // 更新选中状态
      skins.value.forEach(s => s.is_selected = false)
      skin.is_selected = true
      // 更新卡片图片
      if (selectedCard.value) {
        selectedCard.value.image = res.data.card.image
        selectedCard.value.selected_image = res.data.card.selected_image
      }
      showToast('皮肤已切换')
    }
  } catch (e) {
    showToast(e.response?.data?.detail || '切换失败')
  }
}

const setBattleCard = async () => {
  try {
    await cardApi.setBattle(selectedCard.value.id)
    cards.value.forEach(c => c.is_on_battle = false)
    selectedCard.value.is_on_battle = true
    showToast('出战卡片已设置!')
  } catch (e) {
    showToast(e.response?.data?.detail || '设置失败')
  }
}

const upgradeCard = async () => {
  if (upgrading.value) return
  upgrading.value = true
  try {
    const res = await cardApi.upgrade(selectedCard.value.id)
    if (res.data.success) {
      userStore.updateGold(-res.data.cost)
      const idx = cards.value.findIndex(c => c.id === selectedCard.value.id)
      if (idx !== -1) {
        cards.value[idx] = res.data.card
        selectedCard.value = res.data.card
      }
      showToast('升级成功!')
    }
  } catch (e) {
    showToast(e.response?.data?.detail || '升级失败')
  } finally {
    upgrading.value = false
  }
}

const confirmSell = () => {
  showDialog({
    title: '确认出售',
    message: `确定要出售这张卡片吗? 将获得 ${sellValue.value} 卡金`,
    showCancelButton: true,
    confirmButtonText: '确认出售',
    cancelButtonText: '取消',
  }).then(() => {
    sellCard()
  }).catch(() => {})
}

const sellCard = async () => {
  try {
    const res = await cardApi.sell(selectedCard.value.id)
    if (res.data.success) {
      userStore.updateGold(res.data.gold_earned)
      cards.value = cards.value.filter(c => c.id !== selectedCard.value.id)
      selectedCard.value = null
      showDetail.value = false
      showToast(`出售成功! 获得 ${res.data.gold_earned} 卡金`)
    }
  } catch (e) {
    showToast(e.response?.data?.detail || '出售失败')
  }
}

const quickUpgrade = async (card) => {
  try {
    const res = await cardApi.upgrade(card.id)
    if (res.data.success) {
      userStore.updateGold(-res.data.cost)
      const idx = cards.value.findIndex(c => c.id === card.id)
      if (idx !== -1) {
        cards.value[idx] = res.data.card
      }
      showToast('升级成功!')
    }
  } catch (e) {
    showToast(e.response?.data?.detail || '升级失败')
  }
}

const quickSell = (card) => {
  const rarityValues = { '普通': 20, '高级': 50, '史诗': 150, '典藏': 500 }
  const base = rarityValues[card.rarity] || 20
  const starBonus = (card.stars - 1) * 20
  const levelBonus = (card.level - 1) * 10
  const value = base + starBonus + levelBonus

  showDialog({
    title: '确认出售',
    message: `确定要出售 ${card.name} 吗? 将获得 ${value} 卡金`,
    showCancelButton: true,
    confirmButtonText: '确认出售',
    cancelButtonText: '取消',
  }).then(async () => {
    try {
      const res = await cardApi.sell(card.id)
      if (res.data.success) {
        userStore.updateGold(res.data.gold_earned)
        cards.value = cards.value.filter(c => c.id !== card.id)
        showToast(`出售成功! 获得 ${res.data.gold_earned} 卡金`)
      }
    } catch (e) {
      showToast(e.response?.data?.detail || '出售失败')
    }
  }).catch(() => {})
}

const bulkSelling = ref(false)

const showBulkSellDialog = () => {
  showBulkSellSheet.value = true
}

const bulkSellActions = [
  { name: '普通 (白卡)', value: '普通' },
  { name: '高级 (蓝卡)', value: '高级' },
  { name: '史诗 (紫卡)', value: '史诗' },
  { name: '典藏 (金卡)', value: '典藏' },
]

const onSelectBulkSell = (action) => {
  showBulkSellSheet.value = false
  confirmBulkSell(action.value)
}

const confirmBulkSell = (rarity) => {
  showDialog({
    title: `确认批量出售`,
    message: `确定要出售所有「${rarity}」品质的卡片吗？\n出战中的卡片将被保留。`,
    showCancelButton: true,
    confirmButtonText: '确认出售',
    cancelButtonText: '取消',
  }).then(() => {
    bulkSell(rarity)
  }).catch(() => {})
}

const bulkSell = async (rarity) => {
  if (bulkSelling.value) return
  bulkSelling.value = true
  try {
    const res = await cardApi.bulkSell(rarity)
    if (res.data.success) {
      userStore.updateGold(res.data.gold_earned)
      await loadCards()
      showToast(`批量出售成功! 出售 ${res.data.sold_count} 张，获得 ${res.data.gold_earned} 卡金`)
    }
  } catch (e) {
    showToast(e.response?.data?.detail || '批量出售失败')
  } finally {
    bulkSelling.value = false
  }
}

onMounted(() => {
  loadCards()
})
</script>

<style scoped>
.warehouse-page {
  padding: 0 16px 20px;
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

.sort-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 0 4px;
}

.sort-bar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bulk-sell-btn {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.8);
  padding: 6px 12px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.bulk-sell-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.2);
}

.bulk-sell-btn:active {
  background: rgba(255, 255, 255, 0.15);
}

.card-count {
  color: rgba(255, 255, 255, 0.5);
  font-size: 13px;
}

.sort-select {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.8);
  padding: 6px 12px;
  font-size: 13px;
  outline: none;
}

.sort-select option {
  background: #1a1a2e;
  color: #fff;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 14px;
}

.card-swipe-cell {
  border-radius: 14px;
  overflow: hidden;
}

.swipe-btn {
  height: 100%;
  padding: 0 16px;
}

.game-card {
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

.game-card:hover {
  transform: translateY(-3px);
  border-color: rgba(102, 126, 234, 0.4);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
}

.game-card.on-battle {
  border-color: rgba(251, 191, 36, 0.4);
  box-shadow: 0 0 20px rgba(251, 191, 36, 0.1);
}

.battle-tag {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 2;
}

.card-icon-wrap {
  margin: 0 auto 10px;
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

.card-rarity-tag {
  margin-bottom: 6px;
}

.card-stars {
  display: flex;
  justify-content: center;
  gap: 2px;
  margin-bottom: 4px;
}

.card-level {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 8px;
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

.stat-label {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.45);
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

.detail-level {
  color: rgba(255, 255, 255, 0.5);
  font-size: 14px;
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
  margin-bottom: 16px;
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

/* 皮肤选择 */
.skin-section {
  margin-bottom: 16px;
}
.skin-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.skin-title {
  flex: 1;
  font-size: 15px;
  color: #fff;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 6px;
}
.skin-list {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 4px;
}
.skin-item {
  flex-shrink: 0;
  width: 70px;
  text-align: center;
  cursor: pointer;
  border-radius: 8px;
  padding: 4px;
  border: 2px solid transparent;
  transition: border-color 0.2s;
}
.skin-item.skin-selected {
  border-color: #667eea;
}
.skin-thumb {
  width: 60px;
  height: 60px;
  object-fit: cover;
  border-radius: 6px;
}
.skin-label {
  display: block;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 4px;
}
.skin-empty {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.3);
  text-align: center;
  padding: 12px;
}

.upgrade-cost-info {
  text-align: center;
  margin-bottom: 16px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
}

.cost-value {
  color: #fbbf24;
  font-weight: bold;
  font-size: 16px;
}

.card-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.card-actions .van-button {
  font-size: 14px;
}

/* Duplicate count badge */
.dup-count-tag {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 2;
  background: linear-gradient(135deg, #667eea, #764ba2) !important;
  color: #fff !important;
  font-weight: bold;
  font-size: 12px;
  padding: 2px 8px !important;
  border-radius: 10px !important;
}

/* Duplicates section in detail popup */
.duplicates-section {
  background: rgba(102, 126, 234, 0.08);
  border: 1px solid rgba(102, 126, 234, 0.15);
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 16px;
}

.duplicates-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 15px;
  color: #667eea;
  margin: 0 0 6px;
}

.duplicates-hint {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.45);
  margin: 0 0 12px;
}

.dup-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 200px;
  overflow-y: auto;
  margin-bottom: 10px;
}

.dup-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.dup-item:active {
  background: rgba(255, 255, 255, 0.08);
}

.dup-item.dup-selected {
  border-color: rgba(102, 126, 234, 0.5);
  background: rgba(102, 126, 234, 0.12);
}

.dup-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.dup-name {
  font-size: 13px;
  color: #fff;
  font-weight: 500;
}

.dup-detail {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
}

.dup-bonus {
  font-size: 14px;
  font-weight: bold;
  color: #fbbf24;
}

.dup-check {
  flex-shrink: 0;
}

.material-summary {
  text-align: center;
  font-size: 13px;
  color: #fbbf24;
  margin-bottom: 10px;
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
