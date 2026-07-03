<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useUserStore } from '../store/user'
import { showToast } from 'vant'
import api from '../utils/api'
import { brawlApi } from '../utils/api'
import CardIcon from '../components/CardIcon.vue'
import BattleLogEntry from '../components/BattleLogEntry.vue'

const userStore = useUserStore()

// Battle card
const battleCard = ref(null)

// Brawl state
const brawlActive = ref(false)
const isMatching = ref(false)
const isBattling = ref(false)
const isDisconnected = ref(false)
const reconnectAttempts = ref(0)
const maxReconnectAttempts = 3

// Cumulative stats
const wins = ref(0)
const losses = ref(0)
const totalBattles = ref(0)
const currentStreak = ref(0)
const maxStreak = ref(0)
const totalRewards = ref(0)

// Current battle state
const playerName = ref('')
const opponentName = ref('')
const playerCard = ref(null)
const opponentCard = ref(null)
const playerCurrentHp = ref(0)
const playerMaxHp = ref(0)
const opponentCurrentHp = ref(0)
const opponentMaxHp = ref(0)
const battleLogs = ref([])
const playerShake = ref(false)
const opponentShake = ref(false)

// Battle log container
const logContainer = ref(null)

let ws = null
let reconnectTimer = null

// Computed
const winRate = computed(() => {
  if (totalBattles.value === 0) return '--'
  return Math.round((wins.value / totalBattles.value) * 100) + '%'
})

const playerHpPercent = computed(() => {
  if (playerMaxHp.value === 0) return 100
  return Math.max(0, (playerCurrentHp.value / playerMaxHp.value) * 100)
})

const opponentHpPercent = computed(() => {
  if (opponentMaxHp.value === 0) return 100
  return Math.max(0, (opponentCurrentHp.value / opponentMaxHp.value) * 100)
})

const brawlButtonColor = computed(() => brawlActive.value ? '#ef4444' : '#22c55e')
const brawlButtonText = computed(() => brawlActive.value ? '停止挂机' : '开始挂机')

// Load battle card
const loadBattleCard = async () => {
  try {
    const res = await api.get('/battle-card')
    battleCard.value = res.data.card
  } catch (e) {
    console.error('Failed to load battle card:', e)
  }
}

// Load brawl stats from REST
const loadStats = async () => {
  try {
    const res = await brawlApi.getStats()
    const data = res.data
    if (data) {
      wins.value = data.wins || 0
      losses.value = data.losses || 0
      totalBattles.value = data.total_battles || (wins.value + losses.value)
      currentStreak.value = data.current_streak || 0
      maxStreak.value = data.max_streak || 0
      totalRewards.value = data.total_rewards || 0
    }
  } catch (e) {
    // Stats may not exist yet
  }
}

// WebSocket connection
const connectWebSocket = () => {
  if (!battleCard.value) {
    showToast({ message: '请先设置出战卡片', type: 'fail' })
    return
  }

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/ws/pvp?token=${userStore.token}&card_id=${battleCard.value.id}`

  ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    isDisconnected.value = false
    reconnectAttempts.value = 0
    // Send brawl start command
    ws.send(JSON.stringify({ type: 'brawl_start' }))
    isMatching.value = true
  }

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      handleWsMessage(data)
    } catch (e) {
      console.error('Failed to parse WS message:', e)
    }
  }

  ws.onclose = () => {
    isMatching.value = false
    // Auto-reconnect if brawl is still active
    if (brawlActive.value && reconnectAttempts.value < maxReconnectAttempts) {
      isDisconnected.value = true
      const delay = Math.pow(2, reconnectAttempts.value) * 1000
      reconnectTimer = setTimeout(() => {
        reconnectAttempts.value++
        connectWebSocket()
      }, delay)
    } else if (brawlActive.value && reconnectAttempts.value >= maxReconnectAttempts) {
      isDisconnected.value = false
      brawlActive.value = false
      isBattling.value = false
      showToast({ message: '连接断开过多，挂机已停止', type: 'fail' })
    }
  }

  ws.onerror = () => {
    // Error handled by onclose
  }
}

// Handle WebSocket messages
const handleWsMessage = (data) => {
  switch (data.type) {
    case 'matching':
      isMatching.value = true
      isBattling.value = false
      break

    case 'matched':
      isMatching.value = false
      isBattling.value = true

      playerName.value = userStore.username
      opponentName.value = data.is_ai ? 'AI训练师' : data.opponent.name

      playerCard.value = data.my_card || battleCard.value
      opponentCard.value = data.opponent.card

      playerMaxHp.value = playerCard.value.hp
      playerCurrentHp.value = playerCard.value.hp
      opponentMaxHp.value = data.opponent.card.hp
      opponentCurrentHp.value = data.opponent.card.hp

      // Keep last N logs for preview
      battleLogs.value.push({ type: 'battle_start', text: `第 ${totalBattles.value + 1} 场战斗开始` })
      trimLogs()
      scrollToBottom()
      break

    case 'battle_log':
      if (typeof data.log === 'string') {
        try {
          const parsed = JSON.parse(data.log)
          if (Array.isArray(parsed)) {
            parsed.forEach(entry => battleLogs.value.push(entry))
          } else {
            battleLogs.value.push(parsed)
          }
        } catch {
          battleLogs.value.push({ type: 'text', text: data.log })
        }
      } else if (typeof data.log === 'object') {
        battleLogs.value.push(data.log)
      }

      parseBattleLog(data.log)
      trimLogs()
      scrollToBottom()
      break

    case 'hp_update':
      if (data.player !== undefined) {
        playerCurrentHp.value = Math.max(0, data.player.hp)
      }
      if (data.opponent !== undefined) {
        opponentCurrentHp.value = Math.max(0, data.opponent.hp)
      }
      break

    case 'battle_end':
      isBattling.value = false
      totalBattles.value++

      // Track stats
      if (data.result === 'win') {
        wins.value++
        currentStreak.value++
        if (currentStreak.value > maxStreak.value) {
          maxStreak.value = currentStreak.value
        }
      } else if (data.result === 'lose') {
        losses.value++
        currentStreak.value = 0
      }

      // Track rewards
      if (data.reward_gold) {
        totalRewards.value += data.reward_gold
        userStore.updateGold(data.reward_gold)
      }

      battleLogs.value.push({
        type: 'battle_end',
        text: `${data.result === 'win' ? '胜利' : data.result === 'lose' ? '失败' : '平局'} · 获得 ${data.reward_gold || 0} 卡金`
      })
      trimLogs()
      scrollToBottom()

      // Refresh user info periodically
      if (totalBattles.value % 5 === 0) {
        userStore.fetchUserInfo()
      }

      // Server auto-requeues in brawl mode; set matching state
      isMatching.value = true
      break

    case 'brawl_stats':
      // Server may send updated brawl stats
      if (data.wins !== undefined) wins.value = data.wins
      if (data.losses !== undefined) losses.value = data.losses
      if (data.total_battles !== undefined) totalBattles.value = data.total_battles
      if (data.current_streak !== undefined) currentStreak.value = data.current_streak
      if (data.max_streak !== undefined) maxStreak.value = data.max_streak
      if (data.total_rewards !== undefined) totalRewards.value = data.total_rewards
      break

    case 'error':
      showToast({ message: data.message || '发生错误', type: 'fail' })
      break
  }
}

// Parse battle log for HP/shake effects (same as Battle.vue)
const parseBattleLog = (log) => {
  const logText = typeof log === 'string' ? log : (log?.text || '')

  const damageMatch = logText.match(/造成\s*(\d+)\s*点伤害/)
  if (damageMatch) {
    const damage = parseInt(damageMatch[1])
    if (logText.includes(opponentName.value) || logText.includes(opponentCard.value?.name)) {
      if (logText.indexOf('对') < logText.indexOf(opponentName.value || opponentCard.value?.name || '')) {
        opponentCurrentHp.value = Math.max(0, opponentCurrentHp.value - damage)
        opponentShake.value = true
        setTimeout(() => opponentShake.value = false, 500)
      } else {
        playerCurrentHp.value = Math.max(0, playerCurrentHp.value - damage)
        playerShake.value = true
        setTimeout(() => playerShake.value = false, 500)
      }
    }
  }

  const healMatch = logText.match(/恢复\s*(\d+)\s*点生命/)
  if (healMatch) {
    const heal = parseInt(healMatch[1])
    if (logText.includes(playerName.value) || logText.includes(playerCard.value?.name)) {
      playerCurrentHp.value = Math.min(playerMaxHp.value, playerCurrentHp.value + heal)
    } else {
      opponentCurrentHp.value = Math.min(opponentMaxHp.value, opponentCurrentHp.value + heal)
    }
  }
}

// Keep log preview to a reasonable size
const trimLogs = () => {
  if (battleLogs.value.length > 50) {
    battleLogs.value = battleLogs.value.slice(-50)
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  })
}

// Start brawl
const startBrawl = () => {
  if (!battleCard.value) {
    showToast({ message: '请先设置出战卡片', type: 'fail' })
    return
  }

  brawlActive.value = true
  isMatching.value = false
  isBattling.value = false
  isDisconnected.value = false
  reconnectAttempts.value = 0
  battleLogs.value = []

  connectWebSocket()
}

// Stop brawl
const stopBrawl = () => {
  brawlActive.value = false
  isMatching.value = false
  isBattling.value = false
  isDisconnected.value = false

  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }

  if (ws) {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'brawl_stop' }))
    }
    ws.close()
    ws = null
  }

  // Refresh stats and user info
  loadStats()
  userStore.fetchUserInfo()
}

// Toggle brawl
const toggleBrawl = () => {
  if (brawlActive.value) {
    stopBrawl()
  } else {
    startBrawl()
  }
}

const resetStats = () => {
  wins.value = 0
  losses.value = 0
  totalBattles.value = 0
  currentStreak.value = 0
  maxStreak.value = 0
  totalRewards.value = 0
}

onMounted(() => {
  loadBattleCard()
  loadStats()
})

onUnmounted(() => {
  if (ws) {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'brawl_stop' }))
    }
    ws.close()
  }
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
  }
})
</script>

<template>
  <div class="brawl-page">
    <h1 class="page-title">挂机乱斗</h1>

    <!-- Idle state: show battle card and start button -->
    <div v-if="!brawlActive && !isMatching && !isBattling" class="brawl-setup glass-card">
      <h2 class="setup-heading">出战卡片</h2>
      <div class="queue-info">
        <van-icon name="info-o" size="14" />
        <span>挂机模式将自动连续匹配对战</span>
      </div>

      <div v-if="battleCard" class="selected-card">
        <CardIcon :image-id="battleCard.image" :category="battleCard.category" :name="battleCard.name" size="large" />
        <div class="selected-card-info">
          <div class="card-name">{{ battleCard.name }}</div>
          <van-tag :type="battleCard.rarity === '典藏' ? 'warning' : battleCard.rarity === '史诗' ? 'primary' : battleCard.rarity === '高级' ? 'success' : 'default'" plain>
            {{ battleCard.rarity }}
          </van-tag>
          <div class="card-stars">
            <van-rate v-model="battleCard.stars" readonly :count="battleCard.stars" :size="14" color="#fbbf24" />
          </div>
          <div class="card-level">Lv.{{ battleCard.level }}</div>
        </div>
      </div>

      <div v-else class="no-card">
        <p class="no-card-text">你还没有设置出战卡片</p>
        <van-button type="primary" plain size="small" @click="$router.push('/warehouse')">
          去仓库选择
        </van-button>
      </div>

      <van-button
        v-if="battleCard"
        type="primary"
        size="large"
        block
        class="brawl-start-btn"
        @click="startBrawl"
      >
        开始挂机
      </van-button>
    </div>

    <!-- Active brawl: stats + battle arena + log -->
    <template v-if="brawlActive || isMatching || isBattling">
      <!-- Control button -->
      <div class="brawl-control-bar glass-card">
        <div class="brawl-status-indicator">
          <span class="status-dot" :class="{ active: brawlActive }"></span>
          <span class="status-text">{{ isBattling ? '战斗中' : isMatching ? '匹配中' : '运行中' }}</span>
        </div>
        <van-button
          :type="brawlActive ? 'danger' : 'success'"
          round
          size="small"
          @click="toggleBrawl"
        >
          {{ brawlButtonText }}
        </van-button>
      </div>

      <!-- Stats overview -->
      <div class="stats-overview glass-card">
        <div class="stat-block win-block">
          <div class="stat-number">{{ wins }}</div>
          <div class="stat-label">胜利</div>
        </div>
        <div class="stat-block lose-block">
          <div class="stat-number">{{ losses }}</div>
          <div class="stat-label">失败</div>
        </div>
        <div class="stat-block streak-block">
          <div class="stat-number">{{ currentStreak }}</div>
          <div class="stat-label">连胜</div>
        </div>
        <div class="stat-block reward-block">
          <div class="stat-number gold">{{ totalRewards }}</div>
          <div class="stat-label">总收益</div>
        </div>
      </div>

      <!-- Secondary stats -->
      <div class="secondary-stats">
        <div class="secondary-stat">
          <van-icon name="chart-trending-o" size="14" color="#667eea" />
          <span>胜率 {{ winRate }}</span>
        </div>
        <div class="secondary-stat">
          <van-icon name="fire-o" size="14" color="#f5576c" />
          <span>最高连胜 {{ maxStreak }}</span>
        </div>
        <div class="secondary-stat">
          <van-icon name="medal-o" size="14" color="#fbbf24" />
          <span>总计 {{ totalBattles }} 场</span>
        </div>
      </div>

      <!-- Matching state -->
      <div v-if="isMatching && !isBattling" class="matching-section glass-card">
        <van-loading type="spinner" size="36px" color="#667eea" />
        <p class="matching-text">正在匹配对手...</p>
      </div>

      <!-- Battle arena -->
      <div v-if="isBattling" class="battle-arena-section">
        <div class="battle-arena">
          <!-- Player section -->
          <div class="battle-player">
            <div class="player-name">{{ playerName }}</div>
            <div class="battle-card player1" :class="{ shake: playerShake }">
              <CardIcon :image-id="playerCard?.image || ''" size="medium" />
              <div class="battle-card-name">{{ playerCard?.name }}</div>
            </div>
            <div class="hp-bar">
              <div
                class="hp-fill"
                :class="{ low: playerHpPercent < 30 }"
                :style="{ width: playerHpPercent + '%' }"
              ></div>
            </div>
            <div class="hp-text">{{ Math.round(playerCurrentHp) }} / {{ Math.round(playerMaxHp) }}</div>
          </div>

          <div class="vs-text">VS</div>

          <!-- Opponent section -->
          <div class="battle-player">
            <div class="player-name">{{ opponentName }}</div>
            <div class="battle-card player2" :class="{ shake: opponentShake }">
              <CardIcon :image-id="opponentCard?.image || ''" size="medium" />
              <div class="battle-card-name">{{ opponentCard?.name }}</div>
            </div>
            <div class="hp-bar">
              <div
                class="hp-fill"
                :class="{ low: opponentHpPercent < 30 }"
                :style="{ width: opponentHpPercent + '%' }"
              ></div>
            </div>
            <div class="hp-text">{{ Math.round(opponentCurrentHp) }} / {{ Math.round(opponentMaxHp) }}</div>
          </div>
        </div>
      </div>

      <!-- Battle log preview -->
      <div class="battle-log">
        <h3 class="battle-log-title">战斗日志</h3>
        <div ref="logContainer" class="battle-log-scroll">
          <BattleLogEntry
            v-for="(log, index) in battleLogs"
            :key="index"
            :entry="log"
          />
          <div v-if="battleLogs.length === 0" class="log-empty">
            等待战斗开始...
          </div>
        </div>
      </div>
    </template>

    <!-- Disconnected overlay -->
    <van-overlay :show="isDisconnected" z-index="200" class="disconnect-overlay">
      <div class="disconnect-content">
        <van-loading type="spinner" size="36px" color="#f5576c" />
        <p class="disconnect-text">连接断开</p>
        <p class="disconnect-sub">正在尝试重连 ({{ reconnectAttempts }}/{{ maxReconnectAttempts }})</p>
      </div>
    </van-overlay>

    <van-toast id="brawl-toast" />
  </div>
</template>

<style scoped>
.brawl-page {
  padding: 16px;
  padding-bottom: 80px;
  max-width: 600px;
  margin: 0 auto;
}

.page-title {
  text-align: center;
  font-size: 1.5rem;
  margin-bottom: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.glass-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  padding: 20px;
}

/* Setup */
.brawl-setup {
  text-align: center;
}

.setup-heading {
  margin-bottom: 12px;
  font-size: 1.1rem;
  color: rgba(255, 255, 255, 0.9);
}

.queue-info {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(102, 126, 234, 0.1);
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: 20px;
  padding: 6px 16px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 20px;
}

.selected-card {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 12px;
}

.selected-card-info {
  text-align: left;
}

.card-name {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 6px;
}

.card-stars {
  margin-top: 6px;
}

.card-level {
  color: rgba(255, 255, 255, 0.5);
  margin-top: 4px;
  font-size: 0.85rem;
}

.no-card {
  padding: 32px 0;
}

.no-card-text {
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 16px;
}

.brawl-start-btn {
  margin-top: 24px;
}

/* Control bar */
.brawl-control-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  margin-bottom: 16px;
}

.brawl-status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
}

.status-dot.active {
  background: #22c55e;
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.6);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 600;
}

/* Stats overview */
.stats-overview {
  display: flex;
  padding: 20px 12px;
  margin-bottom: 12px;
}

.stat-block {
  flex: 1;
  text-align: center;
  border-right: 1px solid rgba(255, 255, 255, 0.06);
}

.stat-block:last-child {
  border-right: none;
}

.stat-number {
  font-size: 1.5rem;
  font-weight: 800;
  color: #fff;
}

.stat-number.gold {
  color: #fbbf24;
}

.win-block .stat-number {
  color: #22c55e;
}

.lose-block .stat-number {
  color: #f5576c;
}

.streak-block .stat-number {
  color: #fbbf24;
}

.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 4px;
}

/* Secondary stats */
.secondary-stats {
  display: flex;
  justify-content: space-around;
  margin-bottom: 16px;
}

.secondary-stat {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
}

/* Matching section */
.matching-section {
  text-align: center;
  padding: 40px 20px;
  margin-bottom: 16px;
}

.matching-text {
  color: rgba(255, 255, 255, 0.6);
  margin-top: 12px;
  font-size: 14px;
}

/* Battle Arena */
.battle-arena-section {
  margin-bottom: 16px;
}

.battle-arena {
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 24px 16px;
  background: rgba(0, 0, 0, 0.25);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
}

.battle-player {
  text-align: center;
}

.player-name {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 12px;
  color: rgba(255, 255, 255, 0.9);
}

.battle-card {
  width: 120px;
  padding: 14px 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  border: 2px solid;
  transition: all 0.3s ease;
  background: linear-gradient(145deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.03) 100%);
}

.battle-card.player1 {
  border-color: #4facfe;
  box-shadow: 0 0 24px rgba(79, 172, 254, 0.4);
}

.battle-card.player2 {
  border-color: #f5576c;
  box-shadow: 0 0 24px rgba(245, 87, 108, 0.4);
}

.battle-card.shake {
  animation: shake 0.5s ease-in-out;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-8px); }
  75% { transform: translateX(8px); }
}

.battle-card-name {
  margin-top: 8px;
  font-size: 0.8rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
}

.hp-bar {
  width: 120px;
  height: 12px;
  background: rgba(0, 0, 0, 0.4);
  border-radius: 6px;
  overflow: hidden;
  margin-top: 12px;
}

.hp-fill {
  height: 100%;
  background: linear-gradient(90deg, #22c55e 0%, #16a34a 100%);
  transition: width 0.5s ease;
  border-radius: 6px;
}

.hp-fill.low {
  background: linear-gradient(90deg, #f5576c 0%, #ef4444 100%);
}

.hp-text {
  font-size: 0.75rem;
  margin-top: 4px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
}

.vs-text {
  font-size: 2rem;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* Battle Log */
.battle-log {
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 16px;
}

.battle-log-title {
  font-size: 0.95rem;
  margin-bottom: 12px;
  color: rgba(255, 255, 255, 0.7);
}

.battle-log-scroll {
  max-height: 200px;
  overflow-y: auto;
}

.log-empty {
  color: rgba(255, 255, 255, 0.3);
  font-size: 13px;
  text-align: center;
  padding: 20px 0;
}

/* Disconnect overlay */
.disconnect-overlay {
  background: rgba(0, 0, 0, 0.7);
}

.disconnect-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.disconnect-text {
  font-size: 1.2rem;
  font-weight: 600;
  color: #f5576c;
  margin-top: 16px;
}

.disconnect-sub {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 8px;
}

@media (max-width: 768px) {
  .battle-arena {
    flex-direction: column;
    gap: 16px;
  }

  .vs-text {
    font-size: 1.75rem;
  }

  .selected-card {
    flex-direction: column;
    gap: 12px;
  }

  .selected-card-info {
    text-align: center;
  }

  .stats-overview {
    flex-wrap: wrap;
  }

  .stat-block {
    min-width: 50%;
  }
}
</style>
