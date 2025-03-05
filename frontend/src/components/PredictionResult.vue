<template>
    <div v-if="prediction" class="prediction">
      <h3 class="prediction-title">Prediction</h3>
      <div class="prediction-details flex-center">
        <div class="prediction-item flex-center" v-for="item in orderedPredictions" :key="item.key">
            <span class="label">{{ item.label }}</span>
            <div class="bar">
                <div class="bar-fill" :class="item.key" :style="{ width: item.value + '%' }"></div>
            </div>
            <span class="percentage">{{ item.value }}%</span>
        </div>
      </div>
    </div>
</template>
  
<script>
export default {
  props: {
    prediction: Object,
  },
  computed: {
    orderedPredictions() {
      if (!this.prediction) return [];
      return [
        { key: "home_win", label: "Home Win", value: this.prediction.home_win },
        { key: "draw", label: "Draw", value: this.prediction.draw },
        { key: "away_win", label: "Away Win", value: this.prediction.away_win }
      ];
    }
  }
};
</script>
  
<style scoped>
.prediction {
    margin-top: 1.5rem;
    text-align: center;
}

.prediction-details {
    flex-direction: column;
    gap: 1rem;
    width: 100%;
}

.prediction-item {
    width: 70%;
}

.label {
    width: 20%;
    text-align: left;
    margin-right: .75rem;
}

.percentage {
    width: 20%;
    margin-left: 0.5rem;
}
</style>