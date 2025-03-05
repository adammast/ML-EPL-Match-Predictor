<template>
    <div class="team flex-between">
        <p class="team-label">{{ label }}</p>
        <div class="team-info" v-if="selectedTeam">
        <img :src="selectedTeam.logo_url" class="team-logo" />
        <p class="team-name">{{ selectedTeam.team_name }}</p>
        <p class="team-record">Record: {{ selectedTeam.wins }}W - {{ selectedTeam.draws }}D - {{ selectedTeam.losses }}L</p>
        <p class="goal-diff">Goal Difference: {{ selectedTeam.goal_differential }}</p>
        </div>
        <select @change="$emit('update:team', $event.target.value)">
        <option value="" disabled selected>{{ placeholder }}</option>
        <option v-for="team in teams" :key="team.team_name" :value="team.team_name">
            {{ team.team_name }}
        </option>
        </select>
    </div>
</template>
  
<script>
  export default {
    props: {
      label: String,
      teams: Array,
      selectedTeam: Object,
      placeholder: String,
    },
  };
</script>
  
<style scoped>
.team {
flex-direction: column;
width: 48%;
height: 300px; /* Fixed height to prevent layout shifting */
}

.team-label {
font-size: 1.125rem;
font-weight: bold;
margin-bottom: 0.5rem;
color: var(--primary-color);
}

.team-info {
text-align: center;
}

.team-logo {
width: 5rem;
height: 5rem;
}

.team-name {
    font-size: 1.25rem;
}
</style>
  