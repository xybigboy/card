<script setup>
import { computed, ref } from 'vue'
import { cardCategories, cardNames, categoryColors, categoryNameMap, imagePrefixMap } from '../utils/icons'

const props = defineProps({
  imageId: { type: String, default: 'card-default' },
  size: { type: String, default: 'medium' }, // small, medium, large
  category: { type: String, default: '' },   // Chinese category name (e.g. "龙珠")
  name: { type: String, default: '' },        // Card name for initial character
})

// Image preview state
const showPreview = ref(false)
const openPreview = () => {
  if (isImageUrl.value) showPreview.value = true
}

// Check if imageId is a URL or local image path
const isImageUrl = computed(() => {
  return !!(props.imageId && (
    props.imageId.startsWith('http://') ||
    props.imageId.startsWith('https://') ||
    props.imageId.startsWith('/images/')
  ))
})

// Resolve category slug: try imageId lookup, then prefix, then Chinese name
const categorySlug = computed(() => {
  // 1. Exact image ID match
  if (cardCategories[props.imageId]) return cardCategories[props.imageId]
  // 2. Prefix match (e.g. "db-goku" → "dragon-ball")
  for (const [prefix, slug] of Object.entries(imagePrefixMap)) {
    if (props.imageId.startsWith(prefix)) return slug
  }
  // 3. Chinese category name match
  if (props.category && categoryNameMap[props.category]) return categoryNameMap[props.category]
  // 4. Fallback
  return 'other'
})

const colors = computed(() => categoryColors[categorySlug.value] || ['#667eea', '#764ba2'])

// Resolve name and initial
const nameInfo = computed(() => {
  // 1. Exact image ID match
  if (cardNames[props.imageId]) return cardNames[props.imageId]
  // 2. Use card name first character
  if (props.name) return { name: props.name, initial: props.name.charAt(0) }
  // 3. Fallback
  return { name: '未知', initial: '?' }
})

const sizeMap = { small: '60px', medium: '80px', large: '120px' }
const fontSizeMap = { small: '1.5rem', medium: '2rem', large: '3rem' }
const iconSizeMap = { small: '16px', medium: '20px', large: '28px' }

const containerStyle = computed(() => ({
  width: sizeMap[props.size],
  height: sizeMap[props.size],
  background: `linear-gradient(135deg, ${colors.value[0]}, ${colors.value[1]})`,
  borderRadius: '12px',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  justifyContent: 'center',
  boxShadow: `0 4px 15px ${colors.value[0]}40`,
  position: 'relative',
  overflow: 'hidden',
}))

const initialStyle = computed(() => ({
  fontSize: fontSizeMap[props.size],
  fontWeight: 'bold',
  color: '#fff',
  textShadow: '0 2px 4px rgba(0,0,0,0.3)',
  lineHeight: '1',
}))

const categoryLabel = computed(() => {
  const labels = {
    'dragon-ball': '龙珠',
    'naruto': '火影',
    'ultraman': '奥特曼',
    'one-piece': '海贼王',
    'demon-slayer': '鬼灭',
    'pokemon': '宝可梦',
    'detective': '侦探',
    'other': '',
  }
  // Use the Chinese category prop directly if available
  if (props.category) return props.category
  return labels[categorySlug.value] || ''
})
</script>

<template>
  <div class="card-icon" :style="containerStyle">
    <img
      v-if="isImageUrl"
      :src="imageId"
      class="card-icon__img card-icon__img--clickable"
      :style="{ width: sizeMap[size], height: sizeMap[size] }"
      alt="card"
      @click.stop="openPreview"
    />
    <template v-else>
      <div class="card-icon__initial" :style="initialStyle">{{ nameInfo.initial }}</div>
      <div class="card-icon__category" v-if="categoryLabel">{{ categoryLabel }}</div>
    </template>
    <div class="card-icon__shine"></div>

    <!-- Full-screen image preview -->
    <van-popup
      v-model:show="showPreview"
      closeable
      close-icon="cross"
      round
      :style="{ maxWidth: '90vw', maxHeight: '85vh', background: 'transparent', boxShadow: 'none' }"
      class="card-preview-popup"
    >
      <div class="card-preview-inner">
        <div class="card-preview-title">{{ name }}</div>
        <img
          :src="imageId"
          :alt="name"
          class="card-preview-large"
        />
      </div>
    </van-popup>
  </div>
</template>

<style scoped>
.card-icon {
  position: relative;
  overflow: hidden;
}
.card-icon__img {
  border-radius: 12px;
  object-fit: cover;
  display: block;
}
.card-icon__img--clickable {
  cursor: zoom-in;
  transition: transform 0.2s ease;
}
.card-icon__img--clickable:hover {
  transform: scale(1.05);
}
.card-icon__category {
  font-size: 0.6rem;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 4px;
  letter-spacing: 1px;
}
.card-icon__shine {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: linear-gradient(
    45deg,
    transparent 40%,
    rgba(255, 255, 255, 0.1) 50%,
    transparent 60%
  );
  animation: shine 3s ease-in-out infinite;
  pointer-events: none;
}
@keyframes shine {
  0%, 100% { transform: translateX(-100%) translateY(-100%); }
  50% { transform: translateX(100%) translateY(100%); }
}

/* Full-screen image preview */
.card-preview-popup {
  --van-popup-background: transparent;
}
.card-preview-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.card-preview-title {
  color: #fff;
  font-size: 1.1rem;
  font-weight: bold;
  text-shadow: 0 2px 8px rgba(0,0,0,0.8);
  text-align: center;
  padding: 0 16px;
}
.card-preview-large {
  max-width: 80vw;
  max-height: 65vh;
  object-fit: contain;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.6);
}
</style>
