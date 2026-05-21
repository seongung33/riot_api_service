import { createApp } from "vue";
import App from "./App.vue";
import "./styles.css";

// Vue 앱의 최상위 컴포넌트를 index.html의 #app에 마운트한다.
// 이후 App.vue 안의 ref/computed 상태와 template이 실제 화면 렌더링을 담당한다.
createApp(App).mount("#app");
