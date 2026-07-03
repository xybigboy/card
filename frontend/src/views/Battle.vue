<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useUserStore } from '../store/user'
import { useRouter } from 'vue-router'
import { showToast } from 'vant'
import api, { challengeApi } from '../utils/api'
import CardIcon from '../components/CardIcon.vue'
import BattleLogEntry from '../components/BattleLogEntry.vue'

const userStore = useUserStore()
const router = useRouter()

const battleCard = ref(null)
const isMatching = ref(false)
const isBattling = ref(false)
const battleResult = ref(null)
const matchingTime = ref(0)
const matchingTimer = ref(null)
const isDisconnected = ref(false)
const reconnectAttempts = ref(0)
const maxReconnectAttempts = 3
const queueSize = ref(0)
const queuePollTimer = ref(null)
const showAiOption = ref(false)
const aiLoading = ref(false)
const aiTimeout = ref(null)

// Challenge by name
const challengeUsername = ref('')
const challenging = ref(false)
const showChallengeResult = ref(false)
const challengeResult = ref(null)

const doChallenge = async () => {
  if (!challengeUsername.value.trim()) {
    showToast({ message: '请输入玩家名称', type: 'fail' })
    return
  }
  if (!battleCard.value) {
    showToast({ message: '请先设置出战卡片', type: 'fail' })
    return
  }
  challenging.value = true
  challengeResult.value = null
  try {
    const res = await challengeApi.byName(challengeUsername.value.trim())
    challengeResult.value = res.data
    showChallengeResult.value = true
    if (res.data.reward_gold) {
      userStore.updateGold(res.data.reward_gold)
    }
  } catch (e) {
    const msg = e.response?.data?.detail || e.response?.data?.message || '挑战失败'
    showToast({ message: msg, type: 'fail' })
  } finally {
    challenging.value = false
  }
}

// Battle state
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
const showResultPopup = ref(false)
const floatingDamages = ref([])
let damageId = 0
const playerSkillFlash = ref(false)
const opponentSkillFlash = ref(false)

let ws = null
let reconnectTimer = null
const logContainer = ref(null)

const playerHpPercent = computed(() => {
  if (playerMaxHp.value === 0) return 100
  return Math.max(0, (playerCurrentHp.value / playerMaxHp.value) * 100)
})

const opponentHpPercent = computed(() => {
  if (opponentMaxHp.value === 0) return 100
  return Math.max(0, (opponentCurrentHp.value / opponentMaxHp.value) * 100)
})

const resultColor = computed(() => {
  if (!battleResult.value) return '#667eea'
  switch (battleResult.value.result) {
    case 'win': return '#22c55e'
    case 'lose': return '#ef4444'
    default: return '#fbbf24'
  }
})

const resultTitle = computed(() => {
  if (!battleResult.value) return ''
  switch (battleResult.value.result) {
    case 'win': return '胜利'
    case 'lose': return '失败'
    default: return '平局'
  }
})

const loadBattleCard = async () => {
  try {
    const res = await api.get('/battle-card')
    battleCard.value = res.data.card
  } catch (e) {
    console.error(e)
  }
}

const fetchQueueSize = async () => {
  try {
    const res = await api.get('/matchmaking/queue-size')
    queueSize.value = res.data.queue_size
  } catch (e) {
    // ignore
  }
}

const startQueuePolling = () => {
  fetchQueueSize()
  queuePollTimer.value = setInterval(fetchQueueSize, 3000)
}

const stopQueuePolling = () => {
  if (queuePollTimer.value) {
    clearInterval(queuePollTimer.value)
    queuePollTimer.value = null
  }
}

const requestAiBattle = () => {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    showToast({ message: '连接已断开，请重新匹配', type: 'fail' })
    cancelMatching()
    return
  }
  ws.send(JSON.stringify({ type: 'ai_battle' }))
  showAiOption.value = false
  aiLoading.value = true

  // Timeout: if no matched response in 10s, reset
  aiTimeout.value = setTimeout(() => {
    if (aiLoading.value) {
      showToast({ message: 'AI对手准备失败，请重试', type: 'fail' })
      cancelMatching()
    }
  }, 10000)
}

const connectWebSocket = () => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const wsUrl = `${protocol}//${window.location.host}/ws/pvp?token=${userStore.token}&card_id=${battleCard.value.id}`

  ws = new WebSocket(wsUrl)

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      handleWsMessage(data)
    } catch (e) {
      console.error('Failed to parse WS message:', e)
    }
  }

  ws.onclose = () => {
    if (isBattling.value && reconnectAttempts.value < maxReconnectAttempts) {
      isDisconnected.value = true
      const delay = Math.pow(2, reconnectAttempts.value) * 1000
      reconnectTimer = setTimeout(() => {
        reconnectAttempts.value++
        connectWebSocket()
      }, delay)
    } else if (isMatching.value) {
      cancelMatching()
    }
  }

  ws.onerror = () => {
    showToast({ message: '连接失败，请重试', type: 'fail' })
    if (isMatching.value) {
      cancelMatching()
    }
  }

  ws.onopen = () => {
    isDisconnected.value = false
    reconnectAttempts.value = 0
  }
}

const startMatching = () => {
  if (!battleCard.value) {
    showToast({ message: '请先设置出战卡片', type: 'fail' })
    return
  }

  isMatching.value = true
  matchingTime.value = 0
  battleResult.value = null
  showResultPopup.value = false
  showAiOption.value = false
  battleLogs.value = []
  reconnectAttempts.value = 0
  isDisconnected.value = false

  matchingTimer.value = setInterval(() => {
    matchingTime.value++
    // Show AI option after 15 seconds of waiting
    if (matchingTime.value >= 15 && !showAiOption.value) {
      showAiOption.value = true
    }
  }, 1000)

  startQueuePolling()
  connectWebSocket()
}

const handleWsMessage = (data) => {
  switch (data.type) {
    case 'matching':
      break

    case 'matched':
      isMatching.value = false
      isBattling.value = true
      aiLoading.value = false
      if (aiTimeout.value) {
        clearTimeout(aiTimeout.value)
        aiTimeout.value = null
      }
      clearInterval(matchingTimer.value)
      stopQueuePolling()

      playerName.value = userStore.username
      opponentName.value = data.is_ai ? 'AI训练师' : data.opponent.name

      // 使用服务器返回的最新卡片数据（防止属性不一致）
      playerCard.value = data.my_card || battleCard.value
      opponentCard.value = data.opponent.card

      playerMaxHp.value = playerCard.value.hp
      playerCurrentHp.value = playerCard.value.hp
      opponentMaxHp.value = data.opponent.card.hp
      opponentCurrentHp.value = data.opponent.card.hp

      battleLogs.value.push({ type: 'battle_start', text: '战斗开始' })
      break

    case 'battle_log': {
      // Parse structured battle log entries
      let parsedLog = data.log
      if (typeof data.log === 'string') {
        try {
          parsedLog = JSON.parse(data.log)
        } catch {
          parsedLog = { type: 'text', text: data.log }
        }
      }

      if (Array.isArray(parsedLog)) {
        parsedLog.forEach(entry => {
          battleLogs.value.push(entry)
          parseBattleLog(entry)
        })
      } else if (typeof parsedLog === 'object') {
        battleLogs.value.push(parsedLog)
        parseBattleLog(parsedLog)
      } else {
        battleLogs.value.push({ type: 'text', text: String(data.log) })
        parseBattleLog({ type: 'text', text: String(data.log) })
      }
      scrollToBottom()
      break
    }

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
      battleResult.value = data
      showResultPopup.value = true

      userStore.updateGold(data.reward_gold)
      userStore.fetchUserInfo()

      if (ws) {
        ws.close()
        ws = null
      }
      break

    case 'error':
      showToast({ message: data.message || '发生错误', type: 'fail' })
      cancelMatching()
      break
  }
}

const showFloatingDamage = (target, amount, type = 'damage') => {
  const id = ++damageId
  const isPlayer = target === 'player'
  floatingDamages.value.push({
    id,
    target,
    amount,
    type,
    style: isPlayer ? 'player' : 'opponent'
  })
  setTimeout(() => {
    floatingDamages.value = floatingDamages.value.filter(d => d.id !== id)
  }, 1500)
}

const triggerSkillFlash = (target) => {
  if (target === 'player') {
    playerSkillFlash.value = true
    setTimeout(() => playerSkillFlash.value = false, 600)
  } else {
    opponentSkillFlash.value = true
    setTimeout(() => opponentSkillFlash.value = false, 600)
  }
}

const parseBattleLog = (log) => {
  const logObj = typeof log === 'object' ? log : {}
  const logText = typeof log === 'string' ? log : (log?.text || '')
  const logType = logObj.type || ''

  const isPlayer = (name) => name === playerCard.value?.name
  const isOpponent = (name) => name === opponentCard.value?.name

  // Skill trigger flash
  if (['heal', 'attack_buff', 'low_hp_buff', 'combo', 'stack_attack', 'critical_strike_ready',
       'bonus_damage', 'execute', 'stun', 'bleed', 'revive', 'dodge', 'speed_dodge'].includes(logType)) {
    const skillCard = logObj.card || logObj.skill || ''
    if (skillCard) {
      if (isPlayer(skillCard)) triggerSkillFlash('player')
      else if (isOpponent(skillCard)) triggerSkillFlash('opponent')
    }
  }

  // ATTACK: use structured defender_hp
  if (logType === 'attack' && logObj.defender_hp !== undefined) {
    const damage = logObj.damage || 0
    const isCritical = logObj.critical
    if (isOpponent(logObj.defender)) {
      opponentCurrentHp.value = Math.max(0, logObj.defender_hp)
      opponentShake.value = true
      showFloatingDamage('opponent', damage, isCritical ? 'critical' : 'damage')
      setTimeout(() => opponentShake.value = false, 500)
    } else if (isPlayer(logObj.defender)) {
      playerCurrentHp.value = Math.max(0, logObj.defender_hp)
      playerShake.value = true
      showFloatingDamage('player', damage, isCritical ? 'critical' : 'damage')
      setTimeout(() => playerShake.value = false, 500)
    }
    return
  }

  // EXECUTE: instant kill
  if (logType === 'execute' && logObj.defender) {
    if (isOpponent(logObj.defender)) {
      opponentCurrentHp.value = 0
      opponentShake.value = true
      showFloatingDamage('opponent', opponentMaxHp.value, 'critical')
      setTimeout(() => opponentShake.value = false, 500)
    } else if (isPlayer(logObj.defender)) {
      playerCurrentHp.value = 0
      playerShake.value = true
      showFloatingDamage('player', playerMaxHp.value, 'critical')
      setTimeout(() => playerShake.value = false, 500)
    }
    return
  }

  // LIFESTEAL: use attacker_hp
  if (logType === 'lifesteal' && logObj.attacker_hp !== undefined) {
    const heal = logObj.amount || 0
    if (isPlayer(logObj.card)) {
      playerCurrentHp.value = Math.min(playerMaxHp.value, logObj.attacker_hp)
      showFloatingDamage('player', heal, 'heal')
    } else if (isOpponent(logObj.card)) {
      opponentCurrentHp.value = Math.min(opponentMaxHp.value, logObj.attacker_hp)
      showFloatingDamage('opponent', heal, 'heal')
    }
    return
  }

  // HEAL / COMBO: use card_hp
  if ((logType === 'heal' || logType === 'combo') && logObj.card_hp !== undefined) {
    const healAmount = logType === 'combo' ? logObj.heal : logObj.amount
    if (isPlayer(logObj.card)) {
      playerCurrentHp.value = Math.min(playerMaxHp.value, logObj.card_hp)
      showFloatingDamage('player', healAmount || 0, 'heal')
    } else if (isOpponent(logObj.card)) {
      opponentCurrentHp.value = Math.min(opponentMaxHp.value, logObj.card_hp)
      showFloatingDamage('opponent', healAmount || 0, 'heal')
    }
    return
  }

  // BLEED_DAMAGE: use card_hp
  if (logType === 'bleed_damage' && logObj.card_hp !== undefined) {
    const damage = logObj.damage || 0
    if (isPlayer(logObj.card)) {
      playerCurrentHp.value = Math.max(0, logObj.card_hp)
      showFloatingDamage('player', damage, 'bleed')
    } else if (isOpponent(logObj.card)) {
      opponentCurrentHp.value = Math.max(0, logObj.card_hp)
      showFloatingDamage('opponent', damage, 'bleed')
    }
    return
  }

  // REVIVE: use card_hp
  if (logType === 'revive' && logObj.card_hp !== undefined) {
    if (isPlayer(logObj.card)) {
      playerCurrentHp.value = Math.min(playerMaxHp.value, logObj.card_hp)
      showFloatingDamage('player', logObj.card_hp, 'heal')
    } else if (isOpponent(logObj.card)) {
      opponentCurrentHp.value = Math.min(opponentMaxHp.value, logObj.card_hp)
      showFloatingDamage('opponent', logObj.card_hp, 'heal')
    }
    return
  }

  // ROUND_STATUS: sync both HPs
  if (logType === 'round_status') {
    if (logObj.player1 && isPlayer(logObj.player1.name)) {
      playerCurrentHp.value = Math.max(0, logObj.player1.hp)
      opponentCurrentHp.value = Math.max(0, logObj.player2.hp)
    } else if (logObj.player1 && isOpponent(logObj.player1.name)) {
      opponentCurrentHp.value = Math.max(0, logObj.player1.hp)
      playerCurrentHp.value = Math.max(0, logObj.player2.hp)
    }
    return
  }

  // FALLBACK: regex for backward compatibility
  const damageMatch = logText.match(/造成\s*(\d+\.?\d*)\s*点伤害/)
  if (damageMatch) {
    const damage = parseFloat(damageMatch[1])
    const isCritical = logText.includes('暴击')
    if (logText.includes(opponentCard.value?.name) && logText.indexOf('对') < logText.indexOf(opponentCard.value?.name || '')) {
      opponentCurrentHp.value = Math.max(0, opponentCurrentHp.value - damage)
      opponentShake.value = true
      showFloatingDamage('opponent', damage, isCritical ? 'critical' : 'damage')
      setTimeout(() => opponentShake.value = false, 500)
    } else {
      playerCurrentHp.value = Math.max(0, playerCurrentHp.value - damage)
      playerShake.value = true
      showFloatingDamage('player', damage, isCritical ? 'critical' : 'damage')
      setTimeout(() => playerShake.value = false, 500)
    }
  }

  const healMatch = logText.match(/恢复\s*(\d+\.?\d*)\s*点生命/)
  if (healMatch) {
    const heal = parseFloat(healMatch[1])
    if (logText.includes(playerCard.value?.name)) {
      playerCurrentHp.value = Math.min(playerMaxHp.value, playerCurrentHp.value + heal)
      showFloatingDamage('player', heal, 'heal')
    } else {
      opponentCurrentHp.value = Math.min(opponentMaxHp.value, opponentCurrentHp.value + heal)
      showFloatingDamage('opponent', heal, 'heal')
    }
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (logContainer.value) {
      logContainer.value.scrollTop = logContainer.value.scrollHeight
    }
  })
}

const cancelMatching = () => {
  isMatching.value = false
  showAiOption.value = false
  aiLoading.value = false
  if (aiTimeout.value) {
    clearTimeout(aiTimeout.value)
    aiTimeout.value = null
  }
  clearInterval(matchingTimer.value)
  stopQueuePolling()

  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }

  if (ws) {
    ws.close()
    ws = null
  }
}

const resetBattle = () => {
  battleResult.value = null
  showResultPopup.value = false
  isBattling.value = false
  battleLogs.value = []
  loadBattleCard()
}

onMounted(() => {
  loadBattleCard()
  startQueuePolling()
})

onUnmounted(() => {
  if (ws) {
    ws.close()
  }
  if (matchingTimer.value) {
    clearInterval(matchingTimer.value)
  }
  if (aiTimeout.value) {
    clearTimeout(aiTimeout.value)
  }
  stopQueuePolling()
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
  }
})
</script>

<template>
  <div class="battle-page">
    <h1 class="page-title">实时对战</h1>

    <!-- Idle state: show battle card and match button -->
    <div v-if="!isMatching && !isBattling && !battleResult" class="battle-setup glass-card">
      <h2 class="setup-heading">选择出战卡片</h2>
      <div class="queue-info">
        <van-icon name="friends-o" size="14" />
        <span>当前在线等待: <strong>{{ queueSize }}</strong> 人</span>
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
        <van-button type="primary" plain size="small" @click="router.push('/warehouse')">
          去仓库选择
        </van-button>
      </div>

      <van-button
        v-if="battleCard"
        type="primary"
        size="large"
        block
        class="match-btn"
        @click="startMatching"
      >
        开始匹配
      </van-button>

      <!-- 指名挑战 -->
      <div v-if="battleCard" class="challenge-section">
        <van-divider>指名挑战</van-divider>
        <div class="challenge-input-row">
          <van-field
            v-model="challengeUsername"
            placeholder="输入玩家名称"
            class="challenge-input"
            :disabled="challenging"
          />
          <van-button
            type="primary"
            size="small"
            :loading="challenging"
            @click="doChallenge"
          >
            挑战
          </van-button>
        </div>
        <p class="challenge-hint">输入对手玩家名进行离线挑战（不影响积分）</p>
      </div>

      <!-- 乱斗模式入口 -->
      <div v-if="battleCard" class="brawl-entry-section">
        <van-divider>更多模式</van-divider>
        <div class="mode-entry-row">
          <div class="mode-entry-card" @click="router.push('/brawl')">
            <van-icon name="aiming" size="28" color="#f59e0b" />
            <span class="mode-entry-name">大乱斗</span>
            <span class="mode-entry-desc">自动连战 · 挂机收益</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Challenge result popup -->
    <van-popup
      v-model:show="showChallengeResult"
      round
      :close-on-click-overlay="false"
      position="center"
      class="result-popup"
    >
      <div class="battle-result" v-if="challengeResult">
        <div class="result-icon" :style="{ color: challengeResult.result === 'win' ? '#22c55e' : challengeResult.result === 'lose' ? '#ef4444' : '#fbbf24' }">
          <van-icon
            :name="challengeResult.result === 'win' ? 'medal-o' : challengeResult.result === 'lose' ? 'close' : 'balance-o'"
            size="64"
          />
        </div>
        <h2 class="result-title" :style="{ color: challengeResult.result === 'win' ? '#22c55e' : challengeResult.result === 'lose' ? '#ef4444' : '#fbbf24' }">
          {{ challengeResult.result === 'win' ? '胜利' : challengeResult.result === 'lose' ? '失败' : '平局' }}
        </h2>
        <p class="challenge-opponent">对手: {{ challengeResult.opponent_name }}</p>
        <div class="result-rewards">
          <div class="reward-item">
            <span class="reward-label">获得卡金</span>
            <span class="reward-value gold">+{{ challengeResult.reward_gold }}</span>
          </div>
          <div class="reward-item">
            <span class="reward-label">战斗回合</span>
            <span class="reward-value">{{ challengeResult.duration_rounds }}</span>
          </div>
        </div>
        <div class="challenge-logs" v-if="challengeResult.battle_logs">
          <BattleLogEntry
            v-for="(log, i) in challengeResult.battle_logs.slice(-10)"
            :key="i"
            :entry="log"
          />
        </div>
        <van-button type="primary" block @click="showChallengeResult = false" class="close-challenge-btn">
          关闭
        </van-button>
      </div>
    </van-popup>

    <!-- Matching state -->
    <div v-if="isMatching" class="matching glass-card">
      <div class="matching-animation">
        <van-loading type="spinner" size="48px" color="#667eea" />
      </div>
      <h2 class="matching-title">匹配中...</h2>
      <p class="matching-time">
        匹配时间: {{ matchingTime }}s · 队列等待: {{ queueSize }} 人
      </p>

      <div v-if="aiLoading" class="ai-option">
        <van-loading type="spinner" size="32px" color="#f59e0b" />
        <p class="ai-hint">正在准备AI对手...</p>
      </div>

      <div v-else-if="showAiOption" class="ai-option">
        <p class="ai-hint">暂无对手，是否挑战AI训练师？</p>
        <p class="ai-note">AI战斗奖励减半，不影响积分</p>
        <button class="ai-battle-btn" @click="requestAiBattle">
          挑战AI
        </button>
      </div>

      <button class="cancel-match-btn" @click="cancelMatching">
        取消匹配
      </button>
    </div>

    <!-- Battle state -->
    <div v-if="isBattling" class="battle-arena-section">
      <div class="battle-arena">
        <!-- Player section -->
        <div class="battle-player">
          <div class="player-name">{{ playerName }}</div>
          <div class="battle-card player1" :class="{ shake: playerShake, 'skill-flash': playerSkillFlash }">
            <CardIcon :image-id="playerCard?.image || ''" :category="playerCard?.category" :name="playerCard?.name" size="medium" />
            <div class="battle-card-name">{{ playerCard?.name }}</div>
            <div class="card-stats-row">
              <span class="stat atk">ATK {{ Math.round(playerCard?.attack || 0) }}</span>
              <span class="stat def">DEF {{ Math.round(playerCard?.defense || 0) }}</span>
              <span class="stat spd">SPD {{ Math.round(playerCard?.speed || 0) }}</span>
            </div>
          </div>
          <!-- Floating damage numbers -->
          <div class="floating-damage-container">
            <div
              v-for="d in floatingDamages.filter(d => d.target === 'player')"
              :key="d.id"
              class="floating-damage"
              :class="d.type"
            >
              {{ d.type === 'heal' ? '+' : '-' }}{{ Math.round(d.amount) }}
            </div>
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
          <div class="battle-card player2" :class="{ shake: opponentShake, 'skill-flash': opponentSkillFlash }">
            <CardIcon :image-id="opponentCard?.image || ''" :category="opponentCard?.category" :name="opponentCard?.name" size="medium" />
            <div class="battle-card-name">{{ opponentCard?.name }}</div>
            <div class="card-stats-row">
              <span class="stat atk">ATK {{ Math.round(opponentCard?.attack || 0) }}</span>
              <span class="stat def">DEF {{ Math.round(opponentCard?.defense || 0) }}</span>
              <span class="stat spd">SPD {{ Math.round(opponentCard?.speed || 0) }}</span>
            </div>
          </div>
          <!-- Floating damage numbers -->
          <div class="floating-damage-container">
            <div
              v-for="d in floatingDamages.filter(d => d.target === 'opponent')"
              :key="d.id"
              class="floating-damage"
              :class="d.type"
            >
              {{ d.type === 'heal' ? '+' : '-' }}{{ Math.round(d.amount) }}
            </div>
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

      <!-- Battle log -->
      <div class="battle-log">
        <h3 class="battle-log-title">战斗日志</h3>
        <div ref="logContainer" class="battle-log-scroll">
          <BattleLogEntry
            v-for="(log, index) in battleLogs"
            :key="index"
            :entry="log"
          />
        </div>
      </div>
    </div>

    <!-- Disconnected overlay -->
    <van-overlay :show="isDisconnected" z-index="200" class="disconnect-overlay">
      <div class="disconnect-content">
        <van-loading type="spinner" size="36px" color="#f5576c" />
        <p class="disconnect-text">连接断开</p>
        <p class="disconnect-sub">正在尝试重连 ({{ reconnectAttempts }}/{{ maxReconnectAttempts }})</p>
      </div>
    </van-overlay>

    <!-- Result popup -->
    <van-popup
      v-model:show="showResultPopup"
      round
      :close-on-click-overlay="false"
      position="center"
      class="result-popup"
    >
      <div class="battle-result" v-if="battleResult">
        <div class="result-icon" :style="{ color: resultColor }">
          <van-icon
            :name="battleResult.result === 'win' ? 'medal-o' : battleResult.result === 'lose' ? 'close' : 'balance-o'"
            size="64"
            :color="resultColor"
          />
        </div>

        <h2 class="result-title" :style="{ color: resultColor }">
          {{ resultTitle }}
        </h2>
        <div v-if="battleResult.is_ai" class="ai-badge">AI对战</div>

        <div class="result-rewards">
          <div class="reward-item">
            <span class="reward-label">获得卡金</span>
            <span class="reward-value gold">+{{ battleResult.reward_gold }}</span>
          </div>

          <div v-if="battleResult.rating_change" class="reward-item">
            <span class="reward-label">积分变化</span>
            <span
              class="reward-value"
              :class="battleResult.rating_change > 0 ? 'positive' : 'negative'"
            >
              {{ battleResult.rating_change > 0 ? '+' : '' }}{{ battleResult.rating_change }}
            </span>
          </div>

          <div v-if="battleResult.stole_card" class="reward-item highlight">
            <span class="reward-label">掠夺卡片</span>
            <span class="reward-value gold">{{ battleResult.stole_card_name }}</span>
          </div>

          <div v-if="battleResult.card_stolen" class="reward-item negative-row">
            <span class="reward-label">卡片被掠夺</span>
            <span class="reward-value negative">-{{ battleResult.stolen_card_name }}</span>
          </div>
        </div>

        <div class="result-actions">
          <van-button type="primary" plain @click="resetBattle">
            返回
          </van-button>
          <van-button v-if="battleCard" type="primary" @click="resetBattle(); startMatching()">
            再来一局
          </van-button>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<style scoped>
.battle-page {
  padding: 16px;
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
  padding: 24px;
}

/* Setup */
.battle-setup {
  text-align: center;
  max-width: 500px;
  margin: 0 auto;
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

.queue-info strong {
  color: #667eea;
  font-size: 15px;
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

.match-btn {
  margin-top: 24px;
}

/* Matching */
.matching {
  text-align: center;
  max-width: 400px;
  margin: 0 auto;
  padding: 48px 20px;
}

.matching-animation {
  margin-bottom: 24px;
}

.matching-title {
  font-size: 1.25rem;
  color: rgba(255, 255, 255, 0.9);
}

.matching-time {
  color: rgba(255, 255, 255, 0.5);
  margin: 12px 0 20px;
}

.cancel-match-btn {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 10px 32px;
  border-radius: 24px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s;
}
.cancel-match-btn:active {
  background: rgba(255, 255, 255, 0.2);
}

.ai-option {
  margin: 16px 0;
  padding: 16px;
  background: rgba(251, 191, 36, 0.08);
  border: 1px solid rgba(251, 191, 36, 0.2);
  border-radius: 12px;
}

.ai-hint {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0 0 4px;
}

.ai-note {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  margin: 0 0 12px;
}

.ai-battle-btn {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: #fff;
  border: none;
  padding: 10px 32px;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.ai-battle-btn:active {
  opacity: 0.8;
}

/* Battle Arena */
.battle-arena-section {
  margin-bottom: 24px;
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
  margin-bottom: 16px;
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
  width: 140px;
  padding: 16px 12px;
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
  font-size: 0.85rem;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
}

.hp-bar {
  width: 140px;
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
  font-size: 2.5rem;
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
  max-height: 240px;
  overflow-y: auto;
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

/* Result popup */
.result-popup {
  background: transparent !important;
  max-width: 420px;
  width: 90vw;
}

.battle-result {
  text-align: center;
  padding: 32px 24px;
  background: rgba(20, 20, 40, 0.95);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
}

.result-icon {
  margin-bottom: 16px;
}

.result-title {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 12px;
}

.ai-badge {
  display: inline-block;
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
  font-size: 12px;
  padding: 3px 12px;
  border-radius: 12px;
  margin-bottom: 16px;
}

.result-rewards {
  background: rgba(255, 255, 255, 0.04);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 24px;
}

.reward-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.reward-item:last-child {
  border-bottom: none;
}

.reward-label {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
}

.reward-value {
  font-weight: 600;
  font-size: 0.95rem;
}

.reward-value.gold {
  color: #fbbf24;
}

.reward-value.positive {
  color: #22c55e;
}

.reward-value.negative {
  color: #f5576c;
}

.reward-item.highlight {
  background: rgba(251, 191, 36, 0.08);
  margin: 8px -16px;
  padding: 12px 16px;
  border-radius: 8px;
}

.reward-item.negative-row {
  background: rgba(245, 87, 108, 0.08);
  margin: 8px -16px;
  padding: 12px 16px;
  border-radius: 8px;
}

.result-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

/* Card Stats Row */
.card-stats-row {
  display: flex;
  gap: 6px;
  margin-top: 6px;
  justify-content: center;
}

.card-stats-row .stat {
  font-size: 0.65rem;
  padding: 2px 6px;
  border-radius: 8px;
  font-weight: 600;
}

.card-stats-row .stat.atk {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.card-stats-row .stat.def {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.card-stats-row .stat.spd {
  background: rgba(168, 85, 247, 0.15);
  color: #a855f7;
}

/* Skill Flash Effect */
.battle-card.skill-flash {
  animation: skillFlash 0.6s ease-out;
}

@keyframes skillFlash {
  0% { box-shadow: 0 0 24px rgba(255, 255, 0, 0.8); border-color: #fbbf24; }
  50% { box-shadow: 0 0 40px rgba(255, 255, 0, 0.6); border-color: #fbbf24; }
  100% { box-shadow: 0 0 24px rgba(79, 172, 254, 0.4); }
}

.battle-card.player1.skill-flash {
  animation: skillFlashBlue 0.6s ease-out;
}

.battle-card.player2.skill-flash {
  animation: skillFlashRed 0.6s ease-out;
}

@keyframes skillFlashBlue {
  0% { box-shadow: 0 0 40px rgba(102, 126, 234, 0.9); border-color: #667eea; transform: scale(1.05); }
  100% { box-shadow: 0 0 24px rgba(79, 172, 254, 0.4); transform: scale(1); }
}

@keyframes skillFlashRed {
  0% { box-shadow: 0 0 40px rgba(245, 87, 108, 0.9); border-color: #f5576c; transform: scale(1.05); }
  100% { box-shadow: 0 0 24px rgba(245, 87, 108, 0.4); transform: scale(1); }
}

/* Floating Damage Numbers */
.floating-damage-container {
  position: relative;
  height: 0;
  overflow: visible;
  z-index: 10;
}

.floating-damage {
  position: absolute;
  top: -60px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 1.8rem;
  font-weight: 800;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.8);
  animation: floatUp 1.5s ease-out forwards;
  pointer-events: none;
}

.floating-damage.damage {
  color: #ef4444;
}

.floating-damage.critical {
  color: #fbbf24;
  font-size: 2.4rem;
  text-shadow: 0 0 12px rgba(251, 191, 36, 0.6), 0 2px 8px rgba(0, 0, 0, 0.8);
}

.floating-damage.heal {
  color: #22c55e;
}

.floating-damage.bleed {
  color: #dc2626;
  font-size: 1.4rem;
}

@keyframes floatUp {
  0% {
    opacity: 0;
    transform: translateX(-50%) translateY(0) scale(0.5);
  }
  20% {
    opacity: 1;
    transform: translateX(-50%) translateY(-20px) scale(1.2);
  }
  100% {
    opacity: 0;
    transform: translateX(-50%) translateY(-80px) scale(1);
  }
}

/* Brawl Entry Section */
.brawl-entry-section {
  margin-top: 20px;
  text-align: left;
}

.mode-entry-row {
  display: flex;
  gap: 12px;
}

.mode-entry-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 16px;
  background: rgba(245, 158, 11, 0.08);
  border: 1px solid rgba(245, 158, 11, 0.2);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-entry-card:active {
  transform: scale(0.97);
  background: rgba(245, 158, 11, 0.12);
}

.mode-entry-name {
  font-size: 0.95rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.mode-entry-desc {
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.4);
}

/* Challenge Section */
.challenge-section {
  margin-top: 24px;
  text-align: left;
}

.challenge-input-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.challenge-input {
  flex: 1;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  padding: 6px 12px;
}

.challenge-hint {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
  margin: 8px 0 0;
  text-align: center;
}

.challenge-opponent {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
  margin: 8px 0 16px;
}

.challenge-logs {
  max-height: 200px;
  overflow-y: auto;
  margin: 12px 0 16px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  padding: 8px;
}

.close-challenge-btn {
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

  .result-actions {
    flex-direction: column;
  }
}
</style>
