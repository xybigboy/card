<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showConfirmDialog } from 'vant'
import { adminApi } from '../utils/api'
import CardIcon from '../components/CardIcon.vue'

const router = useRouter()
const templates = ref([])
const searchKeyword = ref('')
const activeTab = ref('')
const showFormPopup = ref(false)
const isEdit = ref(false)
const saving = ref(false)
const editingId = ref(null)
// 皮肤管理
const showSkinPopup = ref(false)
const skinTemplateId = ref(null)
const skinCardName = ref('')
const templateSkins = ref([])
const skinFileInput = ref(null)

const adminUsername = computed(() => localStorage.getItem('admin_username') || '管理员')

const rarityTabs = [
  { title: '全部', name: '' },
  { title: '普通', name: '普通' },
  { title: '高级', name: '高级' },
  { title: '史诗', name: '史诗' },
  { title: '典藏', name: '典藏' },
]

const filteredTemplates = computed(() => {
  let result = [...templates.value]

  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(c =>
      c.name.toLowerCase().includes(keyword) ||
      (c.category || '').toLowerCase().includes(keyword)
    )
  }

  if (activeTab.value) {
    result = result.filter(c => c.rarity === activeTab.value)
  }

  return result
})

const rarityTagType = (rarity) => {
  switch (rarity) {
    case '典藏': return 'warning'
    case '史诗': return 'primary'
    case '高级': return 'success'
    default: return 'default'
  }
}

const defaultFormData = () => ({
  name: '',
  image: 'card-default',
  rarity: '普通',
  base_stars: 1,
  category: '其他',
  speed: 100,
  base_attack: 50,
  base_defense: 30,
  base_hp: 200,
  skill_name: '',
  skill_type: '',
  skill_desc: '',
  skill_value: null,
  skill_trigger: '',
  skill_param: null,
  skills_json: '',
})

const formData = ref(defaultFormData())

// 多重技能列表
const skillsList = ref([])

const skillTypes = [
  { text: '无', value: '' },
  { text: '攻击增益', value: 'attack_buff' },
  { text: '治疗', value: 'heal' },
  { text: '叠加攻击', value: 'stack_attack' },
  { text: '暴击', value: 'critical' },
  { text: '闪避', value: 'dodge' },
  { text: '吸血', value: 'lifesteal' },
  { text: '伤害减免', value: 'damage_reduction' },
  { text: '流血', value: 'bleed' },
  { text: '麻痹', value: 'stun' },
  { text: '复活', value: 'revive' },
  { text: '斩杀', value: 'execute' },
  { text: '穿甲', value: 'armor_pierce' },
  { text: '额外伤害', value: 'bonus_damage' },
  { text: '必暴击', value: 'critical_strike' },
  { text: '连击', value: 'combo' },
]

const skillTriggers = [
  { text: '被动', value: 'passive' },
  { text: '每回合', value: 'every_round' },
  { text: '每N回合', value: 'every_n_rounds' },
  { text: '第N回合', value: 'round_n' },
  { text: '血量低于%', value: 'hp_below_pct' },
  { text: '死亡时', value: 'on_death' },
]

const addSkill = () => {
  skillsList.value.push({ type: '', value: null, trigger: 'passive', param: null, name: '', desc: '' })
}

const removeSkill = (index) => {
  skillsList.value.splice(index, 1)
}

// ===== 皮肤管理 =====
const openSkinPopup = async (card) => {
  skinTemplateId.value = card.id
  skinCardName.value = card.name
  showSkinPopup.value = true
  await loadTemplateSkins()
}

const loadTemplateSkins = async () => {
  if (!skinTemplateId.value) return
  try {
    const res = await adminApi.getTemplateSkins(skinTemplateId.value)
    templateSkins.value = res.data.skins || []
  } catch (e) {
    showToast('加载皮肤失败')
  }
}

const triggerSkinUpload = () => {
  skinFileInput.value?.click()
}

const handleSkinUpload = async (event) => {
  const file = event.target.files?.[0]
  if (!file) return
  try {
    await adminApi.uploadTemplateSkin(skinTemplateId.value, file)
    await loadTemplateSkins()
    showToast('皮肤上传成功')
  } catch (e) {
    showToast(e.response?.data?.detail || '上传失败')
  } finally {
    event.target.value = ''
  }
}

const handleDeleteSkin = async (skin) => {
  if (!skin.id) {
    showToast('默认图片无法删除')
    return
  }
  try {
    await showConfirmDialog({ title: '确认删除', message: '确定要删除此皮肤吗？' })
    await adminApi.deleteSkin(skin.id)
    await loadTemplateSkins()
    showToast('皮肤已删除')
  } catch (e) {
    if (e !== 'cancel' && e?.message !== 'cancel') {
      showToast(e.response?.data?.detail || '删除失败')
    }
  }
}

const loadTemplates = async () => {
  try {
    const res = await adminApi.getCardTemplates()
    if (res.data.success) {
      templates.value = res.data.templates
    }
  } catch (e) {
    if (e.response?.status === 401) {
      localStorage.removeItem('admin_token')
      router.push('/admin/login')
    }
  }
}

const openAddModal = () => {
  isEdit.value = false
  editingId.value = null
  formData.value = defaultFormData()
  skillsList.value = []
  showFormPopup.value = true
}

const openEditModal = (card) => {
  isEdit.value = true
  editingId.value = card.id
  formData.value = {
    name: card.name,
    image: card.image,
    rarity: card.rarity,
    base_stars: card.base_stars,
    category: card.category,
    speed: card.speed,
    base_attack: card.base_attack,
    base_defense: card.base_defense,
    base_hp: card.base_hp,
    skill_name: card.skill_name || '',
    skill_type: card.skill_type || '',
    skill_desc: card.skill_desc || '',
    skill_value: card.skill_value,
    skill_trigger: card.skill_trigger || '',
    skill_param: card.skill_param,
    skills_json: card.skills_json || '',
  }
  // 解析多重技能列表：跳过第一个元素（主技能已加载到formData）
  skillsList.value = []
  if (card.skills_json) {
    try {
      const parsed = JSON.parse(card.skills_json)
      if (Array.isArray(parsed) && parsed.length > 1) {
        // slice(1) 跳过主技能（index 0），只加载额外技能
        skillsList.value = parsed.slice(1).map(s => ({
          type: s.type || '',
          value: s.value || null,
          trigger: s.trigger || 'passive',
          param: s.param || null,
          name: s.name || '',
          desc: s.desc || ''
        }))
      }
    } catch (e) {
      console.error('Failed to parse skills_json:', e)
    }
  }
  showFormPopup.value = true
}

const closeForm = () => {
  showFormPopup.value = false
}

const validateForm = () => {
  if (!formData.value.name.trim()) {
    showToast({ message: '请输入卡片名称', type: 'fail' })
    return false
  }
  if (!formData.value.image.trim()) {
    showToast({ message: '请输入卡片图标标识', type: 'fail' })
    return false
  }
  if (!formData.value.rarity) {
    showToast({ message: '请选择稀有度', type: 'fail' })
    return false
  }
  if (!formData.value.base_stars || formData.value.base_stars < 1) {
    showToast({ message: '请输入有效的星级', type: 'fail' })
    return false
  }
  if (!formData.value.base_attack || formData.value.base_attack <= 0) {
    showToast({ message: '请输入有效的攻击力', type: 'fail' })
    return false
  }
  if (!formData.value.base_defense || formData.value.base_defense <= 0) {
    showToast({ message: '请输入有效的防御力', type: 'fail' })
    return false
  }
  if (!formData.value.base_hp || formData.value.base_hp <= 0) {
    showToast({ message: '请输入有效的生命值', type: 'fail' })
    return false
  }
  if (!formData.value.speed || formData.value.speed <= 0) {
    showToast({ message: '请输入有效的速度', type: 'fail' })
    return false
  }
  return true
}

const handleSubmit = async () => {
  if (!validateForm()) return

  saving.value = true

  try {
    // 序列化多重技能：主技能 + 额外技能列表 → skills_json
    const allSkills = []
    // 主技能（来自表单字段）
    if (formData.value.skill_type) {
      allSkills.push({
        type: formData.value.skill_type,
        value: formData.value.skill_value || 0,
        trigger: formData.value.skill_trigger || 'passive',
        param: formData.value.skill_param || 0,
        name: formData.value.skill_name || '',
        desc: formData.value.skill_desc || '',
      })
    }
    // 额外技能
    skillsList.value.forEach(s => {
      if (s.type) {
        allSkills.push({
          type: s.type,
          value: s.value || 0,
          trigger: s.trigger || 'passive',
          param: s.param || 0,
          name: s.name || '',
          desc: s.desc || '',
        })
      }
    })
    // 如果有多重技能，序列化为JSON
    if (allSkills.length > 1) {
      formData.value.skills_json = JSON.stringify(allSkills)
    } else {
      formData.value.skills_json = ''
    }

    if (isEdit.value) {
      await adminApi.updateTemplate(editingId.value, formData.value)
      showToast({ message: '保存成功', type: 'success' })
    } else {
      await adminApi.createTemplate(formData.value)
      showToast({ message: '创建成功', type: 'success' })
    }

    await loadTemplates()
    closeForm()
  } catch (e) {
    showToast({
      message: e.response?.data?.detail || '保存失败',
      type: 'fail',
    })
  } finally {
    saving.value = false
  }
}

const handleDelete = async (card) => {
  try {
    await showConfirmDialog({
      title: '确认删除',
      message: `确定要删除卡片「${card.name}」吗？\n注意：有用户使用的卡片无法删除`,
    })

    await adminApi.deleteTemplate(card.id)
    showToast({ message: '删除成功', type: 'success' })
    await loadTemplates()
  } catch (e) {
    if (e !== 'cancel' && e?.message !== 'cancel') {
      showToast({
        message: e.response?.data?.detail || '删除失败',
        type: 'fail',
      })
    }
  }
}

const handleLogout = async () => {
  try {
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_username')
    router.push('/admin/login')
  } catch (e) {
    // ignore
  }
}

// AI Card Generation
const showAiPopup = ref(false)
const aiGenerating = ref(false)
const aiSaving = ref(false)
const aiGenerated = ref([])
const aiProviders = ref([])
const aiForm = ref({
  provider_id: null,
  count: 5,
  category: '',
  theme: ''
})

const loadAiProviders = async () => {
  try {
    const res = await adminApi.getAiProviders('text')
    if (res.data.success) {
      aiProviders.value = res.data.providers.filter(p => p.is_active)
      if (aiProviders.value.length > 0 && !aiForm.value.provider_id) {
        aiForm.value.provider_id = aiProviders.value[0].id
      }
    }
  } catch (e) {
    console.error('Failed to load AI providers:', e)
  }
}

const openAiModal = () => {
  aiGenerated.value = []
  aiForm.value = { provider_id: null, count: 5, category: '', theme: '' }
  showAiPopup.value = true
  loadAiProviders()
}

const handleAiGenerate = async () => {
  aiGenerating.value = true
  try {
    const res = await adminApi.aiGenerate(aiForm.value)
    if (res.data.success) {
      aiGenerated.value = res.data.generated
      showToast({ message: `生成了 ${res.data.count} 张卡片`, type: 'success' })
    }
  } catch (e) {
    showToast({ message: e.response?.data?.detail || 'AI生成失败', type: 'fail' })
  } finally {
    aiGenerating.value = false
  }
}

const removeAiCard = (index) => {
  aiGenerated.value.splice(index, 1)
}

const handleAiSave = async () => {
  if (aiGenerated.value.length === 0) return
  aiSaving.value = true
  try {
    const res = await adminApi.batchSave(aiGenerated.value)
    showToast({ message: res.data.message, type: 'success' })
    showAiPopup.value = false
    await loadTemplates()
  } catch (e) {
    showToast({ message: e.response?.data?.detail || '保存失败', type: 'fail' })
  } finally {
    aiSaving.value = false
  }
}

// Helper: detect if image field is a real URL
const isImageUrl = (image) => {
  return !!(image && (image.startsWith('http://') || image.startsWith('https://') || image.startsWith('/images/')))
}

// Card image generation
const showImageGenPopup = ref(false)
const imageProviders = ref([])
const imageGenProviderId = ref(null)
const imageGenLoading = ref(false)
const imageGenTarget = ref(null) // { type: 'single', templateId, cardName } or { type: 'batch', count }
const imageGenStyle = ref('default') // default / realistic / anime / custom
const imageGenCustomStyle = ref('')
const imageGenIncludeText = ref(false)

const imageGenStyles = [
  { text: '默认风格', value: 'default' },
  { text: '真人写实', value: 'realistic' },
  { text: '日漫风格', value: 'anime' },
  { text: '自定义', value: 'custom' },
]

const loadImageProviders = async () => {
  try {
    const res = await adminApi.getAiProviders('image')
    if (res.data.success) {
      imageProviders.value = (res.data.providers || []).filter(p => p.is_active)
      if (imageProviders.value.length > 0 && !imageGenProviderId.value) {
        imageGenProviderId.value = imageProviders.value[0].id
      }
    }
  } catch (e) {
    console.error('Failed to load image providers:', e)
  }
}

const openImageGenPopup = (card) => {
  imageGenTarget.value = { type: 'single', templateId: card.id, cardName: card.name }
  imageGenProviderId.value = null
  showImageGenPopup.value = true
  loadImageProviders()
}

const openBatchImageGenPopup = () => {
  const needGen = templates.value.filter(t => !isImageUrl(t.image))
  if (needGen.length === 0) {
    showToast({ message: '所有卡片都已有图片', type: 'fail' })
    return
  }
  imageGenTarget.value = { type: 'batch', count: needGen.length }
  imageGenProviderId.value = null
  showImageGenPopup.value = true
  loadImageProviders()
}

const handleImageGen = async () => {
  if (!imageGenProviderId.value) {
    showToast({ message: '请选择图片提供商', type: 'fail' })
    return
  }
  imageGenLoading.value = true
  try {
    let templateIds
    if (imageGenTarget.value.type === 'single') {
      templateIds = [imageGenTarget.value.templateId]
    } else {
      // Pass actual IDs of templates that need images (not URL images)
      templateIds = templates.value
        .filter(t => !isImageUrl(t.image))
        .map(t => t.id)
    }
    const res = await adminApi.generateCardImages(imageGenProviderId.value, templateIds, {
      style: imageGenStyle.value,
      custom_style: imageGenStyle.value === 'custom' ? imageGenCustomStyle.value : '',
      include_text: imageGenIncludeText.value
    })
    showToast({ message: res.data.message || '图片生成成功', type: 'success' })
    showImageGenPopup.value = false
    await loadTemplates()
  } catch (e) {
    showToast({ message: e.response?.data?.detail || '图片生成失败', type: 'fail' })
  } finally {
    imageGenLoading.value = false
  }
}

// Image preview (large image popup)
const showImagePreview = ref(false)
const previewImageUrl = ref('')
const previewCardName = ref('')

const openImagePreview = (card) => {
  previewImageUrl.value = card.image
  previewCardName.value = card.name
  showImagePreview.value = true
}

onMounted(() => {
  const token = localStorage.getItem('admin_token')
  if (!token) {
    router.push('/admin/login')
    return
  }
  loadTemplates()
})
</script>

<template>
  <div class="admin-page">
    <!-- Nav bar -->
    <van-nav-bar
      title="卡牌管理"
      left-arrow
      @click-left="router.push('/')"
      class="admin-nav-bar"
    >
      <template #right>
        <van-icon name="setting-o" size="18" @click="router.push('/admin/settings')" />
      </template>
    </van-nav-bar>

    <!-- Search bar -->
    <van-search
      v-model="searchKeyword"
      placeholder="搜索卡片名称..."
      shape="round"
      class="admin-search"
    />

    <!-- Rarity tabs -->
    <van-tabs
      v-model:active="activeTab"
      type="card"
      class="rarity-tabs"
      shrink
    >
      <van-tab
        v-for="tab in rarityTabs"
        :key="tab.name"
        :title="tab.title"
        :name="tab.name"
      />
    </van-tabs>

    <!-- Template count -->
    <div class="template-count">
      共 {{ filteredTemplates.length }} 张卡片
    </div>

    <!-- Action bar -->
    <div class="action-bar">
      <van-button
        size="small"
        type="primary"
        plain
        class="action-bar-btn"
        @click="openBatchImageGenPopup"
      >
        <van-icon name="photo-o" />
        <span>批量生成图片</span>
      </van-button>
    </div>

    <!-- Template list -->
    <div class="template-list">
      <van-cell-group v-if="filteredTemplates.length > 0" inset class="template-cells">
        <van-swipe-cell
          v-for="card in filteredTemplates"
          :key="card.id"
        >
          <van-cell
            :title="card.name"
            clickable
            @click="openEditModal(card)"
            class="template-cell"
          >
            <template #icon>
              <div
                class="cell-icon-wrap"
                :class="{ 'icon-clickable': isImageUrl(card.image) }"
                @click.stop="isImageUrl(card.image) ? openImagePreview(card) : null"
              >
                <img
                  v-if="isImageUrl(card.image)"
                  :src="card.image"
                  class="cell-card-img"
                  alt="card"
                />
                <CardIcon
                  v-else
                  :image-id="card.image"
                  :category="card.category"
                  :name="card.name"
                  size="small"
                />
              </div>
            </template>
            <template #default>
              <div class="cell-actions">
                <button
                  v-if="!isImageUrl(card.image)"
                  class="gen-image-btn"
                  @click.stop="openImageGenPopup(card)"
                >
                  生成图片
                </button>
                <button
                  class="gen-image-btn skin-btn"
                  @click.stop="openSkinPopup(card)"
                >
                  皮肤
                </button>
              </div>
            </template>
            <template #label>
              <div class="cell-label">
                <van-tag :type="rarityTagType(card.rarity)" size="medium">
                  {{ card.rarity }}
                </van-tag>
                <span class="stat-summary">
                  ATK {{ card.base_attack }} / DEF {{ card.base_defense }} / HP {{ card.base_hp }} / SPD {{ card.speed }}
                </span>
              </div>
            </template>
          </van-cell>
          <template #right>
            <van-button
              square
              type="danger"
              text="删除"
              class="swipe-delete-btn"
              @click="handleDelete(card)"
            />
          </template>
        </van-swipe-cell>
      </van-cell-group>

      <van-empty v-else description="暂无卡片数据" />
    </div>

    <!-- FAB: Add new template + AI Generate -->
    <div class="fab-wrap">
      <van-button
        round
        type="warning"
        size="normal"
        class="fab-btn ai-fab"
        @click="openAiModal"
      >
        <van-icon name="fire-o" />
        <span class="fab-text">AI生成</span>
      </van-button>
      <van-button
        round
        type="primary"
        size="large"
        class="fab-btn"
        @click="openAddModal"
      >
        <van-icon name="plus" />
        <span class="fab-text">新增</span>
      </van-button>
    </div>

    <!-- Edit/Add form popup -->
    <van-popup
      v-model:show="showFormPopup"
      position="bottom"
      round
      :style="{ maxHeight: '85vh' }"
      class="form-popup"
    >
      <div class="form-popup-inner">
        <div class="form-popup-header">
          <h3 class="form-popup-title">{{ isEdit ? '编辑卡片' : '新增卡片' }}</h3>
          <van-icon name="cross" @click="closeForm" class="form-close-icon" />
        </div>

        <div class="form-popup-body">
          <van-cell-group inset class="form-cell-group">
            <van-field
              v-model="formData.name"
              label="名称"
              placeholder="请输入卡片名称"
              required
            />
            <van-field
              v-model="formData.image"
              label="图标标识"
              placeholder="如 db-goku, nz-naruto"
              required
            />
            <van-field name="rarity" label="稀有度" required>
              <template #input>
                <van-radio-group v-model="formData.rarity" direction="horizontal">
                  <van-radio name="普通">普通</van-radio>
                  <van-radio name="高级">高级</van-radio>
                  <van-radio name="史诗">史诗</van-radio>
                  <van-radio name="典藏">典藏</van-radio>
                </van-radio-group>
              </template>
            </van-field>
            <van-field
              v-model.number="formData.base_stars"
              type="number"
              label="星级"
              placeholder="1-10"
              required
            />
            <van-field
              v-model="formData.category"
              label="分类"
              placeholder="如: 龙珠、火影"
            />
            <van-field
              v-model.number="formData.base_attack"
              type="number"
              label="基础攻击"
              required
            />
            <van-field
              v-model.number="formData.base_defense"
              type="number"
              label="基础防御"
              required
            />
            <van-field
              v-model.number="formData.base_hp"
              type="number"
              label="基础生命"
              required
            />
            <van-field
              v-model.number="formData.speed"
              type="number"
              label="速度"
              required
            />
            <van-field
              v-model="formData.skill_name"
              label="技能名称"
              placeholder="如: 龟派气功"
            />
            <van-field name="skill_type" label="技能类型">
              <template #input>
                <select v-model="formData.skill_type" class="native-select">
                  <option v-for="st in skillTypes" :key="st.value" :value="st.value">
                    {{ st.text }}
                  </option>
                </select>
              </template>
            </van-field>
            <van-field
              v-model="formData.skill_desc"
              label="技能描述"
              type="textarea"
              rows="2"
              placeholder="描述技能效果"
              autosize
            />
            <van-field
              v-model.number="formData.skill_value"
              type="number"
              label="技能数值"
              placeholder="如: 30 表示30%"
            />
            <van-field name="skill_trigger" label="触发条件">
              <template #input>
                <select v-model="formData.skill_trigger" class="native-select">
                  <option value="">默认(被动)</option>
                  <option v-for="t in skillTriggers" :key="t.value" :value="t.value">
                    {{ t.text }}
                  </option>
                </select>
              </template>
            </van-field>
            <van-field
              v-model.number="formData.skill_param"
              type="number"
              label="触发参数"
              placeholder="N值(每N回合/第N回合/百分比)"
            />
          </van-cell-group>

          <!-- 多重技能编辑 -->
          <div class="multi-skill-section">
            <div class="multi-skill-header">
              <span class="multi-skill-title">额外技能</span>
              <van-button size="small" type="primary" @click="addSkill" plain>
                <van-icon name="plus" /> 添加技能
              </van-button>
            </div>
            <div v-if="skillsList.length === 0" class="multi-skill-empty">
              暂无额外技能，点击"添加技能"可为一个卡片配置多重技能效果
            </div>
            <div v-for="(sk, idx) in skillsList" :key="idx" class="multi-skill-item">
              <div class="multi-skill-item-header">
                <span>技能 {{ idx + 2 }}</span>
                <van-icon name="cross" @click="removeSkill(idx)" class="multi-skill-remove" />
              </div>
              <van-cell-group inset>
                <van-field v-model="sk.name" label="名称" placeholder="技能名称" />
                <van-field name="type" label="类型">
                  <template #input>
                    <select v-model="sk.type" class="native-select">
                      <option value="">请选择</option>
                      <option v-for="st in skillTypes.filter(t => t.value)" :key="st.value" :value="st.value">
                        {{ st.text }}
                      </option>
                    </select>
                  </template>
                </van-field>
                <van-field v-model.number="sk.value" type="number" label="数值" placeholder="如: 30" />
                <van-field name="trigger" label="触发">
                  <template #input>
                    <select v-model="sk.trigger" class="native-select">
                      <option v-for="t in skillTriggers" :key="t.value" :value="t.value">
                        {{ t.text }}
                      </option>
                    </select>
                  </template>
                </van-field>
                <van-field v-model.number="sk.param" type="number" label="参数" placeholder="N值/百分比" />
                <van-field
                  v-model="sk.desc"
                  type="textarea"
                  label="描述"
                  placeholder="技能效果描述"
                  rows="2"
                  autosize
                />
              </van-cell-group>
            </div>
          </div>
        </div>

        <div class="form-popup-footer">
          <button class="admin-cancel-btn" @click="closeForm">取消</button>
          <van-button
            type="primary"
            :loading="saving"
            loading-text="保存中..."
            @click="handleSubmit"
          >
            保存
          </van-button>
        </div>
      </div>
    </van-popup>

    <!-- AI Generate popup -->
    <van-popup
      v-model:show="showAiPopup"
      position="bottom"
      round
      :style="{ maxHeight: '90vh' }"
      class="form-popup ai-popup"
    >
      <div class="form-popup-inner">
        <div class="form-popup-header">
          <h3 class="form-popup-title">AI 批量生成卡片</h3>
          <van-icon name="cross" @click="showAiPopup = false" class="form-close-icon" />
        </div>

        <div class="form-popup-body">
          <!-- Config form -->
          <van-cell-group inset class="form-cell-group">
            <van-field name="provider" label="AI 提供商">
              <template #input>
                <select v-model="aiForm.provider_id" class="native-select">
                  <option v-for="p in aiProviders" :key="p.id" :value="p.id">
                    {{ p.name }} ({{ p.model }})
                  </option>
                </select>
              </template>
            </van-field>
            <van-field
              v-model.number="aiForm.count"
              type="number"
              label="生成数量"
              placeholder="1-20"
            />
            <van-field
              v-model="aiForm.category"
              label="动漫系列"
              placeholder="如: 龙珠、火影（留空随机）"
            />
            <van-field
              v-model="aiForm.theme"
              label="主题"
              placeholder="如: 火焰系、防御型（留空随机）"
            />
          </van-cell-group>

          <!-- Generate button -->
          <div class="ai-action-row">
            <van-button
              type="warning"
              :loading="aiGenerating"
              loading-text="AI 生成中..."
              @click="handleAiGenerate"
              block
            >
              <van-icon name="fire-o" />
              开始生成
            </van-button>
          </div>

          <!-- Generated cards preview -->
          <div v-if="aiGenerated.length > 0" class="ai-preview-section">
            <div class="ai-preview-header">
              <span class="ai-preview-title">已生成 {{ aiGenerated.length }} 张卡片</span>
              <span class="ai-preview-hint">可删除不满意的，剩余的一键保存</span>
            </div>
            <div class="ai-card-grid">
              <div
                v-for="(card, idx) in aiGenerated"
                :key="idx"
                class="ai-card-item"
              >
                <div class="ai-card-remove" @click="removeAiCard(idx)">
                  <van-icon name="cross" />
                </div>
                <van-tag :type="rarityTagType(card.rarity)" size="medium" class="ai-rarity-tag">
                  {{ card.rarity }}
                </van-tag>
                <div class="ai-card-name">{{ card.name }}</div>
                <div class="ai-card-stats">
                  <span>ATK {{ card.base_attack }}</span>
                  <span>DEF {{ card.base_defense }}</span>
                  <span>HP {{ card.base_hp }}</span>
                  <span>SPD {{ card.speed }}</span>
                </div>
                <div class="ai-card-skill" v-if="card.skill_name">
                  {{ card.skill_name }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Save footer -->
        <div v-if="aiGenerated.length > 0" class="form-popup-footer">
          <span class="ai-save-hint">将保存 {{ aiGenerated.length }} 张卡片</span>
          <van-button
            type="primary"
            :loading="aiSaving"
            loading-text="保存中..."
            @click="handleAiSave"
          >
            全部保存
          </van-button>
        </div>
      </div>
    </van-popup>

    <!-- Image generation popup -->
    <van-popup
      v-model:show="showImageGenPopup"
      position="bottom"
      round
      :style="{ maxHeight: '70vh' }"
      class="form-popup"
    >
      <div class="form-popup-inner">
        <div class="form-popup-header">
          <h3 class="form-popup-title">
            {{ imageGenTarget?.type === 'batch' ? '批量生成图片' : '生成卡片图片' }}
          </h3>
          <van-icon name="cross" @click="showImageGenPopup = false" class="form-close-icon" />
        </div>

        <div class="form-popup-body">
          <div v-if="imageGenTarget?.type === 'single'" class="gen-target-info">
            <van-icon name="info-o" />
            <span>目标卡片: {{ imageGenTarget.cardName }}</span>
          </div>
          <div v-else-if="imageGenTarget?.type === 'batch'" class="gen-target-info">
            <van-icon name="info-o" />
            <span>将为 {{ imageGenTarget.count }} 张没有图片的卡片生成图片</span>
          </div>

          <van-cell-group inset class="form-cell-group">
            <van-field name="provider" label="图片提供商">
              <template #input>
                <select v-model="imageGenProviderId" class="native-select">
                  <option :value="null">请选择</option>
                  <option v-for="p in imageProviders" :key="p.id" :value="p.id">
                    {{ p.name }} ({{ p.model }})
                  </option>
                </select>
              </template>
            </van-field>

            <van-field name="style" label="图片风格">
              <template #input>
                <select v-model="imageGenStyle" class="native-select">
                  <option v-for="s in imageGenStyles" :key="s.value" :value="s.value">
                    {{ s.text }}
                  </option>
                </select>
              </template>
            </van-field>

            <van-field
              v-if="imageGenStyle === 'custom'"
              name="custom_style"
              label="自定义风格"
              type="textarea"
              v-model="imageGenCustomStyle"
              placeholder="描述你想要的图片风格，如：水彩画风格, 暗黑系, Q版人物..."
              rows="2"
            />

            <van-field name="include_text" label="图片带文字">
              <template #input>
                <van-switch v-model="imageGenIncludeText" />
              </template>
            </van-field>
          </van-cell-group>

          <div v-if="imageProviders.length === 0 && !imageGenLoading" class="no-provider-hint">
            暂无可用的图片提供商，请先在设置页添加图片模型提供商
          </div>

          <div class="ai-action-row">
            <van-button
              type="primary"
              :loading="imageGenLoading"
              loading-text="生成中..."
              :disabled="imageProviders.length === 0"
              @click="handleImageGen"
              block
            >
              <van-icon name="photo-o" />
              开始生成
            </van-button>
          </div>
        </div>
      </div>
    </van-popup>

    <!-- Image preview popup -->
    <van-popup
      v-model:show="showImagePreview"
      round
      closeable
      close-icon="cross"
      :style="{ maxWidth: '90vw', maxHeight: '85vh' }"
      class="image-preview-popup"
    >
      <div class="image-preview-inner">
        <div class="image-preview-header">
          <span class="image-preview-title">{{ previewCardName }}</span>
        </div>
        <img
          :src="previewImageUrl"
          :alt="previewCardName"
          class="image-preview-large"
        />
      </div>
    </van-popup>

    <!-- Skin management popup -->
    <van-popup
      v-model:show="showSkinPopup"
      position="bottom"
      round
      :style="{ maxHeight: '80vh' }"
      class="form-popup"
    >
      <div class="form-popup-inner">
        <div class="form-popup-header">
          <h3 class="form-popup-title">皮肤管理 - {{ skinCardName }}</h3>
          <van-icon name="cross" @click="showSkinPopup = false" class="form-close-icon" />
        </div>
        <div class="form-popup-body">
          <div class="skin-upload-bar">
            <van-button size="small" type="primary" plain @click="triggerSkinUpload">
              <van-icon name="upload" /> 上传皮肤
            </van-button>
            <input ref="skinFileInput" type="file" accept="image/*" style="display:none" @change="handleSkinUpload" />
          </div>
          <div class="admin-skin-list">
            <div v-for="skin in templateSkins" :key="skin.image_path" class="admin-skin-item">
              <img :src="skin.image_path" class="admin-skin-thumb" />
              <div class="admin-skin-info">
                <span class="admin-skin-label">
                  {{ skin.source === 'default' ? '默认图片' : skin.source === 'admin' ? '官方皮肤' : '玩家上传' }}
                </span>
                <van-button
                  v-if="skin.id"
                  size="mini"
                  type="danger"
                  plain
                  @click="handleDeleteSkin(skin)"
                >删除</van-button>
              </div>
            </div>
            <div v-if="templateSkins.length === 0" class="admin-skin-empty">
              暂无皮肤图片
            </div>
          </div>
        </div>
      </div>
    </van-popup>
  </div>
</template>

<style scoped>
.admin-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  padding-bottom: 80px;
}

/* Nav bar */
.admin-nav-bar {
  background: rgba(255, 255, 255, 0.05) !important;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.admin-nav-bar :deep(.van-nav-bar__title) {
  color: #fff;
}

.admin-nav-bar :deep(.van-icon) {
  color: rgba(255, 255, 255, 0.8) !important;
}

/* Search */
.admin-search {
  background: transparent !important;
  padding: 8px 12px;
}

.admin-search :deep(.van-search__content) {
  background: rgba(255, 255, 255, 0.06);
}

.admin-search :deep(.van-field__control) {
  color: #fff;
}

.admin-search :deep(.van-field__control::placeholder) {
  color: rgba(255, 255, 255, 0.35);
}

.admin-search :deep(.van-icon) {
  color: rgba(255, 255, 255, 0.5);
}

/* Rarity tabs */
.rarity-tabs {
  padding: 0 12px;
  margin-bottom: 8px;
}

.rarity-tabs :deep(.van-tabs__nav) {
  background: transparent;
}

.rarity-tabs :deep(.van-tab) {
  color: rgba(255, 255, 255, 0.6);
  border-color: rgba(255, 255, 255, 0.1);
}

.rarity-tabs :deep(.van-tab--active) {
  color: #fff;
  background: rgba(102, 126, 234, 0.3);
  border-color: #667eea;
}

/* Count */
.template-count {
  padding: 4px 20px 8px;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.4);
}

/* Template list */
.template-list {
  padding: 0 4px;
}

.template-cells {
  background: transparent !important;
}

.template-cells :deep(.van-cell) {
  background: rgba(255, 255, 255, 0.04);
  color: #fff;
}

.template-cells :deep(.van-cell::after) {
  border-color: rgba(255, 255, 255, 0.05);
}

.template-cells :deep(.van-cell__title) {
  color: #fff;
}

.template-cells :deep(.van-cell__label) {
  color: rgba(255, 255, 255, 0.5);
}

.template-cell {
  padding-left: 12px;
}

.cell-icon-wrap {
  margin-right: 12px;
  margin-top: 4px;
}

.cell-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
  flex-wrap: wrap;
}

.stat-summary {
  font-size: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
}

.swipe-delete-btn {
  height: 100%;
}

/* Empty state */
:deep(.van-empty) {
  padding: 40px 0;
}

:deep(.van-empty__description) {
  color: rgba(255, 255, 255, 0.4);
}

/* FAB */
.fab-wrap {
  position: fixed;
  bottom: 24px;
  right: 20px;
  z-index: 100;
}

.fab-btn {
  padding: 0 20px;
  height: 48px;
  box-shadow: 0 4px 16px rgba(102, 126, 234, 0.4);
}

.fab-text {
  margin-left: 4px;
}

/* Form popup */
.form-popup {
  background: rgba(20, 20, 40, 0.95) !important;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}

.form-popup-inner {
  display: flex;
  flex-direction: column;
  max-height: 85vh;
}

.form-popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 20px 12px;
}

.form-popup-title {
  font-size: 1.1rem;
  color: #fff;
  font-weight: 600;
}

.form-close-icon {
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  font-size: 20px;
}

.form-popup-body {
  flex: 1;
  overflow-y: auto;
  padding: 0 4px;
}

.form-cell-group {
  background: transparent !important;
}

.form-cell-group :deep(.van-cell) {
  background: rgba(255, 255, 255, 0.04);
  color: #fff;
}

.form-cell-group :deep(.van-cell::after) {
  border-color: rgba(255, 255, 255, 0.05);
}

.form-cell-group :deep(.van-field__label) {
  color: rgba(255, 255, 255, 0.7);
}

.form-cell-group :deep(.van-field__control) {
  color: #fff;
}

.form-cell-group :deep(.van-field__control::placeholder) {
  color: rgba(255, 255, 255, 0.3);
}

.form-cell-group :deep(.van-radio__label) {
  color: rgba(255, 255, 255, 0.8);
}

.native-select {
  background: transparent;
  color: #fff;
  border: none;
  outline: none;
  font-size: 0.875rem;
  width: 100%;
}

.native-select option {
  background: #1a1a2e;
  color: #fff;
}

.form-popup-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

/* Multi-skill editor */
.multi-skill-section {
  padding: 12px 16px;
}
.multi-skill-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.multi-skill-title {
  font-size: 0.9rem;
  font-weight: bold;
  color: rgba(255, 255, 255, 0.8);
}
.multi-skill-empty {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.4);
  padding: 12px 0;
  text-align: center;
}
.multi-skill-item {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  padding: 8px;
  margin-bottom: 8px;
}
.multi-skill-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 4px 4px;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
}
.multi-skill-remove {
  cursor: pointer;
  color: #ef4444;
  font-size: 1.1rem;
}

/* Cell actions (生成图片 + 皮肤 buttons) */
.cell-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
.skin-btn {
  background: rgba(102, 126, 234, 0.15) !important;
  color: #667eea !important;
}

/* Admin skin management */
.skin-upload-bar {
  padding: 12px 16px;
}
.admin-skin-list {
  padding: 0 16px 16px;
}
.admin-skin-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  margin-bottom: 8px;
}
.admin-skin-thumb {
  width: 60px;
  height: 60px;
  object-fit: cover;
  border-radius: 6px;
}
.admin-skin-info {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.admin-skin-label {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.6);
}
.admin-skin-empty {
  text-align: center;
  padding: 24px;
  color: rgba(255, 255, 255, 0.3);
  font-size: 0.9rem;
}

/* AI FAB */
.ai-fab {
  margin-bottom: 12px;
  box-shadow: 0 4px 16px rgba(255, 165, 0, 0.3);
}

/* AI Generate popup */
.ai-action-row {
  padding: 16px 16px 8px;
}

.ai-preview-section {
  padding: 8px 16px 16px;
}

.ai-preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.ai-preview-title {
  color: #fff;
  font-size: 0.95rem;
  font-weight: 600;
}

.ai-preview-hint {
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.75rem;
}

.ai-card-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.ai-card-item {
  position: relative;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  padding: 12px 10px 10px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.ai-card-remove {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: rgba(255, 70, 70, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 12px;
  color: #fff;
}

.ai-rarity-tag {
  margin-bottom: 6px;
}

.ai-card-name {
  color: #fff;
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 6px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ai-card-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2px 8px;
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
}

.ai-card-skill {
  margin-top: 6px;
  font-size: 0.7rem;
  color: rgba(255, 200, 100, 0.7);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ai-save-hint {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.8rem;
}

/* Action bar */
.action-bar {
  padding: 0 16px 10px;
  display: flex;
  gap: 8px;
}

.action-bar-btn {
  flex-shrink: 0;
}

.action-bar-btn :deep(.van-button__text) {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* Generate image button in cell value */
.gen-image-btn {
  background: rgba(168, 85, 247, 0.25);
  color: #c4b5fd;
  border: 1px solid rgba(168, 85, 247, 0.35);
  border-radius: 6px;
  padding: 3px 10px;
  font-size: 0.72rem;
  cursor: pointer;
  white-space: nowrap;
}

/* Card image in cell */
.cell-card-img {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  object-fit: cover;
  display: block;
}

.cell-icon-wrap.icon-clickable {
  cursor: pointer;
}

.cell-icon-wrap.icon-clickable:active {
  opacity: 0.7;
}

/* Image generation popup */
.gen-target-info {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.82rem;
  background: rgba(102, 126, 234, 0.08);
  border-radius: 8px;
  margin: 0 16px 8px;
}

.no-provider-hint {
  text-align: center;
  color: rgba(255, 200, 100, 0.7);
  font-size: 0.8rem;
  padding: 12px 16px;
}

/* Image preview popup */
.image-preview-popup {
  background: rgba(20, 20, 40, 0.95) !important;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}

.image-preview-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
}

.image-preview-header {
  margin-bottom: 12px;
}

.image-preview-title {
  color: #fff;
  font-size: 1rem;
  font-weight: 600;
}

.image-preview-large {
  max-width: 80vw;
  max-height: 65vh;
  border-radius: 12px;
  object-fit: contain;
}
</style>
