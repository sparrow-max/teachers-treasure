<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import AbsenceList from '@/components/AbsenceList.vue'
import AppHeader from '@/components/AppHeader.vue'
import CheckinList from '@/components/CheckinList.vue'
import { getRollcall, listRollcalls } from '@/api/rollcalls'
import { useAuthStore } from '@/stores/auth'
import { formatDateTime } from '@/utils/format'
import { notifyError } from '@/utils/notify'

import type { Session, SessionDetail, SessionStatus } from '@/types/api'

type TagType = 'warning' | 'info'

const auth = useAuthStore()

const items = ref<Session[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const status = ref<SessionStatus | '' | undefined>('')
const loading = ref(false)

const drawerVisible = ref(false)
const detail = ref<SessionDetail | null>(null)
const detailLoading = ref(false)

const isStudent = computed(() => auth.isStudent)

function statusText(value: SessionStatus): string {
  return value === 'calling' ? '点名中' : '已结束'
}

function statusType(value: SessionStatus): TagType {
  return value === 'calling' ? 'warning' : 'info'
}

async function load(): Promise<void> {
  loading.value = true
  try {
    const result = await listRollcalls({
      page: page.value,
      page_size: pageSize,
      status: status.value || undefined,
    })
    items.value = result.items
    total.value = result.total
  } catch (error) {
    notifyError(error)
  } finally {
    loading.value = false
  }
}

function onStatusChange(): void {
  page.value = 1
  void load()
}

function onPageChange(value: number): void {
  page.value = value
  void load()
}

async function openDetail(session: Session): Promise<void> {
  drawerVisible.value = true
  detail.value = null
  detailLoading.value = true

  try {
    detail.value = await getRollcall(session.id)
  } catch (error) {
    drawerVisible.value = false
    notifyError(error)
  } finally {
    detailLoading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="app-shell">
    <AppHeader active="history" />

    <main class="page">
      <div class="page-head">
        <div>
          <h1 class="page-title">历史点名</h1>
          <p class="page-subtitle">
            {{
              isStudent
                ? '查看你参与过的场次与本人签到、缺勤记录'
                : '查看往次点名的统计与签到、缺勤明细'
            }}
          </p>
        </div>
        <el-select
          v-model="status"
          class="status-filter"
          placeholder="全部场次"
          clearable
          @change="onStatusChange"
          @clear="onStatusChange"
        >
          <el-option label="点名中" value="calling" />
          <el-option label="已结束" value="ended" />
        </el-select>
      </div>

      <section class="card">
        <div class="section-head">
          <h2 class="section-title">场次列表</h2>
          <span class="section-hint">共 {{ total }} 场</span>
        </div>

        <p v-if="loading" class="loading">加载中…</p>

        <template v-else-if="items.length">
          <div class="history-table">
            <div
              class="history-head history-grid grid-head"
              :class="{ 'history-grid--student': isStudent }"
            >
              <span>标题</span>
              <span>状态</span>
              <span>开始时间</span>
              <span>结束时间</span>
              <template v-if="!isStudent">
                <span>总人数</span>
                <span>已签到</span>
                <span>缺勤</span>
              </template>
            </div>

            <button
              v-for="item in items"
              :key="item.id"
              type="button"
              class="history-row history-grid"
              :class="{ 'history-grid--student': isStudent }"
              @click="openDetail(item)"
            >
              <span class="cell history-title" data-label="标题">{{ item.title }}</span>
              <span class="cell" data-label="状态">
                <el-tag :type="statusType(item.status)" size="small" effect="light">
                  {{ statusText(item.status) }}
                </el-tag>
              </span>
              <span class="cell" data-label="开始时间">{{ formatDateTime(item.started_at) }}</span>
              <span class="cell" data-label="结束时间">{{ formatDateTime(item.ended_at) }}</span>
              <template v-if="!isStudent">
                <span class="cell" data-label="总人数">{{ item.total_count }}</span>
                <span class="cell" data-label="已签到">{{ item.present_count }}</span>
                <span class="cell" data-label="缺勤">{{ item.absent_count }}</span>
              </template>
            </button>
          </div>

          <div class="pagination">
            <el-pagination
              background
              layout="prev, pager, next"
              :total="total"
              :page-size="pageSize"
              :current-page="page"
              hide-on-single-page
              @current-change="onPageChange"
            />
          </div>
        </template>

        <p v-else class="empty">
          {{ isStudent ? '还没有你参与过的场次' : '还没有历史场次，先回主页发起一次点名吧' }}
        </p>
      </section>
    </main>

    <el-drawer
      v-model="drawerVisible"
      title="场次明细"
      size="min(520px, 92vw)"
      class="history-drawer"
    >
      <div v-if="detailLoading" class="loading">加载中…</div>

      <div v-else-if="detail" class="drawer-body">
        <div class="detail-summary">
          <h3 class="detail-title">{{ detail.session.title }}</h3>
          <p class="detail-meta">
            开始：{{ formatDateTime(detail.session.started_at) }}
          </p>
          <p class="detail-meta">
            结束：{{ formatDateTime(detail.session.ended_at) }}
          </p>
          <div v-if="!isStudent" class="detail-stats">
            <span>总人数 {{ detail.session.total_count }}</span>
            <span>签到 {{ detail.session.present_count }}</span>
            <span>缺勤 {{ detail.session.absent_count }}</span>
            <span>待签到 {{ detail.session.pending_count }}</span>
          </div>
          <div v-else class="detail-stats">
            <span>我的记录 {{ detail.records.length }} 条</span>
          </div>
        </div>

        <CheckinList :records="detail.records" />
        <AbsenceList
          :records="detail.records"
          :ended="detail.session.status === 'ended'"
        />
      </div>

      <p v-else class="empty">暂无数据</p>
    </el-drawer>
  </div>
</template>

<style scoped>
.page-subtitle {
  margin: 4px 0 0;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.status-filter {
  width: 160px;
}

.history-grid {
  display: grid;
  grid-template-columns: 2fr 0.8fr 1.5fr 1.5fr 0.6fr 0.7fr 0.7fr;
  gap: 12px;
  align-items: center;
}

.history-grid--student {
  grid-template-columns: 2fr 0.8fr 1.5fr 1.5fr;
}

.history-head {
  padding: 0 12px 8px;
  border-bottom: 1px solid var(--color-border);
}

.history-row {
  width: 100%;
  padding: 12px;
  border: 0;
  border-bottom: 1px solid var(--color-border);
  background: transparent;
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
  font-variant-numeric: tabular-nums;
}

.history-row:hover {
  background: #f8fafc;
}

.history-row:last-child {
  border-bottom: 0;
}

.history-title {
  font-weight: 500;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.drawer-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-summary {
  padding: 16px;
  border-radius: 10px;
  background: var(--color-primary-soft);
}

.detail-title {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 600;
}

.detail-meta {
  margin: 2px 0;
  color: var(--color-text-secondary);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.detail-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  margin-top: 10px;
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 600;
}

.drawer-body :deep(.card) {
  box-shadow: none;
  border: 1px solid var(--color-border);
}

@media (max-width: 767px) {
  .status-filter {
    width: 100%;
  }

  .history-head {
    display: none;
  }

  .history-row,
  .history-grid--student {
    display: block;
    padding: 12px;
    border: 1px solid var(--color-border);
    border-radius: 10px;
    margin-bottom: 8px;
  }

  .history-row:last-child {
    margin-bottom: 0;
    border-bottom: 1px solid var(--color-border);
  }

  .history-row .cell {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    padding: 3px 0;
  }

  .history-row .cell::before {
    content: attr(data-label);
    flex: none;
    color: var(--color-text-secondary);
    font-size: 12px;
  }

  .pagination {
    justify-content: center;
  }
}
</style>