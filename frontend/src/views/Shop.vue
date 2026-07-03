<template>
  <div class="shop-page">
    <h1 class="page-title">商店</h1>

    <!-- User Resources -->
    <div class="resources-bar">
      <div class="resource-item">
        <van-icon name="gold-coin-o" size="20" color="#fbbf24" />
        <span class="resource-label">当前卡金</span>
        <span class="resource-value gold">{{ userStore.cardGold }}</span>
      </div>
      <div class="resource-item">
        <van-icon name="coupon-o" size="20" color="#667eea" />
        <span class="resource-label">免费抽卡</span>
        <span class="resource-value">{{ userStore.freeDraws }}</span>
      </div>
    </div>

    <!-- Draw Packages -->
    <h2 class="section-title">抽卡礼包</h2>
    <van-cell-group inset class="package-group">
      <van-cell
        is-link
        center
        class="package-cell"
        @click="confirmBuy(1)"
      >
        <template #icon>
          <div class="package-icon single">
            <van-icon name="diamond-o" size="28" />
          </div>
        </template>
        <template #title>
          <span class="package-name">单抽</span>
        </template>
        <template #label>
          <span class="package-desc">抽取1张随机卡片</span>
        </template>
        <template #value>
          <div class="package-price">
            <span class="price-amount">100</span>
            <span class="price-unit">卡金</span>
          </div>
        </template>
      </van-cell>

      <van-cell
        is-link
        center
        class="package-cell highlight"
        @click="confirmBuy(10)"
      >
        <template #icon>
          <div class="package-icon multi">
            <van-icon name="diamond-o" size="28" />
            <van-tag type="danger" round size="small" class="rec-tag">推荐</van-tag>
          </div>
        </template>
        <template #title>
          <span class="package-name">十连抽</span>
        </template>
        <template #label>
          <span class="package-desc">抽取10张随机卡片</span>
        </template>
        <template #value>
          <div class="package-price">
            <span class="price-amount">1000</span>
            <span class="price-unit">卡金</span>
          </div>
        </template>
      </van-cell>
    </van-cell-group>

    <!-- How to Earn Gold -->
    <h2 class="section-title">如何获取卡金?</h2>
    <van-cell-group inset class="tips-group">
      <van-cell center class="tip-cell">
        <template #icon>
          <div class="tip-icon battle-icon">
            <van-icon name="fire-o" size="22" />
          </div>
        </template>
        <template #title>
          <span class="tip-title">PVP对战</span>
        </template>
        <template #label>
          <span class="tip-desc">赢得对战获得大量卡金, 失败也有安慰奖励</span>
        </template>
      </van-cell>

      <van-cell center class="tip-cell">
        <template #icon>
          <div class="tip-icon warehouse-icon">
            <van-icon name="bag-o" size="22" />
          </div>
        </template>
        <template #title>
          <span class="tip-title">兑换卡片</span>
        </template>
        <template #label>
          <span class="tip-desc">在仓库中兑换多余的卡片获得卡金</span>
        </template>
      </van-cell>

      <van-cell center class="tip-cell">
        <template #icon>
          <div class="tip-icon draw-icon">
            <van-icon name="diamond-o" size="22" />
          </div>
        </template>
        <template #title>
          <span class="tip-title">掠夺卡片</span>
        </template>
        <template #label>
          <span class="tip-desc">对战胜利有概率掠夺对方的低星卡片</span>
        </template>
      </van-cell>
    </van-cell-group>

    <van-toast id="shop-toast" />
    <van-dialog id="shop-dialog" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useUserStore } from '../store/user'
import { useRouter } from 'vue-router'
import { shopApi } from '../utils/api'
import { showToast, showDialog } from 'vant'

const userStore = useUserStore()
const router = useRouter()
const buying = ref(false)

const confirmBuy = (count) => {
  const cost = count * 100
  showDialog({
    title: '确认购买',
    message: `确定要花费 ${cost} 卡金进行 ${count} 连抽吗?`,
    showCancelButton: true,
    confirmButtonText: '确认购买',
    cancelButtonText: '取消',
  }).then(() => {
    buyDraw(count)
  }).catch(() => {})
}

const buyDraw = async (count) => {
  if (buying.value) return
  buying.value = true
  try {
    const response = await shopApi.buyDraws(count)
    // 刷新用户卡金和免费抽卡次数（以服务端最新数据为准）
    if (response.data?.card_gold !== undefined) {
      userStore.updateGold(response.data.card_gold - userStore.cardGold)
    }
    if (response.data?.free_draws !== undefined) {
      userStore.updateFreeDraws(response.data.free_draws - userStore.freeDraws)
    }
    // 兜底：拉取最新用户信息确保数据一致
    await userStore.fetchUserInfo()
    showToast(`购买成功! 已抽取 ${count} 次`)
    router.push('/gacha')
  } catch (e) {
    showToast(e.response?.data?.detail || '购买失败')
  } finally {
    buying.value = false
  }
}
</script>

<style scoped>
.shop-page {
  padding: 0 16px 20px;
}

.resources-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}

.resource-item {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 14px;
  padding: 16px;
}

.resource-label {
  color: rgba(255, 255, 255, 0.6);
  font-size: 13px;
}

.resource-value {
  margin-left: auto;
  font-size: 20px;
  font-weight: bold;
  color: #fff;
}

.resource-value.gold {
  color: #fbbf24;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
  margin: 0 0 14px 4px;
}

.package-group {
  background: rgba(255, 255, 255, 0.04);
  border-radius: 14px;
  overflow: hidden;
  margin-bottom: 28px;
}

.package-group :deep(.van-cell-group--inset) {
  background: transparent;
}

.package-cell {
  background: transparent !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.package-cell:last-child {
  border-bottom: none;
}

.package-cell :deep(.van-cell__title) {
  color: #fff;
}

.package-cell :deep(.van-cell__label) {
  color: rgba(255, 255, 255, 0.5);
}

.package-cell :deep(.van-cell__right-icon) {
  color: rgba(255, 255, 255, 0.3);
}

.package-cell.highlight {
  background: rgba(251, 191, 36, 0.06) !important;
}

.package-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  position: relative;
}

.package-icon.single {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.3), rgba(118, 75, 162, 0.3));
  color: #667eea;
}

.package-icon.multi {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.3), rgba(245, 158, 11, 0.3));
  color: #fbbf24;
}

.rec-tag {
  position: absolute;
  top: -6px;
  right: -10px;
}

.package-name {
  font-size: 15px;
  font-weight: 600;
}

.package-desc {
  font-size: 12px;
}

.package-price {
  text-align: right;
}

.price-amount {
  font-size: 22px;
  font-weight: bold;
  color: #fbbf24;
}

.price-unit {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin-left: 4px;
}

.tips-group {
  background: rgba(255, 255, 255, 0.04);
  border-radius: 14px;
  overflow: hidden;
}

.tips-group :deep(.van-cell-group--inset) {
  background: transparent;
}

.tip-cell {
  background: transparent !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.tip-cell:last-child {
  border-bottom: none;
}

.tip-cell :deep(.van-cell__title) {
  color: #fff;
}

.tip-cell :deep(.van-cell__label) {
  color: rgba(255, 255, 255, 0.5);
}

.tip-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
}

.tip-icon.battle-icon {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.tip-icon.warehouse-icon {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
}

.tip-icon.draw-icon {
  background: rgba(102, 126, 234, 0.15);
  color: #667eea;
}

.tip-title {
  font-size: 14px;
  font-weight: 600;
}

.tip-desc {
  font-size: 12px;
}

@media (max-width: 768px) {
  .resources-bar {
    flex-direction: column;
    gap: 10px;
  }
}
</style>
