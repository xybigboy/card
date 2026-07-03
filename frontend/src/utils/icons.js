// Card category icons
export const categoryIcons = {
  'dragon-ball': '~icons/tabler/planet',
  'naruto': '~icons/tabler/flame',
  'ultraman': '~icons/tabler/star',
  'one-piece': '~icons/tabler/anchor',
  'demon-slayer': '~icons/tabler/sword',
  'pokemon': '~icons/tabler/bolt',
  'detective': '~icons/tabler/search',
}

// Map card image IDs to categories
export const cardCategories = {
  'db-goku': 'dragon-ball',
  'db-vegeta': 'dragon-ball',
  'db-frieza': 'dragon-ball',
  'db-gohan': 'dragon-ball',
  'db-krillin': 'dragon-ball',
  'nz-naruto': 'naruto',
  'nz-sasuke': 'naruto',
  'nz-kakashi': 'naruto',
  'nz-gaara': 'naruto',
  'nz-sakura': 'naruto',
  'ul-tiga': 'ultraman',
  'ul-zero': 'ultraman',
  'ul-z': 'ultraman',
  'ul-original': 'ultraman',
  'op-luffy': 'one-piece',
  'op-zoro': 'one-piece',
  'ds-tanjiro': 'demon-slayer',
  'ds-nezuko': 'demon-slayer',
  'dt-conan': 'detective',
  'pm-pikachu': 'pokemon',
}

// Card character display names (first character for avatar)
export const cardNames = {
  'db-goku': { name: '卡卡罗特', initial: '悟' },
  'db-vegeta': { name: '贝吉塔', initial: '贝' },
  'db-frieza': { name: '弗利沙', initial: '弗' },
  'db-gohan': { name: '孙悟饭', initial: '饭' },
  'db-krillin': { name: '克林', initial: '克' },
  'nz-naruto': { name: '漩涡鸣人', initial: '鸣' },
  'nz-sasuke': { name: '宇智波佐助', initial: '佐' },
  'nz-kakashi': { name: '旗木卡卡西', initial: '卡' },
  'nz-gaara': { name: '我爱罗', initial: '罗' },
  'nz-sakura': { name: '春野樱', initial: '樱' },
  'ul-tiga': { name: '迪迦奥特曼', initial: '迪' },
  'ul-zero': { name: '赛罗奥特曼', initial: '赛' },
  'ul-z': { name: '泽塔奥特曼', initial: '泽' },
  'ul-original': { name: '初代奥特曼', initial: '初' },
  'op-luffy': { name: '路飞', initial: '路' },
  'op-zoro': { name: '索隆', initial: '索' },
  'ds-tanjiro': { name: '炭治郎', initial: '炭' },
  'ds-nezuko': { name: '祢豆子', initial: '豆' },
  'dt-conan': { name: '柯南', initial: '柯' },
  'pm-pikachu': { name: '皮卡丘', initial: '皮' },
}

// Map Chinese category names to slugs
export const categoryNameMap = {
  '龙珠': 'dragon-ball',
  '火影': 'naruto',
  '火影忍者': 'naruto',
  '奥特曼': 'ultraman',
  '海贼王': 'one-piece',
  '航海王': 'one-piece',
  '鬼灭': 'demon-slayer',
  '鬼灭之刃': 'demon-slayer',
  '宝可梦': 'pokemon',
  '精灵宝可梦': 'pokemon',
  '名侦探柯南': 'detective',
  '侦探': 'detective',
}

// Map image ID prefixes to category slugs (for AI-generated cards)
export const imagePrefixMap = {
  'db-': 'dragon-ball',
  'nz-': 'naruto',
  'ul-': 'ultraman',
  'op-': 'one-piece',
  'ds-': 'demon-slayer',
  'pm-': 'pokemon',
  'dt-': 'detective',
}

// Category color themes (gradient pairs)
export const categoryColors = {
  'dragon-ball': ['#FF6B35', '#FFD700'],
  'naruto': ['#FF4500', '#FF8C00'],
  'ultraman': ['#4169E1', '#00BFFF'],
  'one-piece': ['#DC143C', '#FF6347'],
  'demon-slayer': ['#2E8B57', '#20B2AA'],
  'pokemon': ['#FFD700', '#FFA500'],
  'detective': ['#4B0082', '#8A2BE2'],
}

// Battle event icons (for structured battle log rendering)
export const battleEventIcons = {
  'attack': '[x]',    // Text-safe battle icons
  'heal': '+',
  'buff': '↑',
  'debuff': '↓',
  'critical': '!!',
  'dodge': '~',
  'stun': '!',
  'bleed': '✕',
  'lifesteal': '<3',
  'revive': '↻',
  'execute': '×',
  'bonus_damage': '★',
  'combo': '»',
  'skill': '◆',
  'battle_start': '▶',
  'battle_end': '■',
  'round': '○',
}

// UI icon mapping (for Tabler icons used in components)
export const uiIcons = {
  gold: 'tabler:coin',
  ticket: 'tabler:ticket',
  star: 'tabler:star-filled',
  trophy: 'tabler:trophy',
  battle: 'tabler:swords',
  shop: 'tabler:shopping-cart',
  gacha: 'tabler:dice-5',
  warehouse: 'tabler:package',
  settings: 'tabler:settings',
  ranking: 'tabler:chart-bar',
  attack: 'tabler:sword',
  defense: 'tabler:shield',
  hp: 'tabler:heart',
  speed: 'tabler:wind',
  search: 'tabler:search',
  lock: 'tabler:lock',
  user: 'tabler:user',
}
