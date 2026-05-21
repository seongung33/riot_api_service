<script setup>
import { computed, ref } from "vue";

// 검색 폼의 입력 상태를 하나의 ref 객체로 관리한다.
// v-model은 이 객체의 각 필드와 input/select 값을 양방향으로 연결한다.
const form = ref({
  game_name: "",
  tag_line: "KR1",
  region: "asia",
  count: 5,
  queue: 420,
});

// result는 /api/accounts/search/ 응답 전체를 담는다.
// matches는 검색 직후 추가로 불러오는 최근 경기 목록이며, 두 데이터를 분리해 화면 섹션별 로딩을 따로 제어한다.
const result = ref(null);
const matches = ref([]);
const isLoading = ref(false);
const isLoadingMatches = ref(false);
const errorMessage = ref("");

// computed는 result에서 화면에 필요한 하위 데이터만 꺼내는 읽기 전용 파생 상태다.
// result가 null인 초기 상태에서도 템플릿이 안전하게 렌더링되도록 기본값을 둔다.
const summary = computed(() => result.value?.summary ?? null);
const champions = computed(() => result.value?.champions ?? []);
const feedback = computed(() => result.value?.feedback ?? []);
const hasResult = computed(() => Boolean(result.value));

async function searchAccount() {
  // 새 검색을 시작할 때 이전 결과와 에러를 비워 화면이 과거 응답을 계속 보여주지 않게 한다.
  errorMessage.value = "";
  result.value = null;
  matches.value = [];
  isLoading.value = true;

  try {
    // 프론트의 검색 form submit 이벤트가 이 POST 요청으로 연결된다.
    // Django AccountSearchView는 이 body를 serializer로 검증한 뒤 Riot API import와 요약 분석을 수행한다.
    const response = await fetch("/api/accounts/search/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        // 사용자가 입력한 공백은 검색 정확도를 떨어뜨릴 수 있어 API로 보내기 전에 trim한다.
        // count/queue는 number input이어도 안전하게 숫자로 변환해 백엔드 serializer 범위 검증을 통과시킨다.
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

    // result가 채워지면 computed(summary/champions/feedback)가 즉시 다시 계산되고,
    // v-if="hasResult" 아래의 결과 패널들이 렌더링된다.
    result.value = data;
    // 검색 응답에는 요약과 피드백이 들어 있고, 최근 경기 리스트는 별도 endpoint에서 가져온다.
    // 이렇게 분리하면 이후 경기 목록만 새로고침하는 흐름으로 확장하기 쉽다.
    await loadRecentMatches(data.account_id);
  } catch (error) {
    errorMessage.value = error.message;
  } finally {
    isLoading.value = false;
  }
}

async function loadRecentMatches(accountId) {
  // account_id가 없으면 계정 검색이 완료되지 않은 상태이므로 경기 목록 요청을 보내지 않는다.
  if (!accountId) return;
  isLoadingMatches.value = true;

  try {
    // accounts/<id>/matches/는 이미 저장된 MatchParticipant를 최근 경기 순으로 직렬화해 반환한다.
    const response = await fetch(`/api/accounts/${accountId}/matches/?limit=10`);
    const data = await response.json().catch(() => []);
    if (!response.ok) return;
    // matches가 바뀌면 template의 v-for가 match-row 목록을 다시 렌더링한다.
    matches.value = data;
  } finally {
    isLoadingMatches.value = false;
  }
}

function formatPercent(value) {
  // API는 숫자만 내려주고, 화면 표시 단위(%)는 프론트에서 붙인다.
  return `${Number(value || 0).toFixed(1)}%`;
}

function formatNumber(value, digits = 1) {
  // null/undefined가 내려와도 화면에 NaN이 보이지 않도록 0으로 보정한다.
  return Number(value || 0).toFixed(digits);
}

function formatKda(match) {
  // 최근 경기 row는 kills/deaths/assists를 각각 들고 있으므로 화면용 K/D/A 문자열로 합친다.
  return `${match.kills}/${match.deaths}/${match.assists}`;
}

function formatDate(value) {
  if (!value) return "";
  // 백엔드 DateTimeField가 ISO 문자열로 내려오면 브라우저에서 Date로 변환해 한국어 날짜 형식으로 표시한다.
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

      <!-- submit.prevent는 브라우저 새로고침을 막고 searchAccount 함수로 API 요청 흐름을 넘긴다. -->
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

      <!-- errorMessage가 있을 때만 오류 영역을 렌더링해 정상 상태의 화면 공간을 깔끔하게 유지한다. -->
      <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>
    </section>

    <!-- hasResult는 검색 API 응답이 들어온 뒤에만 분석 결과 패널을 보여주기 위한 computed 상태다. -->
    <section v-if="hasResult" class="results-grid">
      <article class="panel summary-panel">
        <div class="panel-header">
          <div>
            <p class="eyebrow">Summary</p>
            <h2>{{ result.game_name }}#{{ result.tag_line }}</h2>
          </div>
          <span class="region-pill">{{ result.region }}</span>
        </div>

        <!-- summary computed가 result.summary를 가리키므로 API 응답이 바뀌면 이 지표들이 함께 갱신된다. -->
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

        <!-- feedback 배열은 백엔드 룰 기반 분석 결과이며, metric/category 조합으로 카드 key를 안정화한다. -->
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

        <!-- champions computed는 챔피언별 집계 결과를 테이블 행으로 렌더링한다. -->
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

        <!-- matches는 검색 성공 후 별도 API로 불러오며, win/loss class로 결과 색상을 분기한다. -->
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
