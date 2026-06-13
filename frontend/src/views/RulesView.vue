<script setup>
import { onMounted, reactive, ref } from 'vue'
import { Check, Save } from 'lucide-vue-next'

import { ruleApi } from '../api/modules'
import EmptyState from '../components/EmptyState.vue'
import MessageBar from '../components/MessageBar.vue'

const rules = ref([])
const savingId = ref(null)
const savedId = ref(null)
const message = reactive({ text: '', type: 'info' })

async function loadRules() {
  try {
    rules.value = await ruleApi.list()
  } catch (error) {
    message.text = error.message
    message.type = 'error'
  }
}

async function saveRule(rule) {
  savingId.value = rule.id
  savedId.value = null
  message.text = ''
  try {
    const updated = await ruleApi.update(rule.id, {
      minIntervalDays: rule.minIntervalDays,
      maxDailySlots: rule.maxDailySlots,
      maxSlotsPerTimeslot: rule.maxSlotsPerTimeslot,
      allowWeekend: rule.allowWeekend,
      passingScore: rule.passingScore,
      makeupWaitDays: rule.makeupWaitDays,
      enabled: rule.enabled
    })
    const index = rules.value.findIndex((item) => item.id === updated.id)
    rules.value[index] = updated
    savedId.value = updated.id
    message.text = `${updated.subject} 规则已保存成功`
    message.type = 'success'
    setTimeout(() => {
      if (savedId.value === updated.id) {
        savedId.value = null
      }
    }, 2500)
  } catch (error) {
    message.text = error.message
    message.type = 'error'
  } finally {
    savingId.value = null
  }
}

onMounted(loadRules)
</script>

<template>
  <section class="panel">
    <div class="panel-heading">
      <div>
        <h3>约考规则设置</h3>
        <p>控制预约提前天数、每日名额、时段名额、周末预约、合格线和补考等待期。</p>
      </div>
    </div>

    <MessageBar :message="message.text" :type="message.type" />
    <EmptyState v-if="rules.length === 0" title="暂无规则" description="后端初始化后会自动生成默认规则。" />

    <div class="rule-grid">
      <article v-for="rule in rules" :key="rule.id" class="rule-card" :class="{ 'rule-saved': savedId === rule.id }">
        <div class="rule-title">
          <h4>{{ rule.subject }}</h4>
          <label class="switch">
            <input v-model="rule.enabled" type="checkbox" />
            <span>开放预约</span>
          </label>
        </div>

        <div class="rule-fields">
          <label>
            <span>提前天数</span>
            <input v-model.number="rule.minIntervalDays" min="0" type="number" />
          </label>
          <label>
            <span>每日总名额</span>
            <input v-model.number="rule.maxDailySlots" min="0" type="number" />
          </label>
          <label>
            <span>每时段名额</span>
            <input v-model.number="rule.maxSlotsPerTimeslot" min="0" type="number" />
          </label>
          <label>
            <span>合格线</span>
            <input v-model.number="rule.passingScore" min="0" max="100" type="number" />
          </label>
          <label>
            <span>补考等待</span>
            <input v-model.number="rule.makeupWaitDays" min="0" type="number" />
          </label>
        </div>

        <label class="checkbox-row">
          <input v-model="rule.allowWeekend" type="checkbox" />
          <span>允许周末预约</span>
        </label>

        <button class="primary-button" :disabled="savingId === rule.id" type="button" @click="saveRule(rule)">
          <Check v-if="savedId === rule.id" :size="18" />
          <Save v-else :size="18" />
          <span v-if="savingId === rule.id">保存中</span>
          <span v-else-if="savedId === rule.id">已保存</span>
          <span v-else>保存规则</span>
        </button>
      </article>
    </div>
  </section>
</template>

<style scoped>
.rule-card {
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

.rule-card.rule-saved {
  border-color: #1e6b3f;
  box-shadow: 0 10px 24px rgba(30, 107, 63, 0.12);
}
</style>
