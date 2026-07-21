<template>
  <div
    ref="containerRef"
    class="virtual-scroll-container"
    @scroll="handleScroll"
  >
    <div class="virtual-scroll-content">
      <div
        v-for="item in items"
        :key="item[itemKey]"
        class="virtual-scroll-item"
      >
        <slot :item="item"></slot>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from "vue";

const props = withDefaults(
  defineProps<{
    items: any[];
    itemKey: string;
  }>(),
  {},
);

const emit = defineEmits<{
  (e: "scroll", scrollTop: number): void;
}>();

const containerRef = ref<HTMLElement | null>(null);

const handleScroll = () => {
  if (containerRef.value) {
    emit("scroll", containerRef.value.scrollTop);
  }
};

const scrollToBottom = async () => {
  await nextTick();
  await nextTick();
  if (containerRef.value) {
    containerRef.value.scrollTop = containerRef.value.scrollHeight;
  }
};

defineExpose({
  scrollToBottom,
});

watch(
  () => props.items.length,
  async () => {
    await scrollToBottom();
  },
);
</script>

<style scoped>
.virtual-scroll-container {
  height: 100%;
  overflow-y: auto;
}

.virtual-scroll-content {
  min-height: 100%;
}

.virtual-scroll-item {
  width: 100%;
}
</style>
