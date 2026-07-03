<template>
  <div id="app">
    <!-- Top status bar: shown when logged in and not on admin pages -->
    <div v-if="userStore.isLoggedIn && !isAdminPage" class="status-bar">
      <div class="status-bar-left">
        <van-icon name="contact" size="18" color="rgba(255,255,255,0.8)" />
        <span class="status-bar-username">{{ userStore.username }}</span>
      </div>
      <div class="status-bar-right">
        <span class="status-bar-badge badge-gold">
          <van-icon name="gold-coin-o" size="14" />
          {{ userStore.cardGold }}
        </span>
        <span class="status-bar-badge badge-draws">
          <van-icon name="coupon-o" size="14" />
          {{ userStore.freeDraws }}
        </span>
        <button class="logout-btn" @click="logout">
          <van-icon name="revoke" /> 退出
        </button>
      </div>
    </div>

    <!-- Main content with slide transition -->
    <main>
      <router-view v-slot="{ Component }">
        <transition name="slide-right" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>

    <!-- Bottom tabbar: shown when logged in and not on admin pages -->
    <van-tabbar
      v-if="userStore.isLoggedIn && !isAdminPage"
      v-model="activeTab"
      route
      fixed
      placeholder
      safe-area-inset-bottom
    >
      <van-tabbar-item to="/" icon="home-o">首页</van-tabbar-item>
      <van-tabbar-item to="/gacha" icon="gift-o">抽卡</van-tabbar-item>
      <van-tabbar-item to="/battle" icon="fire-o">对战</van-tabbar-item>
      <van-tabbar-item to="/guild" icon="friends-o">工会</van-tabbar-item>
      <van-tabbar-item to="/mine" icon="contact-o">我的</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useUserStore } from './store/user'
import { useRouter, useRoute } from 'vue-router'
import { computed } from 'vue'

const userStore = useUserStore()
const router = useRouter()
const route = useRoute()

const activeTab = ref(0)

const isAdminPage = computed(() => route.path.startsWith('/admin'))

const logout = () => {
  userStore.logout()
  router.push('/login')
}
</script>
