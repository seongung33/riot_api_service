<script setup>
import { computed, ref } from "vue";

const form = ref({
  game_name: "",
  tag_line: "KR1",
  region: "asia",
  count: 5,
  queue: 420,
});

const result = ref(null);
const matches = ref([]);
const isLoading = ref(false);
const isLoadingMatches = ref(false);
const errorMessage = ref("");

const summary = computed(() => result.value?.summary ?? null);
const champions = computed(() => result.value?.champions ?? []);
const feedback = computed(() => result.value?.feedback ?? []);
const hasResult = computed(() => Boolean(result.value));

async function searchAccount() {
  errorMessage.value = "";
  result.value = null;
  matches.value = [];
  isLoading.value = true;

  try {
    const response = await fetch("/api/accounts/search/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        game_name: form.value.game_name.trim(),
        tag_line: form.value.tag_line.trim(),
        region: form.value.region,
        count: Number(form.value.count),
        queue: Number(form.value.queue),
      }),
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.detail || "검색 중 오류가 발생했습니다.");
    }

    result.value = data;
    await loadRecentMatches(data.account_id);
  } catch (error) {
    errorMessage.value = error.message;
  } finally {
    isLoading.value = false;
  }
}

async function loadRecentMatches(accountId) {
  if (!accountId) return;
  isLoadingMatches.value = true;

  try {
    const response = await fetch(`/api/accounts/${accountId}/matches/?limit=10`);
    const data = await response.json().catch(() => []);
    if (!response.ok) return;
    matches.value = data;
  } finally {
    isLoadingMatches.value = false;
  }
}

function formatPercent(value) {
  return `${Number(value || 0).toFixed(1)}%`;
}

function formatNumber(value, digits = 1) {
  return Number(value || 0).toFixed(digits);
}

function formatKda(match) {
  return `${match.kills}/${match.deaths}/${match.assists}`;
}

function formatDate(value) {
  if (!value) return "";
  return new Intl.DateTimeFormat("ko-KR", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}
</script>

<template>
  <main class="app-shell">
    <section class="search-section">
      <div>
        <p class="eyebrow">Riot API 기반 LoL 인사이트</p>
        <h1>소환사 최근 경기 분석</h1>
        <p class="intro">
          Riot ID를 입력하면 최근 랭크 경기 데이터를 가져와 승률, KDA, 챔피언 성과와 개선 피드백을 보여줍니다.
        </p>
      </div>

      <form class="search-form" @submit.prevent="searchAccount">
        <label>
          Riot ID
          <input v-model="form.game_name" type="text" placeholder="Hide on bush" required />
        </label>

        <label>
          Tagline
          <input v-model="form.tag_line" type="text" placeholder="KR1" required />
        </label>

        <label>
          Region
          <select v-model="form.region">
            <option value="asia">asia</option>
            <option value="americas">americas</option>
            <option value="europe">europe</option>
            <option value="sea">sea</option>
          </select>
        </label>

        <label>
          경기 수
          <input v-model.number="form.count" type="number" min="1" max="20" />
        </label>

        <button type="submit" :disabled="isLoading">
          {{ isLoading ? "분석 중..." : "분석 시작" }}
        </button>
      </form>

      <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
    </section>

    <section v-if="hasResult" class="results-grid">
      <article class="panel summary-panel">
        <div class="panel-header">
          <div>
            <p class="eyebrow">Summary</p>
            <h2>{{ result.game_name }}#{{ result.tag_line }}</h2>
          </div>
          <span class="region-pill">{{ result.region }}</span>
        </div>

        <div class="stat-grid">
          <div class="stat-item">
            <span>최근 경기</span>
            <strong>{{ summary.game_count }}</strong>
          </div>
          <div class="stat-item">
            <span>승률</span>
            <strong>{{ formatPercent(summary.win_rate) }}</strong>
          </div>
          <div class="stat-item">
            <span>평균 KDA</span>
            <strong>{{ formatNumber(summary.average_kda) }}</strong>
          </div>
          <div class="stat-item">
            <span>평균 CS</span>
            <strong>{{ formatNumber(summary.average_cs) }}</strong>
          </div>
          <div class="stat-item">
            <span>평균 데스</span>
            <strong>{{ formatNumber(summary.average_deaths) }}</strong>
          </div>
          <div class="stat-item">
            <span>시야 점수</span>
            <strong>{{ formatNumber(summary.average_vision_score) }}</strong>
          </div>
        </div>

        <div class="summary-footer">
          <span>주 포지션: {{ summary.main_position || "정보 없음" }}</span>
          <span>챔피언 풀: {{ summary.champion_pool.join(", ") || "정보 없음" }}</span>
        </div>
      </article>

      <article class="panel feedback-panel">
        <div class="panel-header">
          <div>
            <p class="eyebrow">Feedback</p>
            <h2>개선 피드백</h2>
          </div>
        </div>

        <div v-if="feedback.length" class="feedback-list">
          <div v-for="item in feedback" :key="`${item.category}-${item.metric}-${item.target || 'all'}`" class="feedback-card">
            <div class="feedback-meta">
              <span>{{ item.category }}</span>
              <strong>{{ item.metric }}: {{ formatNumber(item.value) }}</strong>
            </div>
            <p>{{ item.interpretation }}</p>
            <p class="recommendation">{{ item.recommendation }}</p>
          </div>
        </div>
        <p v-else class="empty-message">현재 조건에서는 별도 개선 피드백이 없습니다.</p>
      </article>

      <article class="panel champion-panel">
        <div class="panel-header">
          <div>
            <p class="eyebrow">Champions</p>
            <h2>챔피언 성과</h2>
          </div>
        </div>

        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>챔피언</th>
                <th>경기</th>
                <th>승률</th>
                <th>KDA</th>
                <th>CS</th>
                <th>포지션</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="champion in champions" :key="champion.champion_id">
                <td>{{ champion.champion_name }}</td>
                <td>{{ champion.game_count }}</td>
                <td>{{ formatPercent(champion.win_rate) }}</td>
                <td>{{ formatNumber(champion.average_kda) }}</td>
                <td>{{ formatNumber(champion.average_cs) }}</td>
                <td>{{ champion.positions.join(", ") }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </article>

      <article class="panel matches-panel">
        <div class="panel-header">
          <div>
            <p class="eyebrow">Matches</p>
            <h2>최근 경기</h2>
          </div>
          <span v-if="isLoadingMatches" class="muted">불러오는 중</span>
        </div>

        <div v-if="matches.length" class="match-list">
          <div v-for="match in matches" :key="match.match_id" class="match-row" :class="{ win: match.win, loss: !match.win }">
            <div>
              <strong>{{ match.champion_name }}</strong>
              <span>{{ formatDate(match.game_start_time) }} · {{ match.individual_position }}</span>
            </div>
            <div>
              <strong>{{ match.win ? "승리" : "패배" }}</strong>
              <span>{{ formatKda(match) }} · KDA {{ formatNumber(match.kda) }}</span>
            </div>
            <div>
              <strong>{{ match.total_cs }} CS</strong>
              <span>{{ match.gold_earned.toLocaleString() }} 골드</span>
            </div>
          </div>
        </div>
        <p v-else class="empty-message">표시할 최근 경기가 없습니다.</p>
      </article>
    </section>
  </main>
</template>
