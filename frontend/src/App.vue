<template>
  <div class="container">
    <div class="card">
      <h2 class="title">English Premier League Match Predictor</h2>
      <div class="team-selection flex-between">
        <TeamSelect label="Home Team" :teams="teams" :selectedTeam="selectedHomeTeam" placeholder="Select Home Team" @update:team="homeTeam = $event"/>
        <div class="vs-text title">Vs.</div>
        <TeamSelect label="Away Team" :teams="teams" :selectedTeam="selectedAwayTeam" placeholder="Select Away Team" @update:team="awayTeam = $event"/>
      </div>
      <MatchPredictor :homeTeam="homeTeam" :awayTeam="awayTeam" @predict="handlePrediction" />
      <ErrorMessage :message="errorMessage" />
      <PredictionResult :prediction="prediction" />
    </div>
  </div>
</template>

<script>
import TeamSelect from "./components/TeamSelect.vue";
import MatchPredictor from "./components/MatchPredictor.vue";
import PredictionResult from "./components/PredictionResult.vue";
import ErrorMessage from "./components/ErrorMessage.vue";

export default {
  components: { TeamSelect, MatchPredictor, PredictionResult, ErrorMessage },
  data() {
    return { teams: [], homeTeam: "", awayTeam: "", prediction: null, errorMessage: null };
  },
  computed: {
    selectedHomeTeam() {
      return this.teams.find(team => team.team_name === this.homeTeam);
    },
    selectedAwayTeam() {
      return this.teams.find(team => team.team_name === this.awayTeam);
    }
  },
  mounted() {
    this.fetchTeams();
  },
  methods: {
    async fetchTeams() {
      const response = await fetch("http://127.0.0.1:5000/teams");
      this.teams = (await response.json()).teams;
    },
    async handlePrediction(error) {
      if (error) {
        this.errorMessage = error;
        return;
      }
      this.errorMessage = null;
      const response = await fetch("http://127.0.0.1:5000/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ home_team: this.homeTeam, away_team: this.awayTeam }),
      });
      this.prediction = await response.json();
    },
  },
};
</script>


<style scoped>
.team-selection {
  align-items: flex-start;
  margin-bottom: 2rem;
  width: 100%;
}

.vs-text {
  align-self: center;
  color: var(--primary-color);
}
</style>