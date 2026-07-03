<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import { adminApi } from '../utils/api'

const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)

const handleLogin = async () => {
  if (!username.value.trim()) {
    showToast({ message: '请输入管理员账号', type: 'fail' })
    return
  }
  if (!password.value.trim()) {
    showToast({ message: '请输入密码', type: 'fail' })
    return
  }

  loading.value = true

  try {
    const res = await adminApi.login(username.value, password.value)

    if (res.data.success) {
      localStorage.setItem('admin_token', res.data.token)
      localStorage.setItem('admin_username', res.data.username)
      router.push('/admin/cards')
    }
  } catch (e) {
    showToast({
      message: e.response?.data?.detail || '登录失败，请检查账号密码',
      type: 'fail',
    })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="admin-login-page">
    <div class="login-container glass-card">
      <h1 class="login-title">管理后台</h1>
      <p class="login-subtitle">卡牌对战游戏 - 管理后台</p>

      <form @submit.prevent="handleLogin" class="login-form">
        <van-cell-group inset class="login-fields">
          <van-field
            v-model="username"
            label="账号"
            placeholder="请输入管理员账号"
            left-icon="user-o"
            clearable
          />
          <van-field
            v-model="password"
            type="password"
            label="密码"
            placeholder="请输入密码"
            left-icon="lock"
            clearable
          />
        </van-cell-group>

        <van-button
          type="primary"
          block
          round
          size="large"
          :loading="loading"
          loading-text="登录中..."
          class="login-btn"
          native-type="submit"
        >
          登 录
        </van-button>
      </form>

      <div class="login-footer">
        <router-link to="/" class="back-link">返回游戏</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
}

.glass-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
}

.login-container {
  width: 100%;
  max-width: 420px;
  padding: 40px 24px;
}

.login-title {
  text-align: center;
  font-size: 1.75rem;
  margin-bottom: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-subtitle {
  text-align: center;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 32px;
  font-size: 0.875rem;
}

.login-form {
  margin-bottom: 24px;
}

.login-fields {
  background: transparent !important;
  margin-bottom: 24px;
}

.login-fields :deep(.van-cell) {
  background: rgba(255, 255, 255, 0.04);
  color: #fff;
}

.login-fields :deep(.van-field__label) {
  color: rgba(255, 255, 255, 0.7);
}

.login-fields :deep(.van-field__control) {
  color: #fff;
}

.login-fields :deep(.van-field__control::placeholder) {
  color: rgba(255, 255, 255, 0.3);
}

.login-fields :deep(.van-icon) {
  color: rgba(255, 255, 255, 0.5);
}

.login-btn {
  margin-top: 8px;
}

.login-footer {
  text-align: center;
}

.back-link {
  color: rgba(255, 255, 255, 0.5);
  text-decoration: none;
  font-size: 0.875rem;
  transition: color 0.2s;
}

.back-link:hover {
  color: #667eea;
}
</style>
