<template>
  <div class="mine-page">
    <h1 class="page-title">我的</h1>
    <van-tabs v-model:active="activeTab" sticky shrink color="#667eea" title-active-color="#667eea" title-inactive-color="rgba(255,255,255,0.5)">
      <van-tab title="仓库">
        <Warehouse />
      </van-tab>
      <van-tab title="图鉴">
        <Collection />
      </van-tab>
      <van-tab title="排行">
        <Ranking />
      </van-tab>
      <van-tab title="战绩">
        <BattleHistory />
      </van-tab>
    </van-tabs>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Warehouse from './Warehouse.vue'
import Collection from './Collection.vue'
import Ranking from './Ranking.vue'
import BattleHistory from './BattleHistory.vue'

const activeTab = ref(0)
</script>

<style scoped>
.mine-page {
  padding-bottom: 60px;
}

.page-title {
  text-align: center;
  font-size: 1.5rem;
  margin-bottom: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

:deep(.van-tabs__wrap) {
  background: rgba(255, 255, 255, 0.04);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

:deep(.van-tabs__nav) {
  background: transparent;
}

:deep(.van-tabs__line) {
  background: #667eea;
}
</style>
