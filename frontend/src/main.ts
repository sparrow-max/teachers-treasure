import { createPinia } from 'pinia'
import { createApp } from 'vue'
import ElementPlus, { ElMessage } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

import 'element-plus/dist/index.css'
import './styles/main.css'

import { setAuthFailureHandler } from './api/authFailure'
import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(ElementPlus, { locale: zhCn })

setAuthFailureHandler((code) => {
  const auth = useAuthStore(pinia)

  if (code === 40302) {
    if (router.currentRoute.value.path !== '/change-password') {
      void router.replace('/change-password')
    }
    return
  }

  auth.clearSession()
  if (code === 40103) {
    ElMessage.warning('登录已过期，请重新登录')
  }
  if (router.currentRoute.value.path !== '/login') {
    void router.replace('/login')
  }
})

app.mount('#app')