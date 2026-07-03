<template>
  <div class="register-container">
    <div class="register-bg-pattern"></div>
    <div class="register-card">
      <h1 class="game-title">创建账号</h1>
      <p class="subtitle">新用户赠送 10 次免费抽卡机会</p>

      <van-form @submit="handleRegister" class="register-form">
        <van-cell-group :border="false" class="dark-cell-group">
          <van-field
            v-model="username"
            name="username"
            placeholder="请输入用户名"
            left-icon="manager-o"
            :rules="[
              { required: true, message: '请输入用户名' },
              { validator: validateUsername, message: '用户名至少3个字符' }
            ]"
            class="dark-field"
          />
          <van-field
            v-model="password"
            type="password"
            name="password"
            placeholder="请输入密码"
            left-icon="lock"
            :rules="[
              { required: true, message: '请输入密码' },
              { validator: validatePassword, message: '密码至少6个字符' }
            ]"
            class="dark-field"
          />
          <van-field
            v-model="confirmPassword"
            type="password"
            name="confirmPassword"
            placeholder="请确认密码"
            left-icon="shield-o"
            :rules="[
              { required: true, message: '请确认密码' },
              { validator: validateConfirmPassword, message: '两次密码不一致' }
            ]"
            class="dark-field"
          />
        </van-cell-group>

        <div class="form-actions">
          <van-button
            type="primary"
            block
            round
            native-type="submit"
            :loading="loading"
            loading-text="注册中..."
            class="register-btn"
          >
            注册
          </van-button>
          <van-button
            plain
            type="default"
            block
            round
            @click="$router.push('/login')"
            class="login-link-btn"
          >
            去登录
          </van-button>
        </div>
      </van-form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../store/user'
import { showSuccessToast, showFailToast } from 'vant'
import 'vant/es/toast/style'

const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)

const router = useRouter()
const userStore = useUserStore()

const validateUsername = (val) => val.length >= 3
const validatePassword = (val) => val.length >= 6
const validateConfirmPassword = (val) => val === password.value

const handleRegister = async () => {
  loading.value = true

  try {
    await userStore.register(username.value, password.value)
    showSuccessToast('注册成功')
    router.push('/')
  } catch (e) {
    showFailToast(e || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 20px;
  position: relative;
  overflow: hidden;
}

.register-bg-pattern {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(circle at 80% 50%, rgba(102, 126, 234, 0.15) 0%, transparent 50%),
    radial-gradient(circle at 20% 80%, rgba(118, 75, 162, 0.15) 0%, transparent 50%),
    radial-gradient(circle at 50% 20%, rgba(240, 147, 251, 0.1) 0%, transparent 50%);
  pointer-events: none;
}

.register-card {
  width: 100%;
  max-width: 400px;
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 40px 30px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  position: relative;
  z-index: 1;
}

.game-title {
  text-align: center;
  font-size: 32px;
  font-weight: 800;
  margin-bottom: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 4px;
}

.subtitle {
  text-align: center;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 32px;
  font-size: 14px;
}

.register-form {
  margin-top: 10px;
}

.dark-cell-group {
  background: transparent !important;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 24px;
}

:deep(.dark-field) {
  background: rgba(255, 255, 255, 0.06) !important;
  margin-bottom: 12px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

:deep(.dark-field .van-field__control) {
  color: #fff;
}

:deep(.dark-field .van-field__control::placeholder) {
  color: rgba(255, 255, 255, 0.35);
}

:deep(.dark-field .van-icon) {
  color: rgba(255, 255, 255, 0.5);
}

:deep(.van-cell) {
  background: transparent;
  color: #fff;
}

:deep(.van-cell::after) {
  display: none;
}

:deep(.van-field__error-message) {
  color: #f093fb;
}

.form-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.register-btn {
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  letter-spacing: 2px;
}

.login-link-btn {
  height: 44px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7) !important;
  border-color: rgba(255, 255, 255, 0.15) !important;
  background: transparent !important;
}

.login-link-btn:hover {
  border-color: rgba(102, 126, 234, 0.5) !important;
  color: #667eea !important;
}
</style>
