<template>
    <button @click="predictMatch" class="button button-primary">Predict Match Outcome</button>
</template>
  
<script>
  export default {
    props: {
      homeTeam: String,
      awayTeam: String,
    },
    emits: ["predict"],
    methods: {
      predictMatch() {
        if (!this.homeTeam || !this.awayTeam) {
          this.$emit("predict", "Please select valid teams.");
          return;
        }
        if (this.homeTeam === this.awayTeam) {
          this.$emit("predict", "Home and Away teams cannot be the same!");
          return;
        }
        this.$emit("predict", null);
      },
    },
  };
</script>