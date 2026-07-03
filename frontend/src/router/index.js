import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../store/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { guest: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { guest: true }
  },
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/gacha',
    name: 'Gacha',
    component: () => import('../views/Gacha.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/warehouse',
    name: 'Warehouse',
    component: () => import('../views/Warehouse.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/collection',
    name: 'Collection',
    component: () => import('../views/Collection.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/battle',
    name: 'Battle',
    component: () => import('../views/Battle.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/shop',
    name: 'Shop',
    component: () => import('../views/Shop.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/ranking',
    name: 'Ranking',
    component: () => import('../views/Ranking.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/battle-history',
    name: 'BattleHistory',
    component: () => import('../views/BattleHistory.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/guild',
    name: 'Guild',
    component: () => import('../views/Guild.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/brawl',
    name: 'Brawl',
    component: () => import('../views/Brawl.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/mine',
    name: 'Mine',
    component: () => import('../views/Mine.vue'),
    meta: { requiresAuth: true }
  },
  // 后台管理路由
  {
    path: '/admin/login',
    name: 'AdminLogin',
    component: () => import('../views/AdminLogin.vue'),
    meta: { adminGuest: true }
  },
  {
    path: '/admin/cards',
    name: 'AdminCards',
    component: () => import('../views/AdminCards.vue'),
    meta: { requiresAdmin: true }
  },
  {
    path: '/admin/settings',
    name: 'AdminSettings',
    component: () => import('../views/AdminSettings.vue'),
    meta: { requiresAdmin: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const adminToken = localStorage.getItem('admin_token')
  
  // 管理员路由检查
  if (to.meta.requiresAdmin && !adminToken) {
    next('/admin/login')
  } else if (to.meta.adminGuest && adminToken) {
    next('/admin/cards')
  }
  // 普通用户路由检查
  else if (to.meta.requiresAuth && !userStore.token) {
    next('/login')
  } else if (to.meta.guest && userStore.token) {
    next('/')
  } else {
    next()
  }
})

export default router
