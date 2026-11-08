<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'

import AppHeader from '@/components/AppHeader.vue'
import PersonalRecords from '@/components/PersonalRecords.vue'
import StudentCheckinCard from '@/components/StudentCheckinCard.vue'
import { useRollcallStore } from '@/stores/rollcall'
import { notifyError } from '@/utils/notify'

const rollcallStore = useRollcallStore()

onMounted(async () => {
  try {
    await rollcallStore.fetchCurrentSession()
  } catch (error) {
    notifyError(error)
  }
})

onUnmounted(() => {
  rollcallStore.stopPolling()
})
</script>

<template>
  <div class="app-shell">
    <AppHeader active="home" />

    <main class="page">
      <section class="student-hero fade-in">
        <div class="student-hero-copy">
          <span class="student-eyebrow">
            <span class="student-eyebrow-dot"></span>
            STUDENT · 本人签到
          </span>
          <h1 class="page-title">我的点名</h1>
          <p class="page-subtitle">查看当前点名状态，完成本人签到并查看记录</p>
        </div>

        <div class="student-hero-art" aria-hidden="true">
          <span class="art-ring art-ring--outer"></span>
          <span class="art-ring art-ring--inner"></span>
          <span class="art-check">
            <svg viewBox="0 0 24 24" width="26" height="26" fill="none">
              <path
                d="M6.5 12.5l3.6 3.6 7.4-7.9"
                stroke="currentColor"
                stroke-width="2.6"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </span>
        </div>
      </section>

      <StudentCheckinCard />
      <PersonalRecords
        :session="rollcallStore.current?.session ?? null"
        :records="rollcallStore.current?.records ?? []"
      />
    </main>
  </div>
</template>

<style scoped>
.student-hero {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  overflow: hidden;
  margin-bottom: 20px;
  padding: 30px 32px;
  border-radius: var(--radius-lg);
  background:
    radial-gradient(520px 240px at 92% 0%, rgba(18, 185, 129, 0.18), transparent 65%),
    var(--gradient-ink);
  box-shadow:
    0 1px 2px rgba(15, 23, 42, 0.08),
    0 30px 60px -34px rgba(16, 30, 76, 0.85);
  color: #fff;
}

.student-hero-copy {
  position: relative;
  z-index: 1;
  min-width: 0;
}

.student-eyebrow {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.62);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.16em;
}

.student-eyebrow-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #6ff0c8;
  box-shadow: 0 0 0 4px rgba(111, 240, 200, 0.16);
}

.student-hero .page-title {
  margin-top: 10px;
  color: #fff;
}

.student-hero .page-subtitle {
  max-width: 460px;
  color: rgba(255, 255, 255, 0.62);
}

.student-hero-art {
  position: relative;
  display: grid;
  flex: none;
  width: 108px;
  height: 108px;
  place-items: center;
}

.art-ring {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.16);
}

.art-ring--outer {
  inset: 0;
}

.art-ring--inner {
  inset: 16px;
  border-color: rgba(111, 240, 200, 0.28);
}

.art-check {
  display: grid;
  width: 58px;
  height: 58px;
  place-items: center;
  border-radius: 50%;
  background: linear-gradient(135deg, #12b981, #4fd7b4);
  box-shadow:
    0 0 0 10px rgba(18, 185, 129, 0.14),
    0 18px 34px -14px rgba(18, 185, 129, 0.8);
  color: #fff;
}

@media (max-width: 900px) {
  .student-hero {
    padding: 26px;
  }

  .student-hero-art {
    width: 88px;
    height: 88px;
  }

  .art-check {
    width: 50px;
    height: 50px;
  }
}

@media (max-width: 767px) {
  .student-hero {
    margin-bottom: 14px;
    padding: 22px 18px;
    border-radius: 20px;
  }

  .student-hero-art {
    display: none;
  }

  .student-hero :deep(.page-title) {
    font-size: 24px;
  }
}
</style>