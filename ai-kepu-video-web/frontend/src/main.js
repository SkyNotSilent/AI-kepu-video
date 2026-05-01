import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

// 引入 Vant 组件库
import Vant from 'vant'
import 'vant/lib/index.css'

const app = createApp(App)

app.use(router)
app.use(Vant)

app.mount('#app')
