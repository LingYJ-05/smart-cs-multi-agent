<template>
  <div
    ref="containerRef"
    class="virtual-scroll-container"
    @scroll="handleScroll"
  >
    <div class="virtual-scroll-content" :style="{ height: totalHeight + 'px' }">
      <div
        v-for="item in visibleItems"
        :key="item[itemKey]"
        class="virtual-scroll-item"
        :style="{ transform: `translateY(${getOffset(item[itemKey])}px)` }"
      >
        <slot :item="item"></slot>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from "vue";

const props = withDefaults(
  defineProps<{
    items: any[];
    itemKey: string;
    estimatedItemSize?: number;
  }>(),
  {
    estimatedItemSize: 100,
  },
);

const emit = defineEmits<{
  (e: "scroll", scrollTop: number): void;
}>();

const containerRef = ref<HTMLElement | null>(null);
const itemHeights = ref<Map<string, number>>(new Map());
const scrollTop = ref(0);

const containerHeight = computed(() => {
  return containerRef.value?.clientHeight || 500;
});

const totalHeight = computed(() => {
  if (props.items.length === 0) return 0;
  let height = 0;
  props.items.forEach((item) => {
    const key = item[props.itemKey] as string;
    height += itemHeights.value.get(key) || props.estimatedItemSize;
  });
  return height;
});

const startIndex = computed(() => {
  let cumulativeHeight = 0;
  for (let i = 0; i < props.items.length; i++) {
    const key = props.items[i][props.itemKey] as string;
    cumulativeHeight += itemHeights.value.get(key) || props.estimatedItemSize;
    if (cumulativeHeight > scrollTop.value) {
      return Math.max(0, i - 1);
    }
  }
  return 0;
});

const endIndex = computed(() => {
  let cumulativeHeight = 0;
  const start = startIndex.value;
  for (let i = start; i < props.items.length; i++) {
    const key = props.items[i][props.itemKey] as string;
    cumulativeHeight += itemHeights.value.get(key) || props.estimatedItemSize;
    if (cumulativeHeight > containerHeight.value + 200) {
      return Math.min(props.items.length - 1, i + 1);
    }
  }
  return props.items.length - 1;
});

const visibleItems = computed(() => {
  return props.items.slice(startIndex.value, endIndex.value + 1);
});

const getOffset = (id: string) => {
  let offset = 0;
  for (let i = 0; i < props.items.length; i++) {
    const key = props.items[i][props.itemKey] as string;
    if (key === id) break;
    offset += itemHeights.value.get(key) || props.estimatedItemSize;
  }
  return offset;
};

const handleScroll = () => {
  if (containerRef.value) {
    scrollTop.value = containerRef.value.scrollTop;
    emit("scroll", scrollTop.value);
  }
};

const scrollToBottom = async () => {
  await nextTick();
  if (containerRef.value) {
    containerRef.value.scrollTop = containerRef.value.scrollHeight;
  }
};

const measureItemHeight = (id: string, height: number) => {
  itemHeights.value.set(id, height);
};

defineExpose({
  scrollToBottom,
  measureItemHeight,
});

watch(
  () => props.items.length,
  async () => {
    await nextTick();
    await scrollToBottom();
  },
);
</script>

<style scoped>
.virtual-scroll-container {
  height: 100%;
  overflow-y: auto;
  position: relative;
}

.virtual-scroll-content {
  position: relative;
  width: 100%;
}

.virtual-scroll-item {
  position: absolute;
  width: 100%;
  left: 0;
}
</style>
