import { defineStore } from 'pinia'

import { ApiError } from '@/api/error'
import {
  checkin as apiCheckin,
  endRollcall as apiEndRollcall,
  getRollcall,
  listRollcalls,
  startRollcall as apiStartRollcall,
} from '@/api/rollcalls'

import type {
  RecordItem,
  RecordStatus,
  RollcallCreate,
  SessionDetail,
} from '@/types/api'

const SESSION_KEY = 'teacher-treasure.current-session'

const STATUS_PRIORITY: Record<RecordStatus, number> = {
  pending: 1,
  absent: 2,
  present: 3,
}

function mergeDetail(local: SessionDetail, remote: SessionDetail): SessionDetail {
  const localRecords = new Map(local.records.map((record) => [record.id, record]))
  const records = remote.records.map((remoteRecord) => {
    const localRecord = localRecords.get(remoteRecord.id)
    if (
      localRecord &&
      STATUS_PRIORITY[localRecord.status] > STATUS_PRIORITY[remoteRecord.status]
    ) {
      return localRecord
    }
    return remoteRecord
  })

  return {
    session: { ...remote.session },
    records,
  }
}

function readStoredSessionId(): number | null {
  const raw = sessionStorage.getItem(SESSION_KEY)
  if (!raw) {
    return null
  }

  const sessionId = Number(raw)
  if (!Number.isInteger(sessionId) || sessionId <= 0) {
    sessionStorage.removeItem(SESSION_KEY)
    return null
  }
  return sessionId
}

function storeSessionId(sessionId: number): void {
  sessionStorage.setItem(SESSION_KEY, String(sessionId))
}

export const useRollcallStore = defineStore('rollcall', {
  state: () => ({
    current: null as SessionDetail | null,
    pollingTimer: null as number | null,
  }),

  getters: {
    session: (state) => state.current?.session ?? null,

    presentRecords: (state): RecordItem[] =>
      (state.current?.records ?? [])
        .filter((record) => record.status === 'present')
        .sort((a, b) => a.order_no - b.order_no),

    absentRecords: (state): RecordItem[] =>
      (state.current?.records ?? [])
        .filter((record) => record.status === 'absent')
        .sort((a, b) => a.order_no - b.order_no),

    pendingRecords: (state): RecordItem[] =>
      (state.current?.records ?? [])
        .filter((record) => record.status === 'pending')
        .sort((a, b) => a.order_no - b.order_no),
  },

  actions: {
    async startRollcall(payload: RollcallCreate = {}) {
      const detail = await apiStartRollcall(payload)
      this.current = detail
      this.recomputeCounts()
      storeSessionId(detail.session.id)
      this.startPolling()
      return detail
    },

    async restoreRollcall() {
      const sessionId = readStoredSessionId()
      if (!sessionId) {
        return null
      }

      try {
        const detail = await getRollcall(sessionId)
        this.current = detail
        this.recomputeCounts()
        if (detail.session.status === 'calling') {
          this.startPolling()
        }
        return detail
      } catch (error) {
        if (error instanceof ApiError && error.code === 40402) {
          this.reset()
          return null
        }
        throw error
      }
    },

    async ensureCurrentSession() {
      const restored = await this.restoreRollcall()
      if (restored) {
        return restored
      }

      const page = await listRollcalls({
        page: 1,
        page_size: 1,
        status: 'calling',
      })
      if (!page.items.length) {
        return null
      }

      const detail = await getRollcall(page.items[0].id)
      this.current = detail
      this.recomputeCounts()
      this.startPolling()
      return detail
    },

    async fetchCurrentSession() {
      const calling = await listRollcalls({
        page: 1,
        page_size: 1,
        status: 'calling',
      })
      if (calling.items.length) {
        const detail = await getRollcall(calling.items[0].id)
        this.current = detail
        this.recomputeCounts()
        this.startPolling()
        return detail
      }

      const ended = await listRollcalls({
        page: 1,
        page_size: 1,
        status: 'ended',
      })
      if (ended.items.length) {
        const detail = await getRollcall(ended.items[0].id)
        this.current = detail
        this.recomputeCounts()
        this.stopPolling()
        return detail
      }

      this.reset()
      return null
    },

    async checkin() {
      const current = this.current
      if (!current) {
        throw new ApiError(40402, '点名场次不存在', 404)
      }

      const record = await apiCheckin(current.session.id)

      if (this.current?.session.id === current.session.id) {
        const index = this.current.records.findIndex(
          (item) => item.id === record.id,
        )
        if (index >= 0) {
          this.current.records[index] = record
        } else {
          this.current.records.push(record)
        }
        this.recomputeCounts()
      }

      return record
    },

    async endRollcall() {
      const current = this.current
      if (!current) {
        throw new ApiError(40402, '点名场次不存在', 404)
      }

      const detail = await apiEndRollcall(current.session.id)
      if (this.current?.session.id === current.session.id) {
        this.current = detail
        this.recomputeCounts()
        this.stopPolling()
      }
      return detail
    },

    async refreshCurrent() {
      const current = this.current
      if (!current) {
        return null
      }

      const detail = await getRollcall(current.session.id)
      this.current = detail
      this.recomputeCounts()
      if (detail.session.status === 'ended') {
        this.stopPolling()
      }
      return detail
    },

    recomputeCounts() {
      if (!this.current) {
        return
      }

      let present = 0
      let absent = 0
      let pending = 0
      for (const record of this.current.records) {
        if (record.status === 'present') {
          present += 1
        } else if (record.status === 'absent') {
          absent += 1
        } else {
          pending += 1
        }
      }

      this.current.session.total_count = this.current.records.length
      this.current.session.present_count = present
      this.current.session.absent_count = absent
      this.current.session.pending_count = pending
    },

    startPolling() {
      this.stopPolling()
      if (this.current?.session.status !== 'calling') {
        return
      }

      this.pollingTimer = window.setInterval(() => {
        void this.poll()
      }, 5000)
    },

    stopPolling() {
      if (this.pollingTimer !== null) {
        window.clearInterval(this.pollingTimer)
        this.pollingTimer = null
      }
    },

    async poll() {
      const current = this.current
      if (!current || current.session.status !== 'calling') {
        this.stopPolling()
        return
      }

      try {
        const remote = await getRollcall(current.session.id)
        if (!this.current || this.current.session.id !== remote.session.id) {
          return
        }

        this.current = mergeDetail(this.current, remote)
        this.recomputeCounts()

        if (this.current.session.status === 'ended') {
          this.stopPolling()
        }
      } catch (error) {
        if (error instanceof ApiError && error.code === 40402) {
          this.reset()
        }
      }
    },

    reset() {
      this.stopPolling()
      this.current = null
      sessionStorage.removeItem(SESSION_KEY)
    },
  },
})