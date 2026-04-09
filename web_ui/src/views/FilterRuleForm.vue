<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import {
  getFilterRule,
  createFilterRule,
  updateFilterRule,
  type FilterRule,
  type FilterRuleCreateParams,
  type FilterRuleUpdateParams
} from '@/api/filterRule'
import { getAllSubscriptions, type Subscription } from '@/api/subscription'

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const submitting = ref(false)
const isEdit = computed(() => !!route.params.id)
const modalVisible = ref(true)
const mpList = ref<Subscription[]>([])

// 表单数据（mp_ids 为空表示全部公众号，对应后端 mp_id 为 "[]"）
const formData = ref<{
  mp_ids: string[]
  rule_name: string
  remove_ids: string
  remove_classes: string
  remove_selectors: string
  remove_attributes: Array<{ name: string; value: string; eq: boolean }>
  remove_regex: string
  remove_normal_tag: boolean
  priority: number
}>({
  mp_ids: [],
  rule_name: '',
  remove_ids: '',
  remove_classes: '',
  remove_selectors: '',
  remove_attributes: [],
  remove_regex: '',
  remove_normal_tag: false,
  priority: 0
})

const fetchMpList = async () => {
  try {
    const list = await getAllSubscriptions({ pageSize: 100 })
    mpList.value = list.filter(m => m.mp_name !== '精选文章')
  } catch {
    mpList.value = []
  }
}

// 新增属性行
const addAttributeRow = () => {
  formData.value.remove_attributes.push({ name: '', value: '', eq: false })
}

// 删除属性行
const removeAttributeRow = (index: number) => {
  formData.value.remove_attributes.splice(index, 1)
}

function resolveRuleMpIds(rule: FilterRule): string[] {
  if (Array.isArray(rule.mp_ids)) {
    return rule.mp_ids.map(String)
  }
  try {
    if (rule.mp_id && rule.mp_id.startsWith('[')) {
      const parsed = JSON.parse(rule.mp_id)
      return Array.isArray(parsed) ? parsed.map(String) : []
    }
    if (rule.mp_id) {
      return [rule.mp_id.trim()].filter(Boolean)
    }
  } catch {
    /* ignore */
  }
  return []
}

// 获取规则详情
const fetchRuleDetail = async (id: number) => {
  loading.value = true
  try {
    const rule = await getFilterRule(id)
    const mpIds = resolveRuleMpIds(rule)

    formData.value = {
      mp_ids: mpIds,
      rule_name: rule.rule_name,
      remove_ids: (rule.remove_ids || []).join('\n'),
      remove_classes: (rule.remove_classes || []).join('\n'),
      remove_selectors: (rule.remove_selectors || []).join('\n'),
      remove_attributes: rule.remove_attributes || [],
      remove_regex: (rule.remove_regex || []).join('\n'),
      remove_normal_tag: !!rule.remove_normal_tag,
      priority: rule.priority || 0
    }
  } catch (error) {
    Message.error('获取规则详情失败')
    router.back()
  } finally {
    loading.value = false
  }
}

// 提交表单
const handleSubmit = async () => {
  if (!formData.value.rule_name.trim()) {
    Message.warning('请输入规则名称')
    return
  }

  submitting.value = true
  try {
    const mpIdJson =
      formData.value.mp_ids.length > 0 ? JSON.stringify(formData.value.mp_ids) : '[]'

    const data: FilterRuleCreateParams | FilterRuleUpdateParams = {
      mp_id: mpIdJson,
      rule_name: formData.value.rule_name.trim(),
      remove_ids: formData.value.remove_ids
        .split('\n')
        .map(s => s.trim())
        .filter(Boolean),
      remove_classes: formData.value.remove_classes
        .split('\n')
        .map(s => s.trim())
        .filter(Boolean),
      remove_selectors: formData.value.remove_selectors
        .split('\n')
        .map(s => s.trim())
        .filter(Boolean),
      remove_attributes: formData.value.remove_attributes.filter(a => a.name.trim()),
      remove_regex: formData.value.remove_regex
        .split('\n')
        .map(s => s.trim())
        .filter(Boolean),
      remove_normal_tag: formData.value.remove_normal_tag ? 1 : 0,
      priority: formData.value.priority
    }

    if (isEdit.value) {
      await updateFilterRule(Number(route.params.id), data)
      Message.success('更新成功')
    } else {
      await createFilterRule(data as FilterRuleCreateParams)
      Message.success('创建成功')
    }
    router.push('/filter-rules')
  } catch (error: any) {
    Message.error(error?.response?.data?.message || '操作失败')
  } finally {
    submitting.value = false
  }
}

// 取消
const handleCancel = () => {
  router.back()
}

onMounted(async () => {
  await fetchMpList()
  if (isEdit.value) {
    fetchRuleDetail(Number(route.params.id))
  } else if (route.query.mp_id) {
    formData.value.mp_ids = [String(route.query.mp_id)]
  }
})
</script>

<template>
  <a-modal
    v-model:visible="modalVisible"
    :title="isEdit ? '编辑过滤规则' : '添加过滤规则'"
    :width="800"
    :footer="false"
    :unmount-on-close="true"
    class="filter-rule-modal"
    @cancel="handleCancel"
  >
    <a-spin :loading="loading">
      <div class="filter-rule-form">
        <a-form :model="formData" layout="vertical" @submit-success="handleSubmit">
          <a-form-item label="规则名称" field="rule_name" :rules="[{ required: true, message: '请输入规则名称' }]">
            <a-input v-model="formData.rule_name" placeholder="例如：移除广告元素" />
          </a-form-item>

          <a-form-item label="公众号选择" field="mp_ids">
            <a-select
              v-model="formData.mp_ids"
              multiple
              allow-clear
              allow-search
              :max-tag-count="3"
              placeholder="全部公众号"
              :options="mpList.map(m => ({ label: m.mp_name, value: m.id }))"
            />
            <template #extra>
              <span class="form-tip">不选或清空表示全部已订阅公众号；选中项保存为 mp_id 列表</span>
            </template>
          </a-form-item>

          <a-form-item label="优先级" field="priority">
            <a-input-number v-model="formData.priority" :min="0" :max="100" placeholder="数字越大优先级越高" />
            <template #extra>
              <span class="form-tip">数字越大优先级越高，同一公众号的规则按优先级依次执行</span>
            </template>
          </a-form-item>

          <a-divider>过滤规则配置</a-divider>

          <a-form-item label="移除ID元素">
            <a-textarea
              v-model="formData.remove_ids"
              placeholder="每行一个ID，例如: ad-banner, footer-nav"
              :auto-size="{ minRows: 2, maxRows: 6 }"
            />
            <template #extra>
              <span class="form-tip">按元素ID移除，每行一个</span>
            </template>
          </a-form-item>

          <a-form-item label="移除Class元素">
            <a-textarea
              v-model="formData.remove_classes"
              placeholder="每行一个class名称，例如: ad-container, recommend-box"
              :auto-size="{ minRows: 2, maxRows: 6 }"
            />
            <template #extra>
              <span class="form-tip">按CSS class移除，每行一个</span>
            </template>
          </a-form-item>

          <a-form-item label="CSS选择器">
            <a-textarea
              v-model="formData.remove_selectors"
              placeholder="每行一个CSS选择器，例如: div.ad-wrapper, .recommend-list > li"
              :auto-size="{ minRows: 2, maxRows: 6 }"
            />
            <template #extra>
              <span class="form-tip">使用CSS选择器精确定位元素，每行一个</span>
            </template>
          </a-form-item>

          <a-form-item label="属性过滤">
            <div class="attribute-list">
              <div v-for="(attr, index) in formData.remove_attributes" :key="index" class="attribute-row">
                <a-input v-model="attr.name" placeholder="属性名" class="attr-name-input" />
                <a-input v-model="attr.value" placeholder="属性值(可选)" class="attr-value-input" />
                <a-checkbox v-model="attr.eq" class="attr-checkbox">精确匹配</a-checkbox>
                <a-button type="text" status="danger" @click="removeAttributeRow(index)" class="attr-delete-btn">
                  <template #icon><icon-delete /></template>
                </a-button>
              </div>
              <a-button type="dashed" long @click="addAttributeRow">
                <template #icon><icon-plus /></template>
                添加属性条件
              </a-button>
            </div>
            <template #extra>
              <span class="form-tip">根据元素属性过滤，如 data-type="ad"</span>
            </template>
          </a-form-item>

          <a-form-item label="正则表达式">
            <a-textarea
              v-model="formData.remove_regex"
              placeholder="每行一个正则表达式，例如: &lt;div class=&quot;ad&quot;&gt;.*?&lt;/div&gt;"
              :auto-size="{ minRows: 2, maxRows: 6 }"
            />
            <template #extra>
              <span class="form-tip">使用正则表达式移除内容，每行一个。谨慎使用，确保表达式正确</span>
            </template>
          </a-form-item>

          <a-form-item label="移除常见HTML元素">
            <a-switch v-model="formData.remove_normal_tag" />
            <template #extra>
              <span class="form-tip">自动移除 script、style 标签和 HTML 注释等常见元素</span>
            </template>
          </a-form-item>

          <a-form-item>
            <a-space>
              <a-button type="primary" html-type="submit" :loading="submitting">
                {{ isEdit ? '保存修改' : '创建规则' }}
              </a-button>
              <a-button @click="handleCancel">取消</a-button>
            </a-space>
          </a-form-item>
        </a-form>
      </div>
    </a-spin>
  </a-modal>
</template>

<style scoped>
.filter-rule-form {
  width: 100%;
  display: block;
}

.filter-rule-form :deep(.arco-spin) {
  width: 100%;
  display: block;
}

.filter-rule-form :deep(.arco-form) {
  width: 100%;
}

.filter-rule-form :deep(.arco-form-item) {
  width: 100%;
}

.form-tip {
  color: var(--color-text-3);
  font-size: 12px;
}

.attribute-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.attribute-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.attr-name-input {
  width: 140px;
  flex-shrink: 0;
}

.attr-value-input {
  flex: 1;
  min-width: 0;
}

.attr-checkbox {
  white-space: nowrap;
  flex-shrink: 0;
}

.attr-delete-btn {
  flex-shrink: 0;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .attribute-row {
    flex-wrap: wrap;
    gap: 8px;
  }

  .attr-name-input {
    width: 100%;
  }

  .attr-value-input {
    width: 100%;
  }

  .attr-checkbox {
    order: 3;
    margin-left: 0;
  }

  .attr-delete-btn {
    order: 4;
    margin-left: auto;
  }

  /* 属性行在移动端的重新排列 */
  .attribute-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }

  .attr-name-input {
    grid-column: 1;
  }

  .attr-value-input {
    grid-column: 2;
  }

  .attr-checkbox {
    grid-column: 1;
  }

  .attr-delete-btn {
    grid-column: 2;
    justify-self: end;
  }

  /* 按钮组在移动端垂直排列 */
  :deep(.arco-form-item:last-child .arco-space) {
    flex-direction: column;
    width: 100%;
  }

  :deep(.arco-form-item:last-child .arco-space .arco-space-item) {
    width: 100%;
  }

  :deep(.arco-form-item:last-child .arco-btn) {
    width: 100%;
  }
}
</style>
<style>
/* 模态框样式 */
.filter-rule-modal .arco-modal-body {
  padding: 16px 20px;
}

.filter-rule-modal .arco-modal-body > .arco-spin,
.filter-rule-modal .arco-modal-body > .arco-spin > .filter-rule-form {
  width: 100%;
}

/* 模态框移动端适配 */
@media (max-width: 768px) {
  .filter-rule-modal .arco-modal {
    width: 95% !important;
    max-width: 95% !important;
    margin: 20px auto;
  }

  .filter-rule-modal .arco-modal-body {
    padding: 12px;
    max-height: 60vh;
    overflow-y: auto;
  }
}
</style>
