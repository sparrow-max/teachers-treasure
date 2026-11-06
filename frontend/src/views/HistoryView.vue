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
          <span class="page-eyebrow">ARCHIVE · 点名档案</span>
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
          <span class="section-count">共 {{ total }} 场</span>
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
              <span class="cell mono" data-label="开始时间">{{ formatDateTime(item.started_at) }}</span>
              <span class="cell mono" data-label="结束时间">{{ formatDateTime(item.ended_at) }}</span>
              <template v-if="!isStudent">
                <span class="cell mono" data-label="总人数">{{ item.total_count }}</span>
                <span class="cell mono count-present" data-label="已签到">{{ item.present_count }}</span>
                <span class="cell mono count-absent" data-label="缺勤">{{ item.absent_count }}</span>
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
          <div class="detail-glow" aria-hidden="true"></div>
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
  margin: 6px 0 0;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.status-filter {
  width: 170px;
}

.status-filter :deep(.el-select__wrapper) {
  min-height: 42px;
  border-radius: 11px;
  background: #fff;
}

.history-table {
  overflow: hidden;
  border: 1px solid var(--color-border);
  border-radius: 14px;
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
  padding: 11px 16px;
  border-bottom: 1px solid var(--color-border);
  background: #f8faff;
}

.history-row {
  width: 100%;
  padding: 13px 16px;
  border: 0;
  border-bottom: 1px solid var(--color-border);
  background: transparent;
  color: inherit;
  font: inherit;
  font-size: 13px;
  text-align: left;
  cursor: pointer;
  font-variant-numeric: tabular-nums;
  transition: background 0.16s ease;
}

.history-row:hover {
  background: #f6f8ff;
}

.history-row:last-child {
  border-bottom: 0;
}

.history-title {
  font-weight: 600;
}

.mono {
  color: var(--color-text-secondary);
}

.count-present {
  color: var(--color-success);
  font-weight: 700;
}

.count-absent {
  color: var(--color-danger);
  font-weight: 700;
}

.pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 18px;
}

.drawer-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-summary {
  position: relative;
  overflow: hidden;
  padding: 22px 24px;
  border-radius: 18px;
  background: var(--gradient-ink);
  color: #fff;
}

.detail-glow {
  position: absolute;
  top: -100px;
  right: -40px;
  width: 220px;
  height: 220px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(124, 140, 255, 0.5), transparent 66%);
  pointer-events: none;
}

.detail-title {
  position: relative;
  margin: 0 0 8px;
  font-size: 19px;
  font-weight: 700;
}

.detail-meta {
  position: relative;
  margin: 2px 0;
  color: rgba(255, 255, 255, 0.58);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.detail-stats {
  position: relative;
  display: flex;
  flex-wrap: wrap;
  gap: 8px 18px;
  margin-top: 14px;
  color: #8ff0d2;
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

  .history-table {
    overflow: visible;
    border: 0;
    border-radius: 0;
  }

  .history-head {
    display: none;
  }

  .history-row,
  .history-grid--student {
    display: block;
    padding: 12px 14px;
    border: 1px solid var(--color-border);
    border-radius: 12px;
    margin-bottom: 8px;
    background: #fff;
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
    color: var(--color-text-muted);
    font-size: 11px;
    font-weight: 600;
  }

  .pagination {
    justify-content: center;
  }
}
</style>