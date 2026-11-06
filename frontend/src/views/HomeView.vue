<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import StudentHomeView from '@/views/StudentHomeView.vue'
import TeacherHomeView from '@/views/TeacherHomeView.vue'

const auth = useAuthStore()
</script>

<template>
  <TeacherHomeView v-if="auth.isTeacher || auth.isMonitor" />
  <StudentHomeView v-else />
</template>