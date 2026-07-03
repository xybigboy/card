<script setup>
import { computed } from 'vue'

const props = defineProps({
  entry: { type: [Object, String], required: true },
})

const parsed = computed(() => {
  if (typeof props.entry === 'string') {
    return { type: 'text', text: props.entry }
  }
  return props.entry
})

const typeConfig = {
  battle_start: { color: '#667eea', icon: '▶', label: '开始' },
  round: { color: '#aaa', icon: '○', label: '回合' },
  attack: { color: '#ff6b6b', icon: '[x]', label: '攻击' },
  skill: { color: '#ffd93d', icon: '◆', label: '技能' },
  heal: { color: '#51cf66', icon: '+', label: '治疗' },
  buff: { color: '#4facfe', icon: '↑', label: '增益' },
  debuff: { color: '#f093fb', icon: '↓', label: '减益' },
  critical: { color: '#ff4757', icon: '!!', label: '暴击' },
  dodge: { color: '#a29bfe', icon: '~', label: '闪避' },
  stun: { color: '#ffa502', icon: '!', label: '眩晕' },
  bleed: { color: '#e74c3c', icon: '✕', label: '流血' },
  lifesteal: { color: '#e91e63', icon: '<3', label: '吸血' },
  revive: { color: '#00d2d3', icon: '↻', label: '复活' },
  execute: { color: '#c0392b', icon: '×', label: '斩杀' },
  bonus_damage: { color: '#f39c12', icon: '★', label: '加伤' },
  combo: { color: '#e67e22', icon: '»', label: '连击' },
  battle_end: { color: '#2ecc71', icon: '■', label: '结束' },
  text: { color: '#ccc', icon: '', label: '' },
}

const config = computed(() => typeConfig[parsed.value.type] || typeConfig.text)
</script>

<template>
  <div class="battle-log-entry" :class="'battle-log-entry--' + parsed.type">
    <span v-if="config.icon" class="battle-log-entry__icon" :style="{ color: config.color }">
      [{{ config.icon }}]
    </span>
    <span class="battle-log-entry__text">{{ parsed.text }}</span>
  </div>
</template>

<style scoped>
.battle-log-entry {
  padding: 4px 8px;
  font-size: 0.85rem;
  line-height: 1.5;
  border-left: 3px solid transparent;
  margin-bottom: 2px;
}
.battle-log-entry--battle_start { border-left-color: #667eea; background: rgba(102, 126, 234, 0.1); }
.battle-log-entry--battle_end { border-left-color: #2ecc71; background: rgba(46, 204, 113, 0.1); }
.battle-log-entry--critical { border-left-color: #ff4757; background: rgba(255, 71, 87, 0.1); }
.battle-log-entry--heal { border-left-color: #51cf66; }
.battle-log-entry--round { opacity: 0.6; font-size: 0.75rem; }
.battle-log-entry__icon {
  font-weight: bold;
  margin-right: 6px;
  font-family: monospace;
  display: inline-block;
  min-width: 24px;
  text-align: center;
}
.battle-log-entry__text {
  color: rgba(255, 255, 255, 0.85);
}
</style>
